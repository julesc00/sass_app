from typing import Optional

from pydantic import BaseModel

from fastapi import (
    APIRouter,
    HTTPException,
    status
)

from enums import ResMsg
from models import (
    Task,
    TaskWithId,
)
from operations import (
    read_all_tasks,
    read_task,
    create_task,
    modify_task,
    remove_task,
)


router = APIRouter(prefix="/tasks", tags=["Tasks"])


class UpdateTask(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


@router.get("/", response_model=list[TaskWithId])
def get_tasks(
        status: Optional[str] = None,
        title: Optional[str] = None,
):
    tasks = read_all_tasks()
    if status:
        tasks = [task for task in tasks if task.status == status]
    if title:
        tasks = [task for task in tasks if task.title == title]

    return tasks


@router.get("/search", response_model=list[TaskWithId])
def search_tasks(keyword: str):
    tasks = read_all_tasks()
    filtered_tasks  = [task for task in tasks if keyword.lower() in (task.title + task.description).lower()]

    return filtered_tasks


@router.get("/{task_id}", response_model=TaskWithId)
def get_task(task_id: int):
    task = read_task(task_id=task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ResMsg.task_not_found)
    return task


@router.post("/", response_model=TaskWithId)
def add_task(task: Task):
    return create_task(task=task)


@router.put("/{task_id}", response_model=TaskWithId)
def update_task(task_id: int, task_update: UpdateTask):
    modified = modify_task(task_id=task_id, task=task_update.model_dump(exclude_none=True))
    if not modified:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ResMsg.task_not_found)
    return modified


@router.delete("/{task_id}", response_model=Task)
def delete_task(task_id: int):
    deleted = remove_task(task_id=task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ResMsg.task_not_found)
    return deleted

