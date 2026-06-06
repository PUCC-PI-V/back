from fastapi import HTTPException, Request
from database import conn as db
import asyncio

async def login(request: Request):
    data = await request.json()
    email = str(data.get("email") or "").strip()
    password = str(data.get("password") or "")

    if not email or not password:
        raise HTTPException(
            status_code=400, detail="Email e senha sao obrigatorios."
        )


    user = await asyncio.to_thread(db.get_user_by_email, email)
    if user is None or user["password"] != password:
        raise HTTPException(
            status_code=401, detail="Email ou senha invalidos."
        )

    return {
        "success": True,
        "user": {"id": user["id"], "email": user["email"]},
    }
