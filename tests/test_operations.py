import csv
import pytest
from unittest.mock import patch

from models import Task, TaskWithId
import operations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COLUMN_FIELDS = ["id", "title", "description", "status"]


def _write_csv(path, rows: list[dict]) -> None:
    """Write a CSV file with the standard task headers."""
    with open(path, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMN_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _sample_rows() -> list[dict]:
    return [
        {"id": "1", "title": "Task One", "description": "Desc One", "status": "Incomplete"},
        {"id": "2", "title": "Task Two", "description": "Desc Two", "status": "Ongoing"},
    ]


# ---------------------------------------------------------------------------
# Fixture: redirect DATABASE_FILENAME to a temp file for every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def csv_file(tmp_path):
    """Create a temp CSV pre-populated with sample data and patch the module."""
    temp_csv = tmp_path / "tasks.csv"
    _write_csv(temp_csv, _sample_rows())

    with patch.object(operations, "DATABASE_FILENAME", str(temp_csv)):
        yield temp_csv


# ---------------------------------------------------------------------------
# read_all_tasks
# ---------------------------------------------------------------------------

class TestReadAllTasks:
    def test_returns_list_of_task_with_id(self):
        tasks = operations.read_all_tasks()
        assert isinstance(tasks, list)
        assert all(isinstance(t, TaskWithId) for t in tasks)

    def test_returns_correct_count(self):
        tasks = operations.read_all_tasks()
        assert len(tasks) == 2

    def test_fields_are_mapped_correctly(self):
        tasks = operations.read_all_tasks()
        assert tasks[0].id == 1
        assert tasks[0].title == "Task One"
        assert tasks[0].description == "Desc One"
        assert tasks[0].status == "Incomplete"

    def test_empty_csv_returns_empty_list(self, tmp_path):
        empty_csv = tmp_path / "empty.csv"
        _write_csv(empty_csv, [])
        with patch.object(operations, "DATABASE_FILENAME", str(empty_csv)):
            assert operations.read_all_tasks() == []


# ---------------------------------------------------------------------------
# read_task
# ---------------------------------------------------------------------------

class TestReadTask:
    def test_returns_correct_task(self):
        task = operations.read_task(1)
        assert task is not None
        assert task.id == 1
        assert task.title == "Task One"

    def test_returns_second_task(self):
        task = operations.read_task(2)
        assert task is not None
        assert task.id == 2

    def test_returns_none_for_missing_id(self):
        task = operations.read_task(999)
        assert task is None

    def test_returns_task_with_id_instance(self):
        task = operations.read_task(1)
        assert isinstance(task, TaskWithId)


# ---------------------------------------------------------------------------
# get_next_id
# ---------------------------------------------------------------------------

class TestGetNextId:
    def test_returns_max_id_plus_one(self):
        next_id = operations.get_next_id()
        assert next_id == 3  # max(1, 2) + 1

    def test_returns_1_when_file_not_found(self, tmp_path):
        missing = tmp_path / "nonexistent.csv"
        with patch.object(operations, "DATABASE_FILENAME", str(missing)):
            assert operations.get_next_id() == 1

    def test_returns_1_when_csv_is_empty(self, tmp_path):
        empty_csv = tmp_path / "empty.csv"
        _write_csv(empty_csv, [])
        with patch.object(operations, "DATABASE_FILENAME", str(empty_csv)):
            assert operations.get_next_id() == 1


# ---------------------------------------------------------------------------
# write_task_into_csv
# ---------------------------------------------------------------------------

class TestWriteTaskIntoCsv:
    def test_appends_new_task(self):
        new_task = TaskWithId(id=3, title="Task Three", description="Desc Three", status="Done")
        operations.write_task_into_csv(new_task)
        tasks = operations.read_all_tasks()
        assert len(tasks) == 3

    def test_appended_task_has_correct_fields(self):
        new_task = TaskWithId(id=3, title="Task Three", description="Desc Three", status="Done")
        operations.write_task_into_csv(new_task)
        tasks = operations.read_all_tasks()
        last = tasks[-1]
        assert last.id == 3
        assert last.title == "Task Three"
        assert last.status == "Done"


# ---------------------------------------------------------------------------
# modify_task
# ---------------------------------------------------------------------------

class TestModifyTask:
    def test_returns_updated_task(self):
        updated = operations.modify_task(1, {"title": "Updated Title"})
        assert updated is not None
        assert updated.title == "Updated Title"

    def test_updated_task_is_task_with_id_instance(self):
        updated = operations.modify_task(1, {"status": "Done"})
        assert isinstance(updated, TaskWithId)

    def test_update_persists_to_csv(self):
        operations.modify_task(1, {"status": "Done"})
        task = operations.read_task(1)
        assert task is not None
        assert task.status == "Done"

    def test_other_tasks_unchanged(self):
        operations.modify_task(1, {"title": "Changed"})
        task2 = operations.read_task(2)
        assert task2 is not None
        assert task2.title == "Task Two"

    def test_returns_none_for_missing_id(self):
        result = operations.modify_task(999, {"title": "Ghost"})
        assert result is None


# ---------------------------------------------------------------------------
# remove_task
# ---------------------------------------------------------------------------

class TestRemoveTask:
    def test_returns_task_on_success(self):
        result = operations.remove_task(1)
        assert result is not None
        assert isinstance(result, Task)

    def test_returned_task_has_correct_fields(self):
        result = operations.remove_task(1)
        assert result is not None
        assert result.title == "Task One"
        assert result.description == "Desc One"
        assert result.status == "Incomplete"

    def test_task_is_removed_from_csv(self):
        operations.remove_task(1)
        assert operations.read_task(1) is None

    def test_remaining_tasks_are_preserved(self):
        operations.remove_task(1)
        tasks = operations.read_all_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == 2

    def test_returns_none_for_missing_id(self):
        result = operations.remove_task(999)
        assert result is None

    def test_csv_unchanged_when_id_not_found(self):
        operations.remove_task(999)
        assert len(operations.read_all_tasks()) == 2

