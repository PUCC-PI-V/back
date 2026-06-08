from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
import mysql.connector
import asyncio


async def get_tattoo_by_id(id_tatuagem, table="tatuagem"):
    conn = await asyncio.to_thread(
        mysql.connector.connect,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME or None,
        port=DB_PORT,
    )
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT * FROM {table} WHERE id_tatuagem = %s LIMIT 1", (id_tatuagem,))
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        try:
            conn.close()
        except Exception:
            pass
        
async def create_tattoo(cliente, tamanho, sombreamento, colorido, estilo, area_tatuada, regiao_especifica, table="tatuagem"):
    conn = await asyncio.to_thread(
        mysql.connector.connect,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME or None,
        port=DB_PORT,
    )
    try:
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO {table} (cliente, tamanho, sombreamento, colorido, estilo, area_tatuada, regiao_especifica) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (cliente, tamanho, sombreamento, colorido, estilo, area_tatuada, regiao_especifica),
        )
        conn.commit()
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass