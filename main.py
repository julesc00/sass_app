from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Base, engine, db_connection
from models import User

# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI()

class UserBody(BaseModel):
    name: str
    email: str


@app.get("/users/")
def read_users(db: db_connection):
    users = db.query(User).all()
    return users


@app.get("/user")
def get_user(user_id: int, db: db_connection):
    user = (
        db.query(User).filter(
            User.id == user_id
        ).first()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="[ERROR] User not found")
    return user


@app.post("/user")
def add_user(
    user: UserBody,
    db: db_connection
):
    new_user = User(
        name=user.name,
        email=user.email
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        db.close()


@app.post("/user/{user_id}")
def update_user(
        user_id: int,
        user: UserBody,
        db: db_connection
):
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="[ERROR] User not found"
        )
    db_user.name = user.name
    db_user.email = user.email
    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/user/{user_id}")
def delete_user(user_id: int, db: db_connection):
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="[ERROR] User not found"
        )
    db.delete(db_user)
    db.commit()
    return {"detail": "[INFO] User deleted successfully"}
