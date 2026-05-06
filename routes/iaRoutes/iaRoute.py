from fastapi import APIRouter, Request
from controllers.iaControllers import iaController

router = APIRouter()

@router.post("/prompt")
async def prompt(request: Request):
    return await iaController.prompt_index(request)