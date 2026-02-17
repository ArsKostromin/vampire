import uuid
from typing import List
from pydantic import BaseModel, Field, validator


# USER REQUESTS
class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=30, strip_whitespace=True)

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty or only spaces")
        return v


class UserLoginRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=30, strip_whitespace=True)

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty or only spaces")
        return v


class UpdateRecordRequest(BaseModel):
    record: float = Field(..., ge=0)  # record >= 0


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)  # минимальная длина токена


#  USER RESPONSES
class UserRegisterResponse(BaseModel):
    id: uuid.UUID
    name: str


class UserMeResponse(BaseModel):
    id: uuid.UUID
    name: str
    record: float


class UpdateRecordResponse(BaseModel):
    old_record: float
    new_record: float


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# LEADERBOARD 
class LeaderboardUser(BaseModel):
    id: uuid.UUID
    name: str
    record: float


class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderboardUser]
    position: int
