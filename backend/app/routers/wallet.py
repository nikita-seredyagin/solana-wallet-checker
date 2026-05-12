from fastapi import APIRouter, HTTPException, Path, status

from app.schemas.wallet import WalletResponseSchema
from app.services.wallet_service import get_wallet_info


SOLANA_ADDRESS_RE = r"^[1-9A-HJ-NP-Za-km-z]{32,44}$"

router = APIRouter(prefix="/api/v1/wallet", tags=["wallet"])


@router.get("/{wallet_address}", response_model=WalletResponseSchema, status_code=status.HTTP_200_OK)
async def check_wallet(
    wallet_address: str = Path(..., pattern=SOLANA_ADDRESS_RE, description="Solana wallet address in base58 format"),
):
    try:
        return await get_wallet_info(wallet_address)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
