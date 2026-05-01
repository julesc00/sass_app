from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from fastapi import Depends, HTTPException, status

from enums import ResMsg

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "hashed_password": "hashed_secret"
    },
    "janedoe": {
        "username": "janedoe",
        "hashed_password": "hashed_secret2"
    }
}


def fakely_hash_password(password: str) -> str:
    return f"hashed_{password}"


class User(BaseModel):
    username: str


class UserInDB(User):
    hashed_password: str


def get_user(db: dict, username: str) -> UserInDB | None:
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def fake_token_generator(user: UserInDB) -> str | None:
    # This doesn't provide any security at all
    return f"tokenized_{user.username}"


def fake_token_resolver(token: str) -> UserInDB | None:
    # This doesn't provide any security at all
    if token.startswith("tokenized_"):
        user_id = token.removeprefix("tokenized_")
        user = get_user(db=fake_users_db, username=user_id)
        return user
    return None


def get_user_from_token(token: str = Depends(oauth2_scheme)) -> UserInDB | None:
    user = fake_token_resolver(token=token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ResMsg.invalid_auth_credentials,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
