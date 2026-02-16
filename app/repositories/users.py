import uuid
from typing import List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User


async def get_user_by_name(db: AsyncSession, name: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.name == name))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, name: str) -> User:
    user = User(id=uuid.uuid4(), name=name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_users_ordered_by_record(db: AsyncSession) -> List[User]:
    result = await db.execute(select(User).order_by(desc(User.record)))
    return result.scalars().all()


async def update_record_if_higher(
    db: AsyncSession,
    user: User,
    new_record: float,
) -> Tuple[float, float]:
    old_record = user.record
    if new_record > old_record:
        user.record = new_record
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return old_record, user.record

