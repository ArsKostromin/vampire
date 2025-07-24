import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.db.session import get_db
from app.main import app
from app.models.user import Base as UserBase
from app.models.audit import Base as AuditBase  # если нужна таблица логов

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(DATABASE_URL, echo=False, future=True)
TestSessionLocal = async_sessionmaker(bind=engine_test, expire_on_commit=False)

@pytest.fixture(scope="session")
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(AuditBase.metadata.create_all)

    yield

    async with engine_test.begin() as conn:
        await conn.run_sync(UserBase.metadata.drop_all)
        await conn.run_sync(AuditBase.metadata.drop_all)

@pytest.fixture()
async def db_session(setup_db):
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture()
async def client(db_session: AsyncSession):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
