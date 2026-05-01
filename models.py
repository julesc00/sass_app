from pydantic import BaseModel
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
    title: str
    description: str
    status: str


class TaskV2(BaseModel):
    title: str
    description: str
    status: str
    priority: str | None = None


class TaskWithId(Task):
    id: int


class TaskWithIdV2(TaskV2):
    id: int
