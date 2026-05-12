import asyncio
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import get_cached_wallet, set_cached_wallet
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.task import Task, TaskStatus
from app.models.wallet_result import WalletResult
from app.schemas.task import CheckOptions
from app.schemas.wallet import WalletResponseSchema
from app.services.wallet_service import get_wallet_info


async def create_task(addresses: list[str], options: CheckOptions, db: AsyncSession) -> Task:
    task = Task(total=len(addresses))
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(task_id: str, db: AsyncSession) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def get_task_results(task_id: str, page: int, page_size: int, db: AsyncSession) -> list[WalletResult]:
    offset = (page - 1) * page_size
    result = await db.execute(
        select(WalletResult)
        .where(WalletResult.task_id == task_id)
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all())


async def update_task(task_id: str, db: AsyncSession, **fields) -> None:
    await db.execute(update(Task).where(Task.id == task_id).values(**fields))
    await db.commit()


async def process_task(task_id: str, addresses: list[str], options: CheckOptions) -> None:
    semaphore = asyncio.Semaphore(settings.max_concurrency)

    async with AsyncSessionLocal() as db:
        await update_task(task_id, db, status=TaskStatus.running)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            coroutines = [
                process_single_address(task_id, address, options, client, semaphore)
                for address in addresses
            ]
            await asyncio.gather(*coroutines)

        async with AsyncSessionLocal() as db:
            await update_task(task_id, db, status=TaskStatus.done, completed_at=datetime.now(timezone.utc))

    except Exception:
        async with AsyncSessionLocal() as db:
            await update_task(task_id, db, status=TaskStatus.failed, completed_at=datetime.now(timezone.utc))


async def process_single_address(
    task_id: str,
    address: str,
    options: CheckOptions,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> None:
    try:
        cached = await get_cached_wallet(address)
        if cached is not None:
            wallet_response = WalletResponseSchema.model_validate(cached)
        else:
            wallet_response = await get_wallet_info(address, client=client, semaphore=semaphore)
            await set_cached_wallet(address, wallet_response.model_dump(mode="json"))

        wallet_result = WalletResult(
            task_id=task_id,
            address=address,
            sol_balance=wallet_response.sol_balance,
            spl_tokens=[token.model_dump() for token in wallet_response.spl_tokens] if options.include_spl else [],
            nfts=[nft.model_dump() for nft in wallet_response.nfts] if options.include_nfts else [],
            last_activity_at=wallet_response.last_activity_at,
            is_active=wallet_response.is_active,
        )
        counter_update = {"processed": Task.processed + 1}
    except Exception as error:
        wallet_result = WalletResult(task_id=task_id, address=address, error=str(error))
        counter_update = {"processed": Task.processed + 1, "failed": Task.failed + 1}

    async with AsyncSessionLocal() as db:
        db.add(wallet_result)
        await db.execute(update(Task).where(Task.id == task_id).values(**counter_update))
        await db.commit()
