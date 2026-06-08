from fastapi import HTTPException
from utils.token.tokenVerify import verify_token as decode_token


async def verify_token(token: str):
    if not token:
        raise HTTPException(status_code=400, detail="Token obrigatorio.")

    payload = await decode_token(token)
    return {"valid": True, "payload": payload}
