from fastapi import HTTPException, Request
from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
import mysql.connector

import asyncio

async def login(email, password, table = "usuario"):
    conn = await asyncio.get_event_loop().run_in_executor(None, mysql.connector.connect,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME or None,
        port=DB_PORT,
    )
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT * FROM {table} WHERE email = %s AND senha = %s LIMIT 1", (email, password))
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        try:
            conn.close()
        except Exception:
            pass
