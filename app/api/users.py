from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import auth
from app.db.session import get_db
from app.models.user import User as UserModel
from app.schemas.users import (
    LeaderboardResponse,
    TokenRefreshRequest,
    TokenResponse,
    UpdateRecordRequest,
    UpdateRecordResponse,
    UserLoginRequest,
    UserMeResponse,
    UserRegisterRequest,
    UserRegisterResponse,
)
from app.services.users import (
    get_leaderboard_service,
    get_me_service,
    login_user_service,
    refresh_token_service,
    register_user_service,
    update_record_service,
)
from app.utils.logger_decorator import log_all, log_elastic_only

router = APIRouter()

@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
@log_all
async def register_user(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user_response = await register_user_service(request, db)
    if user_response is None:
        raise HTTPException(
            status_code=400,
            detail="User with this name already exists",
        )
    return user_response


@router.post("/login", response_model=TokenResponse)
@log_elastic_only
async def login_user(request: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    token_response = await login_user_service(request, db)
    if token_response is None:
        raise HTTPException(status_code=401, detail="User not found")
    return token_response


@router.get("/me", response_model=UserMeResponse)
@log_elastic_only
async def get_me(current_user: UserModel = Depends(auth.get_current_user)):
    return await get_me_service(current_user)


@router.post("/refresh", response_model=TokenResponse)
@log_elastic_only
async def refresh_token(request: TokenRefreshRequest):
    token_response = await refresh_token_service(request)
    if token_response is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )
    return token_response



@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(auth.get_current_user),
):
    return await get_leaderboard_service(db, current_user)


@router.patch("/record", response_model=UpdateRecordResponse)
@log_all
async def update_record(
    request: UpdateRecordRequest,
    current_user: UserModel = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_record_service(request, current_user, db)
