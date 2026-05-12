from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import SAMPLE_ADDRESS

SECOND_ADDRESS = "xHAFLJoX5FRYuqF9eQXsbweouQejTcKtHoVvxNc17XW"


async def test_valid_request_returns_202(http_client):
    with patch("app.routers.check.task_service.process_task", new_callable=AsyncMock):
        response = await http_client.post("/api/v1/check", json={
            "addresses": [SAMPLE_ADDRESS, SECOND_ADDRESS],
        })
    assert response.status_code == 202
    body = response.json()
    assert "task_id" in body
    assert body["status"] == "pending"
    assert body["total"] == 2


async def test_response_has_required_fields(http_client):
    with patch("app.routers.check.task_service.process_task", new_callable=AsyncMock):
        response = await http_client.post("/api/v1/check", json={
            "addresses": [SAMPLE_ADDRESS],
        })
    body = response.json()
    assert "task_id" in body
    assert "status" in body
    assert "total" in body
    assert "created_at" in body


async def test_empty_addresses_returns_422(http_client):
    response = await http_client.post("/api/v1/check", json={"addresses": []})
    assert response.status_code == 422


async def test_too_many_addresses_returns_422(http_client):
    addresses = [SAMPLE_ADDRESS] * 1001
    with patch("app.routers.check.task_service.process_task", new_callable=AsyncMock):
        response = await http_client.post("/api/v1/check", json={"addresses": addresses})
    assert response.status_code == 422


async def test_missing_addresses_field_returns_422(http_client):
    response = await http_client.post("/api/v1/check", json={})
    assert response.status_code == 422


async def test_default_options_applied(http_client):
    with patch("app.routers.check.task_service.process_task", new_callable=AsyncMock):
        response = await http_client.post("/api/v1/check", json={
            "addresses": [SAMPLE_ADDRESS],
        })
    assert response.status_code == 202
