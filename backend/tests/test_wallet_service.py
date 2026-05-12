from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.wallet_service import build_wallet_response


ADDRESS = "BJS5s36uAYzsbKskfwfazzKtqmkFSDrHyvxjeCKZpnoc"
RECENT_BLOCK_TIME = int(datetime.now(timezone.utc).timestamp())
OLD_BLOCK_TIME = int((datetime.now(timezone.utc) - timedelta(days=100)).timestamp())


async def test_is_active_true_for_recent_transaction():
    with patch("app.services.wallet_service.fetch_all", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (2.0, [], [], RECENT_BLOCK_TIME)
        async with httpx.AsyncClient() as client:
            result = await build_wallet_response(ADDRESS, client, semaphore=None)
    assert result.is_active is True
    assert result.sol_balance == 2.0


async def test_is_active_false_for_old_transaction():
    with patch("app.services.wallet_service.fetch_all", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (0.5, [], [], OLD_BLOCK_TIME)
        async with httpx.AsyncClient() as client:
            result = await build_wallet_response(ADDRESS, client, semaphore=None)
    assert result.is_active is False


async def test_is_active_false_when_no_transactions():
    with patch("app.services.wallet_service.fetch_all", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (0.0, [], [], None)
        async with httpx.AsyncClient() as client:
            result = await build_wallet_response(ADDRESS, client, semaphore=None)
    assert result.is_active is False
    assert result.last_activity_at is None


async def test_spl_tokens_and_nfts_mapped_correctly():
    spl_raw = [{"mint": "MintA", "symbol": "USDC", "amount": 100.0}]
    nfts_raw = [{"mint": "NFT1", "name": "My NFT", "collection": "Cool"}]
    with patch("app.services.wallet_service.fetch_all", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (1.0, spl_raw, nfts_raw, RECENT_BLOCK_TIME)
        async with httpx.AsyncClient() as client:
            result = await build_wallet_response(ADDRESS, client, semaphore=None)
    assert len(result.spl_tokens) == 1
    assert result.spl_tokens[0].mint == "MintA"
    assert result.spl_tokens[0].amount == 100.0
    assert len(result.nfts) == 1
    assert result.nfts[0].name == "My NFT"


async def test_semaphore_is_acquired_when_provided():
    import asyncio
    semaphore = asyncio.Semaphore(1)
    with patch("app.services.wallet_service.fetch_all", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (0.0, [], [], None)
        async with httpx.AsyncClient() as client:
            await build_wallet_response(ADDRESS, client, semaphore=semaphore)
    assert semaphore._value == 1  # семафор освобождён после выполнения
