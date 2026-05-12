import datetime

from pydantic import BaseModel, Field


class SplTokenSchema(BaseModel):
    mint: str
    symbol: str
    amount: float
    
    
class NftSchema(BaseModel):
    mint: str
    name: str
    collection: str
    
    
class WalletResponseSchema(BaseModel):
    address: str
    sol_balance: float
    spl_tokens: list[SplTokenSchema]
    nfts: list[NftSchema]
    last_activity_at: datetime.datetime | None = None
    is_active: bool
    error: str | None = None