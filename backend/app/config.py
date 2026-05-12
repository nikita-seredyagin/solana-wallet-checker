from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    alchemy_api_key: str
    alchemy_solana_base: str = "https://solana-mainnet.g.alchemy.com/v2"
    alchemy_nft_base: str = "https://solana-mainnet.g.alchemy.com/nft/v3"

    database_url: str = "sqlite+aiosqlite:///./checker.db"
    redis_url: str = "redis://localhost:6379/0"
    max_concurrency: int = 10
    max_addresses_per_request: int = 1000
    bulk_cache_ttl_seconds: int = 60

    @computed_field
    @property
    def rpc_url(self) -> str:
        return f"{self.alchemy_solana_base.rstrip('/')}/{self.alchemy_api_key}"

    @computed_field
    @property
    def nft_url(self) -> str:
        return f"{self.alchemy_nft_base.rstrip('/')}/{self.alchemy_api_key}"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
