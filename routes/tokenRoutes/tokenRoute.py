from fastapi import APIRouter, HTTPException, Request
from controllers.tokenControllers import tokenController

router = APIRouter()


@router.post("/validate")
async def verify_token_route(request: Request):
    data = await request.json()
    token = str(data.get("token") or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token obrigatorio.")
    return await tokenController.verify_token(token)