from typing import Annotated

from fastapi import APIRouter, Depends, status

from third_party_login import resolve_github_token
from responses import (
    UserCreateResponse,
)

router = APIRouter()

@router.get(path="/home", responses={status.HTTP_403_FORBIDDEN: {"description": "Token not valid"}})
def homepage(user: Annotated[UserCreateResponse, Depends(resolve_github_token)]):
    return {"message": f"Welcome to the homepage, {user.username}!"}
