import csv
from typing import Optional

from models import Task, TaskWithId, TaskWithIdV2


DATABASE_FILENAME = "tasks.csv"

column_fields = ["id", "title", "description", "status"]

def read_all_tasks() -> list[TaskWithId]:
    with open(DATABASE_FILENAME, encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        return [TaskWithId(**{**row, "id": int(row["id"])}) for row in reader]


def read_all_tasks_v2() -> list[TaskWithIdV2]:
    with open(DATABASE_FILENAME, mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        return [TaskWithIdV2(**row) for row in reader]


def read_task(task_id: int) -> Optional[TaskWithId]:
    with open(DATABASE_FILENAME, encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if int(row["id"]) == task_id:
                return TaskWithId(**{**row, "id": int(row["id"])})
        return None


def get_next_id():
    try:
        with open(DATABASE_FILENAME, mode="r") as csvfile:
            reader = csv.DictReader(csvfile)
            max_id = max([int(row["id"]) for row in reader])
            return max_id + 1
    except (FileNotFoundError, ValueError):
        return 1


def write_task_into_csv(task: TaskWithId) -> None:
    with open(DATABASE_FILENAME, mode="a") as file:
        writer = csv.DictWriter(file, fieldnames=column_fields)
        writer.writerow(task.model_dump())


def create_task(task: TaskWithId) -> TaskWithId:
    task_id = get_next_id()
    task_w_id = TaskWithId(id=task_id, **task.model_dump())
    write_task_into_csv(task=task_w_id)

    return task_w_id


def modify_task(task_id: int, task: dict) -> Optional[TaskWithId]:
    updated_task: Optional[TaskWithId] = None
    tasks = read_all_tasks()
    for idx, task_ in enumerate(tasks):
        if task_.id == task_id:
            updated_task = task_.model_copy(update=task)
            tasks[idx] = updated_task

    with open(DATABASE_FILENAME, mode="w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_fields)
        writer.writeheader()
        for t in tasks:
            writer.writerow(t.model_dump())

    return updated_task


def remove_task(task_id: int) -> Optional[Task]:
    deleted_task: Optional[TaskWithId] = None
    tasks = read_all_tasks()
    with open(DATABASE_FILENAME, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=column_fields)
        writer.writeheader()

        for t in tasks:
            if t.id == task_id:
                deleted_task = t
                continue
            writer.writerow(t.model_dump())
    if deleted_task:
        dict_task_without_id = deleted_task.model_dump()
        del dict_task_without_id["id"]
        return Task(**dict_task_without_id)
    return None
