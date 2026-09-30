


from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.api_tag import APITag
from app.api.dependencies import UserServiceDep, get_user_access_token
from app.api.schemas.user import UserCreate, UserRead
from app.db.redis import (
    add_jti_to_blacklist,
)

router = APIRouter(prefix="/user", tags=[APITag.USER])

@router.post("/signup", response_model=UserRead)
async def register_user(data: UserCreate, service: UserServiceDep):
    return await service.create(data)


# Login the user
@router.post("/token")
async def login_user(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: UserServiceDep,
):

    token = await service.token(
        request_form.username,
        request_form.password,
    )

    return {
        "access_token": token,
        "type": "jwt",
    }



# Logout the user
@router.get("/logout")
async def logout_user(
    token_data: Annotated[dict, Depends(get_user_access_token)],
):
    await add_jti_to_blacklist(
        jti=token_data["jti"],
        exp=token_data["exp"],
    )

    return {"detail": "Successfully logged out"}