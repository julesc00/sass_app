from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from db_connection import get_session
from models import User
from operations import get_user, pwd_context


SECRET_KEY = "a_very_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def authenticate_user(session: Session, username_or_email: str, password: str) -> User | None:
    try:
        user = get_user(session=session, username_or_email=username_or_email)
        if not user or not pwd_context.verify(password, user.hashed_password):
            return None
        return user
    except SQLAlchemyError:
        return None


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str, db_session: Session) -> User | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
    except JWTError:
        return None

    if not username:
        return None
    user = get_user(session=db_session, username_or_email=username)
    return user
