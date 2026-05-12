import asyncio
from datetime import datetime, timezone, timedelta

import httpx

from app.schemas.wallet import NftSchema, SplTokenSchema, WalletResponseSchema
from app.services.alchemy_client import fetch_sol_balance, fetch_spl_tokens, fetch_nfts, fetch_last_transaction

ACTIVE_DAYS = 90


async def get_wallet_info(
    address: str,
    client: httpx.AsyncClient | None = None,
    semaphore: asyncio.Semaphore | None = None,
) -> WalletResponseSchema:
    if client is None:
        async with httpx.AsyncClient(timeout=10.0) as owned_client:
            return await build_wallet_response(address, owned_client, semaphore)
    return await build_wallet_response(address, client, semaphore)


async def build_wallet_response(
    address: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore | None,
) -> WalletResponseSchema:
    if semaphore is not None:
        async with semaphore:
            sol_balance, spl_tokens_raw, nfts_raw, last_block_time = await fetch_all(client, address)
    else:
        sol_balance, spl_tokens_raw, nfts_raw, last_block_time = await fetch_all(client, address)

    last_activity_at = None
    if last_block_time is not None:
        last_activity_at = datetime.fromtimestamp(last_block_time, tz=timezone.utc)

    is_active = (
        last_activity_at is not None
        and last_activity_at >= datetime.now(tz=timezone.utc) - timedelta(days=ACTIVE_DAYS)
    )

    return WalletResponseSchema(
        address=address,
        sol_balance=sol_balance,
        spl_tokens=[SplTokenSchema(**token) for token in spl_tokens_raw],
        nfts=[NftSchema(**nft) for nft in nfts_raw],
        last_activity_at=last_activity_at,
        is_active=is_active,
    )


async def fetch_all(client: httpx.AsyncClient, address: str):
    return await asyncio.gather(
        fetch_sol_balance(client, address),
        fetch_spl_tokens(client, address),
        fetch_nfts(client, address),
        fetch_last_transaction(client, address),
    )
