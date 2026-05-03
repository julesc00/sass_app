import pytest
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from operations import add_user
from security import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    SECRET_KEY,
    ALGORITHM,
)

# ---------------------------------------------------------------------------
# In-memory test database
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def session():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_USER = {
    "username": "johndoe",
    "email": "john@example.com",
    "password": "secret123",
}


@pytest.fixture
def existing_user(session):
    return add_user(session=session, **VALID_USER)


# ---------------------------------------------------------------------------
# authenticate_user
# ---------------------------------------------------------------------------

class TestAuthenticateUser:
    def test_valid_username_and_password(self, session, existing_user):
        user = authenticate_user(session, VALID_USER["username"], VALID_USER["password"])
        assert user is not None

    def test_valid_email_and_password(self, session, existing_user):
        user = authenticate_user(session, VALID_USER["email"], VALID_USER["password"])
        assert user is not None

    def test_returns_correct_user(self, session, existing_user):
        user = authenticate_user(session, VALID_USER["username"], VALID_USER["password"])
        assert user.username == VALID_USER["username"]

    def test_wrong_password_returns_none(self, session, existing_user):
        user = authenticate_user(session, VALID_USER["username"], "wrongpassword")
        assert user is None

    def test_nonexistent_username_returns_none(self, session):
        user = authenticate_user(session, "ghost", "anypassword")
        assert user is None

    def test_nonexistent_email_returns_none(self, session):
        user = authenticate_user(session, "ghost@example.com", "anypassword")
        assert user is None


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------

class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token({"sub": "johndoe"})
        assert isinstance(token, str)

    def test_token_contains_sub(self):
        token = create_access_token({"sub": "johndoe"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "johndoe"

    def test_token_contains_exp(self):
        token = create_access_token({"sub": "johndoe"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload

    def test_token_with_extra_data(self):
        token = create_access_token({"sub": "johndoe", "role": "admin"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["role"] == "admin"

    def test_different_subjects_produce_different_tokens(self):
        token1 = create_access_token({"sub": "alice"})
        token2 = create_access_token({"sub": "bob"})
        assert token1 != token2


# ---------------------------------------------------------------------------
# decode_access_token
# ---------------------------------------------------------------------------

class TestDecodeAccessToken:
    def test_valid_token_returns_user(self, session, existing_user):
        token = create_access_token({"sub": VALID_USER["username"]})
        user = decode_access_token(token=token, db_session=session)
        assert user is not None
        assert user.username == VALID_USER["username"]

    def test_invalid_token_returns_none(self, session):
        user = decode_access_token(token="not.a.valid.token", db_session=session)
        assert user is None

    def test_tampered_token_returns_none(self, session):
        token = create_access_token({"sub": VALID_USER["username"]})
        tampered = token[:-5] + "XXXXX"
        user = decode_access_token(token=tampered, db_session=session)
        assert user is None

    def test_token_with_nonexistent_user_returns_none(self, session):
        token = create_access_token({"sub": "ghost_user"})
        user = decode_access_token(token=token, db_session=session)
        assert user is None

    def test_token_without_sub_returns_none(self, session):
        token = create_access_token({"data": "no_sub_field"})
        user = decode_access_token(token=token, db_session=session)
        assert user is None

