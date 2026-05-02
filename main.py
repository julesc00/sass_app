from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI

from database import Base
from db_connection import get_engine
from routers import users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    We use the lifespan parameter of the FastAPI object to instruct the server to sync our database class,
    User, with the database when it starts up.
    """
    Base.metadata.create_all(bind=get_engine())
    yield

app = FastAPI(title="SaaS application", lifespan=lifespan)

app.include_router(users.router)
