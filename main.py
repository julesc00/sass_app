from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from database import Base, engine, db_connection
from models import User


Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/users/")
async def read_users(db: db_connection):
    users = db.query(User).all()
    return users


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
