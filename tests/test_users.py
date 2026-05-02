import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from db_connection import get_session
from main import app
from operations import add_user

# ---------------------------------------------------------------------------
# In-memory test database
# StaticPool ensures all connections share the same in-memory DB instance,
# so tables created by create_all are visible to every session.
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
    """TestClient with get_session overridden to use the in-memory DB."""
    def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_USER = {
    "username": "johndoe",
    "email": "john@example.com",
    "password": "secret123",
}


# ---------------------------------------------------------------------------
# POST /users/register — endpoint tests
# ---------------------------------------------------------------------------

class TestRegisterEndpoint:
    def test_register_returns_201(self, client):
        response = client.post("/users/register", json=VALID_USER)
        assert response.status_code == 201

    def test_register_response_has_message(self, client):
        response = client.post("/users/register", json=VALID_USER)
        assert "message" in response.json()

    def test_register_response_has_user(self, client):
        response = client.post("/users/register", json=VALID_USER)
        data = response.json()
        assert "user" in data
        assert data["user"]["username"] == VALID_USER["username"]
        assert data["user"]["email"] == VALID_USER["email"]

    def test_register_duplicate_username_returns_409(self, client):
        client.post("/users/register", json=VALID_USER)
        duplicate = {**VALID_USER, "email": "other@example.com"}
        response = client.post("/users/register", json=duplicate)
        assert response.status_code == 409

    def test_register_duplicate_email_returns_409(self, client):
        client.post("/users/register", json=VALID_USER)
        duplicate = {**VALID_USER, "username": "other_user"}
        response = client.post("/users/register", json=duplicate)
        assert response.status_code == 409

    def test_register_missing_field_returns_422(self, client):
        response = client.post("/users/register", json={"username": "johndoe"})
        assert response.status_code == 422

    def test_register_invalid_email_returns_422(self, client):
        response = client.post("/users/register", json={**VALID_USER, "email": "not-an-email"})
        assert response.status_code == 422

    def test_response_does_not_expose_password(self, client):
        response = client.post("/users/register", json=VALID_USER)
        data = response.json()
        assert "password" not in data
        assert "password" not in data.get("user", {})
        assert "hashed_password" not in data.get("user", {})


# ---------------------------------------------------------------------------
# add_user — unit tests
# ---------------------------------------------------------------------------

class TestAddUser:
    def test_returns_user_instance(self, test_session):
        from models import User
        user = add_user(session=test_session, **VALID_USER)
        assert isinstance(user, User)

    def test_username_is_stored(self, test_session):
        user = add_user(session=test_session, **VALID_USER)
        assert user.username == VALID_USER["username"]

    def test_email_is_stored(self, test_session):
        user = add_user(session=test_session, **VALID_USER)
        assert user.email == VALID_USER["email"]

    def test_password_is_hashed(self, test_session):
        user = add_user(session=test_session, **VALID_USER)
        assert user.hashed_password != VALID_USER["password"]

    def test_id_is_assigned(self, test_session):
        user = add_user(session=test_session, **VALID_USER)
        assert user.id is not None

    def test_duplicate_username_returns_none(self, test_session):
        add_user(session=test_session, **VALID_USER)
        result = add_user(
            session=test_session,
            username=VALID_USER["username"],
            email="other@example.com",
            password="pass"
        )
        assert result is None

    def test_duplicate_email_returns_none(self, test_session):
        add_user(session=test_session, **VALID_USER)
        result = add_user(
            session=test_session,
            username="other_user",
            email=VALID_USER["email"],
            password="pass"
        )
        assert result is None


