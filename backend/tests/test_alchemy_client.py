from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.alchemy_client import (
    fetch_last_transaction,
    fetch_nfts,
    fetch_sol_balance,
    fetch_spl_tokens,
    rpc_call,
)


FAKE_REQUEST = httpx.Request("POST", "http://test")


def make_rpc_response(result) -> httpx.Response:
    return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": result}, request=FAKE_REQUEST)


def make_rpc_error(message: str) -> httpx.Response:
    return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "error": {"code": -32602, "message": message}}, request=FAKE_REQUEST)


@pytest.fixture
def mock_client():
    return AsyncMock(spec=httpx.AsyncClient)


async def test_rpc_call_raises_on_error_response(mock_client):
    mock_client.post.return_value = make_rpc_error("Invalid param")
    with pytest.raises(ValueError, match="Invalid param"):
        await rpc_call(mock_client, "getBalance", ["bad_address"])


async def test_fetch_sol_balance_converts_lamports(mock_client):
    mock_client.post.return_value = make_rpc_response({"value": 1_500_000_000})
    balance = await fetch_sol_balance(mock_client, "addr")
    assert balance == 1.5


async def test_fetch_sol_balance_zero(mock_client):
    mock_client.post.return_value = make_rpc_response({"value": 0})
    balance = await fetch_sol_balance(mock_client, "addr")
    assert balance == 0.0


async def test_fetch_spl_tokens_filters_zero_balances(mock_client):
    mock_client.post.return_value = make_rpc_response({
        "value": [
            {"account": {"data": {"parsed": {"info": {
                "mint": "MintA",
                "tokenAmount": {"uiAmount": 10.0},
            }}}}},
            {"account": {"data": {"parsed": {"info": {
                "mint": "MintB",
                "tokenAmount": {"uiAmount": 0.0},
            }}}}},
            {"account": {"data": {"parsed": {"info": {
                "mint": "MintC",
                "tokenAmount": {"uiAmount": None},
            }}}}},
        ]
    })
    tokens = await fetch_spl_tokens(mock_client, "addr")
    assert len(tokens) == 1
    assert tokens[0]["mint"] == "MintA"
    assert tokens[0]["amount"] == 10.0


async def test_fetch_spl_tokens_empty(mock_client):
    mock_client.post.return_value = make_rpc_response({"value": []})
    tokens = await fetch_spl_tokens(mock_client, "addr")
    assert tokens == []


async def test_fetch_nfts_returns_empty_on_non_200(mock_client):
    mock_client.get.return_value = httpx.Response(401)
    nfts = await fetch_nfts(mock_client, "addr")
    assert nfts == []


async def test_fetch_nfts_parses_response(mock_client):
    mock_client.get.return_value = httpx.Response(200, json={
        "ownedNfts": [
            {"mint": "MintNFT1", "name": "Cool NFT", "collection": {"name": "Cool Collection"}},
        ]
    })
    nfts = await fetch_nfts(mock_client, "addr")
    assert len(nfts) == 1
    assert nfts[0]["mint"] == "MintNFT1"
    assert nfts[0]["name"] == "Cool NFT"
    assert nfts[0]["collection"] == "Cool Collection"


async def test_fetch_last_transaction_returns_none_when_no_signatures(mock_client):
    mock_client.post.return_value = make_rpc_response([])
    result = await fetch_last_transaction(mock_client, "addr")
    assert result is None


async def test_fetch_last_transaction_returns_block_time(mock_client):
    mock_client.post.return_value = make_rpc_response([{"blockTime": 1700000000, "signature": "sig"}])
    result = await fetch_last_transaction(mock_client, "addr")
    assert result == 1700000000
