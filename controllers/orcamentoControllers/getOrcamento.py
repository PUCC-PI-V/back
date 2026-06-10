from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT, ORCAMENTO_TABLE
import mysql.connector
import asyncio


def _connect():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
    )


async def get_all_orcamentos(table=ORCAMENTO_TABLE):
    def _work():
        conn = _connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            cur.close()
            return rows
        finally:
            conn.close()

    return await asyncio.to_thread(_work)
