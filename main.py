from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI

from database import Base
from db_connection import get_engine
from routers import home, users, rbac, premium_access, github_login


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    We use the lifespan parameter of the FastAPI object to instruct the server to sync our database class,
    User, with the database when it starts up.
    """
    Base.metadata.create_all(bind=get_engine())
    yield

app = FastAPI(title="SaaS application", lifespan=lifespan)

app.include_router(github_login.router)
app.include_router(users.router)
app.include_router(home.router)
app.include_router(premium_access.router)


app.include_router(rbac.router)
