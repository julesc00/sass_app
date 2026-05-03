from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from db_connection import get_session
from models import Role
from operations import add_user
from responses import (
    ResponseCreateUser,
    UserCreateBody,
    UserCreateResponse
)


router = APIRouter()


@router.post(path="/register/premium-user",
             status_code=status.HTTP_201_CREATED,
             response_model=ResponseCreateUser,
             responses={
                 status.HTTP_401_UNAUTHORIZED: {"description": "User not found"},
                 status.HTTP_201_CREATED: {"description": "User created"},
             })
def register_premium_user(user: UserCreateBody, session: Annotated[Session, Depends(get_session)]):
    user = add_user(session=session, **user.model_dump(), role=Role.premium)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User or email already exists")
    user_response = UserCreateResponse(username=user.username, email=user.email)

    return {
        "user": user_response,
        "message": "Premium user created successfully"
    }




