from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db_connection import get_session
from operations import add_user
from responses import ResponseCreateUser, UserCreateResponse, UserCreateBody
from security import authenticate_user, create_access_token, decode_access_token

router = APIRouter(prefix="/users", tags=["users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseCreateUser,
    responses={status.HTTP_409_CONFLICT: {"description": "The user already exists."}})
def register_user(
        user: UserCreateBody,
        session: Annotated[Session, Depends(get_session)],):
    user = add_user(session=session, **user.model_dump())

    if not user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User or email already exists")
    user_response = UserCreateResponse(username=user.username, email=user.email)

    return {
        "user": user_response,
        "message": "User created successfully"
    }


@router.post(
    path="/token",
    response_model=Token,
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "The token is invalid"}})
def get_user_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Annotated[Session, Depends(get_session)]):
    user = authenticate_user(
        session=session,
        username_or_email=form_data.username,
        password=form_data.password
    )

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get(path="/me", responses={
    status.HTTP_401_UNAUTHORIZED: {"description": "The user does not exist"},
    status.HTTP_200_OK: {"description": "The user exists"},})
def read_user_me(token: Annotated[str, Depends(oauth2_scheme)], session: Annotated[Session, Depends(get_session)]):
    user = decode_access_token(token=token, db_session=session)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized")

    return {"description": f"{user.username} authorized"}
