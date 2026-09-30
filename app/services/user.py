from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.user import UserCreate
from app.db.models import User
from app.services.base_user import BaseUserService


class UserService(BaseUserService):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)


    async def create(self, data: UserCreate) -> User:

        return await self._create_user(
            data.model_dump(),
            "user"
        )

    async def token(self, email, password) -> str:

        return await self._generate_token(email, password)
