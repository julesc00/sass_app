from pydantic import EmailStr, field_validator, BaseModel
from sqlalchemy import Column, Integer
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from database import Base


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]


class Task(BaseModel):
    title: Mapped[str]
    description: Mapped[str]
    status: Mapped[str]


class TaskWithId(Task):
    id: Mapped[int] = mapped_column(primary_key=True)
