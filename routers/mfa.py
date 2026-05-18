from typing import Annotated

import pyotp
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from db_connection import get_session
from operations import get_user
from rbac import get_current_user
from responses import UserCreateResponse


def generate_totp_secret():
    return pyotp.random_base32()


def generate_totp_uri(secret: str, user_email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=user_email, issuer_name="MyApp")


router = APIRouter()


@router.post("/user/enable-mfa")
def enable_mfa(
        user: Annotated[UserCreateResponse, Depends(get_current_user)],
        db_session: Annotated[Session, Depends(get_session)]
):
    secret = generate_totp_secret()
    db_user = get_user(session=db_session, username_or_email=user.username)
    db_user.totp_secret = secret
    db_session.add(db_user)
    db_session.commit()
    totp_uri = generate_totp_uri(secret=secret, user_email=user.email)

    # Return the TOTP URI for QR code generation in the frontend
    return {
        "totp_uri": totp_uri,
        "secret_number": pyotp.TOTP(secret).now()
    }


@router.post("/verify-totp")
def verify_totp(
        code: str,
        username: str,
        session: Annotated[Session, Depends(get_session)]
):
    user = get_user(session=session, username_or_email=username)
    if not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA not enabled for this user")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP token")

    return {"message": "TOTP token verified successfully"}
