import os
os.environ.setdefault("ALCHEMY_API_KEY", "test_fake_key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_checker.db")

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import AsyncSessionLocal, Base, engine
from app.main import app
from app.schemas.wallet import WalletResponseSchema

SAMPLE_ADDRESS = "2JU69zJUgYeZZbkD6RinqWn6cTpFcEJX5yUU9PdNHtnZ"

SAMPLE_WALLET = WalletResponseSchema(
    address=SAMPLE_ADDRESS,
    sol_balance=1.5,
    spl_tokens=[],
    nfts=[],
    last_activity_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    is_active=True,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    from app.models import task, wallet_result  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    if os.path.exists("./test_checker.db"):
        os.remove("./test_checker.db")


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def http_client():
    with patch("app.main.init_redis", new_callable=AsyncMock), \
         patch("app.main.close_redis", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client


@pytest.fixture
def mock_get_wallet_info():
    with patch("app.routers.wallet.get_wallet_info", new_callable=AsyncMock) as mocked:
        mocked.return_value = SAMPLE_WALLET
        yield mocked
