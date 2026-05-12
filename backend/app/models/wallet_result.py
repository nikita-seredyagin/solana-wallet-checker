import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import JSON

from app.database import Base

JSON_TYPE = JSON


class WalletResult(Base):
    __tablename__ = "wallet_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(44), nullable=False, index=True)
    sol_balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    spl_tokens: Mapped[dict | None] = mapped_column(JSON_TYPE, nullable=True)
    nfts: Mapped[dict | None] = mapped_column(JSON_TYPE, nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    task: Mapped["Task"] = relationship("Task", back_populates="results")


from app.models.task import Task  # noqa: E402
