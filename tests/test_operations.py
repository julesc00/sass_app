import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
from models import User
from operations import add_user, pwd_context

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


# ---------------------------------------------------------------------------
# add_user
# ---------------------------------------------------------------------------

class TestAddUser:
    def test_returns_user_instance(self, session):
        user = add_user(session=session, **VALID_USER)
        assert isinstance(user, User)

    def test_username_is_stored(self, session):
        user = add_user(session=session, **VALID_USER)
        assert user.username == VALID_USER["username"]

    def test_email_is_stored(self, session):
        user = add_user(session=session, **VALID_USER)
        assert user.email == VALID_USER["email"]

    def test_password_is_hashed(self, session):
        user = add_user(session=session, **VALID_USER)
        assert user.hashed_password != VALID_USER["password"]

    def test_hashed_password_verifies(self, session):
        user = add_user(session=session, **VALID_USER)
        assert pwd_context.verify(VALID_USER["password"], user.hashed_password)

    def test_id_is_assigned(self, session):
        user = add_user(session=session, **VALID_USER)
        assert user.id is not None
        assert isinstance(user.id, int)

    def test_user_is_persisted_in_db(self, session):
        add_user(session=session, **VALID_USER)
        result = session.query(User).filter_by(username=VALID_USER["username"]).first()
        assert result is not None

    def test_default_role_is_basic(self, session):
        user = add_user(session=session, **VALID_USER)
        assert user.role == "basic"

    def test_totp_secret_is_none_by_default(self, session):
        user = add_user(session=session, **VALID_USER)
        assert user.totp_secret is None

    def test_duplicate_username_returns_none(self, session):
        add_user(session=session, **VALID_USER)
        result = add_user(
            session=session,
            username=VALID_USER["username"],
            email="other@example.com",
            password="pass",
        )
        assert result is None

    def test_duplicate_email_returns_none(self, session):
        add_user(session=session, **VALID_USER)
        result = add_user(
            session=session,
            username="other_user",
            email=VALID_USER["email"],
            password="pass",
        )
        assert result is None

    def test_duplicate_does_not_corrupt_session(self, session):
        """After a failed duplicate insert the session should still be usable."""
        add_user(session=session, **VALID_USER)
        add_user(session=session, username=VALID_USER["username"],
                 email="other@example.com", password="pass")
        # session rolled back — original user still queryable
        result = session.query(User).filter_by(username=VALID_USER["username"]).first()
        assert result is not None

    def test_multiple_users_can_be_added(self, session):
        user1 = add_user(session=session, username="alice", email="alice@example.com", password="pass1")
        user2 = add_user(session=session, username="bob", email="bob@example.com", password="pass2")
        assert user1 is not None
        assert user2 is not None
        assert user1.id != user2.id
