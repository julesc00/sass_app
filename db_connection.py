from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URI = "sqlite:///db.sqlite3"


@lru_cache
def get_engine():
    return create_engine(SQLALCHEMY_DATABASE_URI)


def get_session():
    session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=get_engine()
    )
    session = session_local()
    try:
        yield session
    finally:
        session.close()
