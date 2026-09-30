


from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserRead(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    email_verified: bool
    is_active: bool


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str