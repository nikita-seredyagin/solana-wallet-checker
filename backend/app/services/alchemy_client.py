import httpx

from app.config import settings

RPC_URL = settings.rpc_url
NFT_URL = settings.nft_url


async def rpc_call(client: httpx.AsyncClient, method: str, params: list) -> dict:
    response = await client.post(
        RPC_URL,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
    )
    response.raise_for_status()
    response_data = response.json()
    if "error" in response_data:
        raise ValueError(response_data["error"].get("message", "Alchemy RPC error"))
    return response_data


async def fetch_sol_balance(client: httpx.AsyncClient, address: str) -> float:
    response_data = await rpc_call(client, "getBalance", [address])
    lamports = response_data["result"]["value"]
    return lamports / 1e9


async def fetch_spl_tokens(client: httpx.AsyncClient, address: str) -> list[dict]:
    response_data = await rpc_call(
        client,
        "getTokenAccountsByOwner",
        [
            address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"},
        ],
    )
    tokens = []
    for token_account in response_data["result"]["value"]:
        token_info = token_account["account"]["data"]["parsed"]["info"]
        ui_amount = token_info["tokenAmount"]["uiAmount"]
        if ui_amount and ui_amount > 0:
            tokens.append(
                {
                    "mint": token_info["mint"],
                    "symbol": "",
                    "amount": ui_amount,
                }
            )
    return tokens


async def fetch_nfts(client: httpx.AsyncClient, address: str) -> list[dict]:
    response = await client.get(
        f"{NFT_URL}/getNFTsForOwner",
        params={"owner": address, "withMetadata": "true"},
    )
    if response.status_code != 200:
        return []
    response_data = response.json()
    nfts = []
    for nft_item in response_data.get("ownedNfts", []):
        nfts.append(
            {
                "mint": nft_item.get("mint", ""),
                "name": nft_item.get("name", ""),
                "collection": (nft_item.get("collection") or {}).get("name", ""),
            }
        )
    return nfts


async def fetch_last_transaction(client: httpx.AsyncClient, address: str) -> int | None:
    response_data = await rpc_call(
        client,
        "getSignaturesForAddress",
        [address, {"limit": 1}],
    )
    signatures = response_data["result"]
    if not signatures:
        return None
    return signatures[0].get("blockTime")
