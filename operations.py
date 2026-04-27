import csv
from typing import Optional

from models import Task, TaskWithId


DATABASE_FILENAME = "tasks.csv"

column_fields = ["id", "title", "description", "status"]

def read_all_tasks() -> list[TaskWithId]:
    with open(DATABASE_FILENAME) as csvfile:
        reader = csv.DictReader(csvfile)
        return [TaskWithId(**row) for row in reader]


def read_task(task_id: int) -> Optional[TaskWithId]:
    with open(DATABASE_FILENAME) as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if int(row["id"]) == task_id:
                return TaskWithId(**row)
