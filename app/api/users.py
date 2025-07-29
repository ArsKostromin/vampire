from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.db.session import get_db, get_async_session
from app.models.user import User
from app.core import auth
from app.models.user import User as UserModel
from app.models.audit import AuditLog
from typing import List
from datetime import datetime
import uuid

router = APIRouter()

# ----------- SCHEMAS -----------

class UserRegisterRequest(BaseModel):
    name: str

class UserRegisterResponse(BaseModel):
    id: uuid.UUID
    name: str

class UserLoginRequest(BaseModel):
    name: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserMeResponse(BaseModel):
    id: uuid.UUID
    name: str
    record: float

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class LeaderboardUser(BaseModel):
    id: uuid.UUID
    name: str
    record: float

class UpdateRecordRequest(BaseModel):
    record: float

class UpdateRecordResponse(BaseModel):
    old_record: float
    new_record: float

class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderboardUser]
    position: int

# ----------- ENDPOINTS -----------

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.name == request.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="User with this name already exists")

    user = User(id=uuid.uuid4(), name=request.name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserRegisterResponse(id=user.id, name=user.name)

@router.post("/login", response_model=TokenResponse)
async def login_user(request: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.name == request.name))
    user = result.scalar_one_or_none()

    # Создаём лог для фейла
    if not user:
        log = AuditLog(
            table_name="users",
            operation="LOGIN_ATTEMPT",
            username=request.name,
            extra="fail: user not found"
        )
        db.add(log)
        await db.commit()
        raise HTTPException(status_code=401, detail="User not found")

    # Создаём лог для успеха
    log = AuditLog(
        table_name="users",
        operation="LOGIN_ATTEMPT",
        user_id=user.id,
        username=user.name,
        extra="success"
    )
    db.add(log)
    await db.commit()

    access_token = auth.create_access_token({"sub": user.name})
    refresh_token = auth.create_refresh_token({"sub": user.name})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: UserModel = Depends(auth.get_current_user)):
    return UserMeResponse(id=current_user.id, name=current_user.name, record=current_user.record)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    from jose import JWTError, jwt
    from app.core.config import settings

    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=["HS256"])

        if payload.get("type") != "refresh":
            log = AuditLog(
                table_name="users",
                operation="TOKEN_REFRESH",
                username=payload.get("sub", "unknown"),
                extra="fail: invalid token type"
            )
            db.add(log)
            await db.commit()
            raise HTTPException(status_code=401, detail="Invalid token type")

        username = payload.get("sub")
        if not username:
            log = AuditLog(
                table_name="users",
                operation="TOKEN_REFRESH",
                extra="fail: token payload missing 'sub'"
            )
            db.add(log)
            await db.commit()
            raise HTTPException(status_code=401, detail="Invalid token payload")

        result = await db.execute(select(User).where(User.name == username))
        user = result.scalar_one_or_none()

        log = AuditLog(
            table_name="users",
            operation="TOKEN_REFRESH",
            user_id=user.id if user else None,
            username=username,
            extra="success"
        )
        db.add(log)
        await db.commit()

        access_token = auth.create_access_token({"sub": username})
        refresh_token = auth.create_refresh_token({"sub": username})
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    except JWTError:
        log = AuditLog(
            table_name="users",
            operation="TOKEN_REFRESH",
            extra="fail: invalid JWT"
        )
        db.add(log)
        await db.commit()
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
):
    result = await db.execute(select(User).order_by(desc(User.record)))
    users = result.scalars().all()
    leaderboard = [LeaderboardUser(id=u.id, name=u.name, record=u.record) for u in users]
    # Найти позицию текущего пользователя (индекс + 1)
    position = next((i + 1 for i, u in enumerate(users) if u.id == current_user.id), None)
    return LeaderboardResponse(leaderboard=leaderboard, position=position)

@router.patch("/record", response_model=UpdateRecordResponse)
async def update_record(
    request: UpdateRecordRequest,
    current_user: UserModel = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    old_record = current_user.record
    if request.record > old_record:
        current_user.record = request.record
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
        return UpdateRecordResponse(old_record=old_record, new_record=current_user.record)
    return UpdateRecordResponse(old_record=old_record, new_record=old_record)
