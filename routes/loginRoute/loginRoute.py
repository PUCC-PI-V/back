from fastapi import APIRouter, Request
from controllers.loginControllers import loginController
from routes.iaRoutes.iaRoute import limiter

router = APIRouter()

@router.post("/login")
@limiter.limit("2/minute")
async def login(request: Request):
    return await loginController.login(request)