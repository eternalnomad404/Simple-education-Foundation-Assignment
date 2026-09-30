

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.models import UserBase
from app.utils import generate_access_token

from .base import BaseService

password_context = CryptContext(schemes=["bcrypt"])


class BaseUserService(BaseService):
    def __init__(self, model: UserBase, session: AsyncSession):
        self.session = session
        self.model = model

    async def _get_by_email(self, email) -> UserBase:
        return await self.session.scalar(
            select(self.model).where(self.model.email ==email)
        )

    async def _create_user(self, data: dict, router_prefix: str):
        user = self.model(
            **data,
            password_hash = password_context.hash(data["password"])
        )

        user = await self._create(user)

        # can create a user email verification token creation and verification flow later here

        return user

    async def _generate_token(self, email, password) -> str:
        # validate credentials
        user = await self._get_by_email(email)


        # Reject if user doesn't exist or password doesn't match the stored hash
        if user is None or not password_context.verify(
            password,
            user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bad credentials"
            )

        # Future - Block login until the user has verified their email

        # Generate the access token with basic user info
        token = generate_access_token(
            data={
                "user": {
                    "name" : user.name,
                    "id" : str(user.id),
                }
            }
        )

        return token