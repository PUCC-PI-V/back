from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
import mysql.connector
import asyncio


async def get_all_orcamentos(table="orcamento"):
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
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        try:
            conn.close()
        except Exception:
            pass


async def get_orcamento_by_id(id_orcamento, table="orcamento"):
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
        cur.execute(f"SELECT * FROM {table} WHERE id_orcamento = %s LIMIT 1", (id_orcamento,))
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        try:
            conn.close()
        except Exception:
            pass


async def create_orcamento(
    tatuagem,
    usuario,
    admin,
    tinta,
    materiais,
    area,
    taxa_fixa,
    valor_hora,
    tempo_estimado,
    dificuldade,
    table="orcamento",
):
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
            f"INSERT INTO {table} (tatuagem, usuario, admin, tinta, materiais, area, taxa_fixa, valor_hora, tempo_estimado, dificuldade) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                tatuagem,
                usuario,
                admin,
                tinta,
                materiais,
                area,
                taxa_fixa,
                valor_hora,
                tempo_estimado,
                dificuldade,
            ),
        )
        conn.commit()
        last_id = cur.lastrowid
        cur.close()
        return {"id_orcamento": last_id}
    finally:
        try:
            conn.close()
        except Exception:
            pass
