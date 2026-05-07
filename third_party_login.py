import httpx
import secrets
from typing import Annotated

from decouple import config
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import user

from db_connection import get_session
from models import User
from operations import get_user, add_user


GITHUB_CLIENT_ID = config("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = config("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = config("GITHUB_REDIRECT_URI")
GITHUB_AUTHORIZATION_URL = config("GITHUB_AUTHORIZATION_URL")


def resolve_github_token(
        access_token: Annotated[str, Depends(OAuth2())],
        session: Annotated[Session, Depends(get_session)]) -> User:
    user_response = httpx.get(
        url="https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"}).json()
    if "message" in user_response:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"[ERROR] GitHub API error: {user_response['message']}"
        )
    username = user_response.get("login", "")

    if not username:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="[ERROR] Token not valid")

    user = get_user(session=session, username_or_email=username)

    if not user:
        email = user_response.get("email", "")
        user = get_user(session=session, username_or_email=email)
    # Process user_response to log
    # the user in or create a new account
    if not user:
        # Auto-register on first GitHub login
        user = add_user(
            session=session,
            username=username,
            email=user_response.get("email") or f"{username}@github.local",
            password=secrets.token_hex(32),
        )
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="[ERROR] Token not valid")

    return user

