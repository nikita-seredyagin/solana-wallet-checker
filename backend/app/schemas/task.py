from datetime import datetime

from pydantic import BaseModel, Field

from app.models.task import TaskStatus
from app.schemas.wallet import WalletResponseSchema


class CheckOptions(BaseModel):
    include_nfts: bool = True
    include_spl: bool = True


class CheckRequest(BaseModel):
    addresses: list[str] = Field(..., min_length=1)
    options: CheckOptions = CheckOptions()


class TaskCreatedResponse(BaseModel):
    task_id: str
    status: TaskStatus
    total: int
    created_at: datetime


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    total: int
    processed: int
    failed: int
    created_at: datetime
    completed_at: datetime | None
    results: list[WalletResponseSchema]

    model_config = {"from_attributes": True}
