from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from enums import ResMsg
from security import (
    fakely_hash_password,
    fake_token_generator,
    fake_users_db,
    UserInDB
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)

    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ResMsg.invalid_username_or_password,
        )
    user = UserInDB(**user_dict)
    hashed_password = fakely_hash_password(form_data.password)

    if hashed_password != user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ResMsg.invalid_username_or_password
        )
    token = fake_token_generator(user=user)

    return {
        "access_token": token,
        "token_type": "bearer",
    }


