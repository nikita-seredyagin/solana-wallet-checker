import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.task import CheckRequest, TaskCreatedResponse
from app.services import task_service

router = APIRouter(prefix="/api/v1", tags=["check"])


@router.post("/check", response_model=TaskCreatedResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_check_task(body: CheckRequest, db: AsyncSession = Depends(get_db)):
    if len(body.addresses) > settings.max_addresses_per_request:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Too many addresses: max {settings.max_addresses_per_request}",
        )

    task = await task_service.create_task(body.addresses, body.options, db)

    asyncio.create_task(
        task_service.process_task(task.id, body.addresses, body.options)
    )

    return TaskCreatedResponse(
        task_id=task.id,
        status=task.status,
        total=task.total,
        created_at=task.created_at,
    )
