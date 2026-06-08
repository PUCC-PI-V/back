from fastapi import HTTPException
from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
import mysql.connector
import asyncio

ADMIN_TABLE = "User"


async def login(email: str, password: str):
    def _work():
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
        )
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"SELECT id, email, password FROM {ADMIN_TABLE} WHERE email = %s LIMIT 1",
                (email,),
            )
            row = cur.fetchone()
            cur.close()
            return row
        finally:
            try:
                conn.close()
            except Exception:
                pass

    user = await asyncio.to_thread(_work)

    if user is None or user.get("password") != password:
        raise HTTPException(status_code=401, detail="Email ou senha invalidos.")

    return {
        "success": True,
        "user": {"id": user["id"], "email": user["email"]},
    }
