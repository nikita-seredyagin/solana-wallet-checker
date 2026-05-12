from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.task import TaskStatusResponse
from app.schemas.wallet import WalletResponseSchema
from app.services import task_service

router = APIRouter(prefix="/api/v1/task", tags=["task"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.get_task(task_id, db)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    wallet_results = await task_service.get_task_results(task_id, page, page_size, db)

    results = [
        WalletResponseSchema(
            address=wallet_result.address,
            sol_balance=wallet_result.sol_balance or 0.0,
            spl_tokens=wallet_result.spl_tokens or [],
            nfts=wallet_result.nfts or [],
            last_activity_at=wallet_result.last_activity_at,
            is_active=wallet_result.is_active or False,
            error=wallet_result.error,
        )
        for wallet_result in wallet_results
    ]

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        total=task.total,
        processed=task.processed,
        failed=task.failed,
        created_at=task.created_at,
        completed_at=task.completed_at,
        results=results,
    )
