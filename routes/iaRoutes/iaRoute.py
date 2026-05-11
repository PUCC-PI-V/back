from fastapi import APIRouter, Request
from controllers.iaControllers import iaController
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)

@router.post("/prompt")
@limiter.limit("5/minute")
async def prompt(request: Request):
    return await iaController.prompt_index(request)