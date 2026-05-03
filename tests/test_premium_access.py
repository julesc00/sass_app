import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from db_connection import get_session
from main import app
from models import Role
from operations import add_user

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

VALID_USER = {
    "username": "premiumjohn",
    "email": "premiumjohn@example.com",
    "password": "secret123",
}


# ---------------------------------------------------------------------------
# POST /register/premium-user — endpoint tests
# ---------------------------------------------------------------------------

class TestRegisterPremiumUser:
    def test_returns_201(self, client):
        response = client.post("/register/premium-user", json=VALID_USER)
        assert response.status_code == 201

    def test_response_has_message(self, client):
        response = client.post("/register/premium-user", json=VALID_USER)
        assert "message" in response.json()

    def test_response_has_user(self, client):
        response = client.post("/register/premium-user", json=VALID_USER)
        data = response.json()
        assert "user" in data
        assert data["user"]["username"] == VALID_USER["username"]
        assert data["user"]["email"] == VALID_USER["email"]

    def test_user_is_stored_with_premium_role(self, client, test_session):
        client.post("/register/premium-user", json=VALID_USER)
        from operations import get_user
        user = get_user(session=test_session, username_or_email=VALID_USER["username"])
        assert user is not None
        assert user.role == Role.premium

    def test_duplicate_username_returns_401(self, client):
        client.post("/register/premium-user", json=VALID_USER)
        duplicate = {**VALID_USER, "email": "other@example.com"}
        response = client.post("/register/premium-user", json=duplicate)
        assert response.status_code == 401

    def test_duplicate_email_returns_401(self, client):
        client.post("/register/premium-user", json=VALID_USER)
        duplicate = {**VALID_USER, "username": "other_user"}
        response = client.post("/register/premium-user", json=duplicate)
        assert response.status_code == 401

    def test_missing_field_returns_422(self, client):
        response = client.post("/register/premium-user", json={"username": "onlyname"})
        assert response.status_code == 422

    def test_invalid_email_returns_422(self, client):
        response = client.post("/register/premium-user", json={**VALID_USER, "email": "not-an-email"})
        assert response.status_code == 422

    def test_response_does_not_expose_password(self, client):
        response = client.post("/register/premium-user", json=VALID_USER)
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data.get("user", {})

    def test_different_from_basic_registration(self, client, test_session):
        """Premium registration should store Role.premium, not Role.basic."""
        from operations import get_user
        client.post("/register/premium-user", json=VALID_USER)
        user = get_user(session=test_session, username_or_email=VALID_USER["username"])
        assert user.role != Role.basic

