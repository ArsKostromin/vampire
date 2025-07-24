from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.user import User
from passlib.context import CryptContext
import uuid
from app.core import auth
from fastapi import Response
from app.models.user import User as UserModel
from typing import List

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRegisterRequest(BaseModel):
    name: str
    password: str

class UserRegisterResponse(BaseModel):
    id: uuid.UUID
    name: str

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    # Проверка уникальности имени
    result = await db.execute(select(User).where(User.name == request.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="User with this name already exists")
    hashed_password = pwd_context.hash(request.password)
    user = User(id=uuid.uuid4(), name=request.name, password_hash=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserRegisterResponse(id=user.id, name=user.name)

class UserLoginRequest(BaseModel):
    name: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
async def login_user(request: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth.authenticate_user(db, request.name, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = auth.create_access_token({"sub": user.name})
    refresh_token = auth.create_refresh_token({"sub": user.name})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

class UserMeResponse(BaseModel):
    id: uuid.UUID
    name: str
    record: float

@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: UserModel = Depends(auth.get_current_user)):
    return UserMeResponse(id=current_user.id, name=current_user.name, record=current_user.record)

class TokenRefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: TokenRefreshRequest):
    from jose import JWTError, jwt
    from app.core.config import settings
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    from app.core import auth
    access_token = auth.create_access_token({"sub": username})
    refresh_token = auth.create_refresh_token({"sub": username})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

class LeaderboardUser(BaseModel):
    id: uuid.UUID
    name: str
    record: float

@router.get("/leaderboard", response_model=List[LeaderboardUser])
async def get_leaderboard(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import desc
    result = await db.execute(select(User).order_by(desc(User.record)).limit(10))
    users = result.scalars().all()
    return [LeaderboardUser(id=u.id, name=u.name, record=u.record) for u in users]

class UpdateRecordRequest(BaseModel):
    record: float

class UpdateRecordResponse(BaseModel):
    old_record: float
    new_record: float

@router.patch("/record", response_model=UpdateRecordResponse)
async def update_record(request: UpdateRecordRequest, current_user: UserModel = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    old_record = current_user.record
    if request.record > old_record:
        current_user.record = request.record
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
        return UpdateRecordResponse(old_record=old_record, new_record=current_user.record)
    return UpdateRecordResponse(old_record=old_record, new_record=old_record) 