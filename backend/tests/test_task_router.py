from unittest.mock import AsyncMock, patch

import pytest

from app.models.task import Task, TaskStatus
from tests.conftest import SAMPLE_ADDRESS


async def create_test_task(db_session, total: int = 2, status: TaskStatus = TaskStatus.done) -> Task:
    task = Task(total=total, status=status, processed=total)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


async def test_nonexistent_task_returns_404(http_client):
    response = await http_client.get("/api/v1/task/nonexistent-task-id")
    assert response.status_code == 404


async def test_existing_task_returns_200(http_client, db_session):
    task = await create_test_task(db_session)
    response = await http_client.get(f"/api/v1/task/{task.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == task.id
    assert body["status"] == "done"
    assert body["total"] == 2


async def test_task_response_has_required_fields(http_client, db_session):
    task = await create_test_task(db_session)
    response = await http_client.get(f"/api/v1/task/{task.id}")
    body = response.json()
    assert "task_id" in body
    assert "status" in body
    assert "total" in body
    assert "processed" in body
    assert "failed" in body
    assert "created_at" in body
    assert "completed_at" in body
    assert "results" in body


async def test_pending_task_has_empty_results(http_client, db_session):
    task = await create_test_task(db_session, status=TaskStatus.pending)
    response = await http_client.get(f"/api/v1/task/{task.id}")
    body = response.json()
    assert body["status"] == "pending"
    assert body["results"] == []


async def test_pagination_params_accepted(http_client, db_session):
    task = await create_test_task(db_session)
    response = await http_client.get(f"/api/v1/task/{task.id}?page=1&page_size=10")
    assert response.status_code == 200


async def test_invalid_pagination_returns_422(http_client, db_session):
    task = await create_test_task(db_session)
    response = await http_client.get(f"/api/v1/task/{task.id}?page=0")
    assert response.status_code == 422
