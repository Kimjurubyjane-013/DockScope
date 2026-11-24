from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_user(self, email: str, hashed_password: str) -> User:
        user = User(
            email=email.lower().strip(),
            hashed_password=hashed_password,
            is_active=True,
        )
        return await self.create(user)
