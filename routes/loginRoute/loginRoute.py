from http.client import HTTPException
from fastapi import APIRouter, Request
from controllers.loginControllers import loginController
from routes.iaRoutes.iaRoute import limiter

router = APIRouter()

@router.post("/login")
@limiter.limit("2/minute")
async def login(request: Request):
    data = await request.json()
    email = str(data.get("email") or "").strip()
    password = str(data.get("password") or "").strip()

    if not email or not password:
        raise HTTPException(
            status_code=400, detail="Email e senha sao obrigatorios."
        )

    return await loginController.login(email, password)