from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import auth
from app.models.user import User as UserModel
from app.repositories.users import (
    create_user,
    get_user_by_name,
    get_users_ordered_by_record,
    update_record_if_higher,
)
from app.schemas.users import (
    LeaderboardResponse,
    LeaderboardUser,
    TokenRefreshRequest,
    TokenResponse,
    UpdateRecordRequest,
    UpdateRecordResponse,
    UserLoginRequest,
    UserMeResponse,
    UserRegisterRequest,
    UserRegisterResponse,
)


async def register_user_service(
    request: UserRegisterRequest,
    db: AsyncSession,
) -> Optional[UserRegisterResponse]:
    existing = await get_user_by_name(db, request.name)
    if existing:
        return None

    user = await create_user(db, request.name)
    return UserRegisterResponse(id=user.id, name=user.name)


async def login_user_service(
    request: UserLoginRequest,
    db: AsyncSession,
) -> Optional[TokenResponse]:
    user = await get_user_by_name(db, request.name)
    if not user:
        return None

    access_token = auth.create_access_token({"sub": user.name})
    refresh_token = auth.create_refresh_token({"sub": user.name})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def get_me_service(current_user: UserModel) -> UserMeResponse:
    return UserMeResponse(
        id=current_user.id,
        name=current_user.name,
        record=current_user.record,
    )


async def refresh_token_service(
    request: TokenRefreshRequest,
) -> Optional[TokenResponse]:
    username = auth.verify_refresh_token(request.refresh_token)
    if not username:
        return None

    access_token = auth.create_access_token({"sub": username})
    refresh_token = auth.create_refresh_token({"sub": username})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def get_leaderboard_service(
    db: AsyncSession,
    current_user: UserModel,
) -> LeaderboardResponse:
    users = await get_users_ordered_by_record(db)
    leaderboard = [
        LeaderboardUser(
            id=u.id,
            name=u.name,
            record=u.record,
        )
        for u in users
    ]
    position = next(
        (i + 1 for i, u in enumerate(users) if u.id == current_user.id),
        None,
    )
    return LeaderboardResponse(leaderboard=leaderboard, position=position)


async def update_record_service(
    request: UpdateRecordRequest,
    current_user: UserModel,
    db: AsyncSession,
) -> UpdateRecordResponse:
    old_record, new_record = await update_record_if_higher(
        db,
        current_user,
        request.record,
    )
    return UpdateRecordResponse(old_record=old_record, new_record=new_record)

