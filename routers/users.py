from typing import Annotated
from fastapi import APIRouter, Depends

from security import get_user_from_token, User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=User)
def read_users_me(
        current_user: Annotated[User, Depends(get_user_from_token)],
):
    return current_user