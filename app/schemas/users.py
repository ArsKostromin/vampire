import uuid
from typing import List

from pydantic import BaseModel


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

