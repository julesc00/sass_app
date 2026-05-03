import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from db_connection import get_session
from main import app
from models import Role
from operations import add_user
from security import create_access_token
from routers.rbac import get_current_user, get_premium_user, UserCreateRequestWithRole

# ---------------------------------------------------------------------------
# In-memory test database
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_session(test_engine):
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(test_session):
    def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_basic_user(session, username="basicuser", email="basic@example.com", password="pass123"):
    return add_user(session=session, username=username, email=email, password=password)


def make_premium_user(session, username="premiumuser", email="premium@example.com", password="pass123"):
    user = make_basic_user(session, username=username, email=email, password=password)
    if user:
        user.role = Role.premium
        session.commit()
        session.refresh(user)
    return user


def token_for(username: str) -> str:
    return create_access_token(data={"sub": username})


# ---------------------------------------------------------------------------
# get_current_user — unit tests
# ---------------------------------------------------------------------------

class TestGetCurrentUser:
    def test_returns_user_create_request_with_role(self, test_session):
        user = make_basic_user(test_session)
        result = get_current_user(token=token_for(user.username), session=test_session)
        assert isinstance(result, UserCreateRequestWithRole)

    def test_returns_correct_username(self, test_session):
        user = make_basic_user(test_session)
        result = get_current_user(token=token_for(user.username), session=test_session)
        assert result.username == user.username

    def test_returns_correct_email(self, test_session):
        user = make_basic_user(test_session)
        result = get_current_user(token=token_for(user.username), session=test_session)
        assert result.email == user.email

    def test_returns_correct_role(self, test_session):
        user = make_basic_user(test_session)
        result = get_current_user(token=token_for(user.username), session=test_session)
        assert result.role == Role.basic

    def test_invalid_token_raises_401(self, test_session):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="invalid.token.here", session=test_session)
        assert exc_info.value.status_code == 401

    def test_nonexistent_user_raises_401(self, test_session):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token_for("ghost_user"), session=test_session)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# get_premium_user — unit tests
# ---------------------------------------------------------------------------

class TestGetPremiumUser:
    def test_premium_user_passes(self):
        current = UserCreateRequestWithRole(
            username="premiumuser", email="premium@example.com", role=Role.premium
        )
        result = get_premium_user(current_user=current)
        assert result.username == "premiumuser"

    def test_basic_user_raises_401(self):
        current = UserCreateRequestWithRole(
            username="basicuser", email="basic@example.com", role=Role.basic
        )
        with pytest.raises(HTTPException) as exc_info:
            get_premium_user(current_user=current)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# GET /welcome/all-users — endpoint tests
# ---------------------------------------------------------------------------

class TestAllUsersEndpoint:
    def test_basic_user_can_access(self, client, test_session):
        user = make_basic_user(test_session)
        response = client.get("/welcome/all-users", headers={"Authorization": f"Bearer {token_for(user.username)}"})
        assert response.status_code == 200

    def test_response_contains_username(self, client, test_session):
        user = make_basic_user(test_session)
        response = client.get("/welcome/all-users", headers={"Authorization": f"Bearer {token_for(user.username)}"})
        assert user.username in response.json()["message"]

    def test_premium_user_can_access(self, client, test_session):
        user = make_premium_user(test_session)
        response = client.get("/welcome/all-users", headers={"Authorization": f"Bearer {token_for(user.username)}"})
        assert response.status_code == 200

    def test_no_token_returns_401(self, client):
        response = client.get("/welcome/all-users")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        response = client.get("/welcome/all-users", headers={"Authorization": "Bearer invalid.token"})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /welcome/premium-user — endpoint tests
# ---------------------------------------------------------------------------

class TestPremiumUserEndpoint:
    def test_premium_user_can_access(self, client, test_session):
        user = make_premium_user(test_session)
        response = client.get("/welcome/premium-user", headers={"Authorization": f"Bearer {token_for(user.username)}"})
        assert response.status_code == 200

    def test_response_contains_username(self, client, test_session):
        user = make_premium_user(test_session)
        response = client.get("/welcome/premium-user", headers={"Authorization": f"Bearer {token_for(user.username)}"})
        assert user.username in response.json()["message"]

    def test_basic_user_cannot_access(self, client, test_session):
        user = make_basic_user(test_session)
        response = client.get("/welcome/premium-user", headers={"Authorization": f"Bearer {token_for(user.username)}"})
        assert response.status_code == 401

    def test_no_token_returns_401(self, client):
        response = client.get("/welcome/premium-user")
        assert response.status_code == 401

