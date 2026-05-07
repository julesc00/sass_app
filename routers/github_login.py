
import httpx
from decouple import config
from fastapi import APIRouter, HTTPException, status

from routers.users import Token


GITHUB_CLIENT_ID = config("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = config("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = config("GITHUB_REDIRECT_URI")
GITHUB_AUTHORIZATION_URL = config("GITHUB_AUTHORIZATION_URL")

router = APIRouter()


@router.get("/auth/url")
def github_login():
    return {"auth_url": f"{GITHUB_AUTHORIZATION_URL}?client_id={GITHUB_CLIENT_ID}"}


@router.get(
    path="/github/auth/token",
    response_model=Token,
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "User not registered"}})
async def github_callback(code: str):
    token_response = httpx.post(
        url="https://github.com/login/oauth/access_token",
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_REDIRECT_URI,
        },
        headers={"Accept": "application/json"},
    ).json()

    access_token = token_response.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not registered")
    token_type = token_response.get("token_type", "Bearer")

    return {"access_token": access_token, "token_type": token_type}
