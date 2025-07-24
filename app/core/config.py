import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://api_user:password@localhost/vampire_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecret")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

settings = Settings() 