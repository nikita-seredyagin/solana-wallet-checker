from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import SAMPLE_ADDRESS, SAMPLE_WALLET

INVALID_ADDRESS = "not_a_valid_address!!!"
SHORT_ADDRESS = "abc"


async def test_valid_address_returns_200(http_client, mock_get_wallet_info):
    response = await http_client.get(f"/api/v1/wallet/{SAMPLE_ADDRESS}")
    assert response.status_code == 200
    body = response.json()
    assert body["address"] == SAMPLE_ADDRESS
    assert body["sol_balance"] == 1.5
    assert body["is_active"] is True


async def test_invalid_address_format_returns_422(http_client):
    response = await http_client.get(f"/api/v1/wallet/{INVALID_ADDRESS}")
    assert response.status_code == 422


async def test_too_short_address_returns_422(http_client):
    response = await http_client.get(f"/api/v1/wallet/{SHORT_ADDRESS}")
    assert response.status_code == 422


async def test_alchemy_value_error_returns_400(http_client):
    with patch("app.routers.wallet.get_wallet_info", new_callable=AsyncMock) as mocked:
        mocked.side_effect = ValueError("Invalid param: wrong address")
        response = await http_client.get(f"/api/v1/wallet/{SAMPLE_ADDRESS}")
    assert response.status_code == 400
    assert "Invalid param" in response.json()["detail"]


async def test_alchemy_unavailable_returns_502(http_client):
    with patch("app.routers.wallet.get_wallet_info", new_callable=AsyncMock) as mocked:
        mocked.side_effect = Exception("connection timeout")
        response = await http_client.get(f"/api/v1/wallet/{SAMPLE_ADDRESS}")
    assert response.status_code == 502


async def test_response_schema_fields_present(http_client, mock_get_wallet_info):
    response = await http_client.get(f"/api/v1/wallet/{SAMPLE_ADDRESS}")
    body = response.json()
    assert "address" in body
    assert "sol_balance" in body
    assert "spl_tokens" in body
    assert "nfts" in body
    assert "is_active" in body
    assert "last_activity_at" in body
