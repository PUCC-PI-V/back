from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
import mysql.connector
import asyncio


async def get_tattoo_by_id(tattoo_id, table="tatuagem"):
    conn = await asyncio.get_event_loop().run_in_executor(None, mysql.connector.connect,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME or None,
        port=DB_PORT,
    )
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT * FROM {table} WHERE id = %s LIMIT 1", (tattoo_id,))
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        try:
            conn.close()
        except Exception:
            pass
        
async def create_tattoo(name, description, price, table="tatuagem"):
    conn = await asyncio.get_event_loop().run_in_executor(None, mysql.connector.connect,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME or None,
        port=DB_PORT,
    )
    try:
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO {table} (name, description, price) VALUES (%s, %s, %s)",
            (name, description, price),
        )
        conn.commit()
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass