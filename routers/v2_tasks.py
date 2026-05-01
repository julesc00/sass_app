
from fastapi import (
    APIRouter,
)

from models import (
    TaskWithIdV2
)
from operations import (
    read_all_tasks_v2
)

router = APIRouter(prefix="/v2/tasks", tags=["Tasks V2"])


@router.get("/", response_model=list[TaskWithIdV2])
def get_all_tasks_v2():
    tasks = read_all_tasks_v2()
    return tasks