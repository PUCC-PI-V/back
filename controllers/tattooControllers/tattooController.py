from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
from services.iaServices.iaService import answer_question
import mysql.connector
import asyncio
import re


def extract_valor_ia(texto):
    m = re.search(r"R\$\s*([0-9\.\,]+)", texto)
    if not m:
        return None
    raw = m.group(1)
    norm = raw.replace(".", "").replace(",", ".")
    try:
        return float(norm) if "." in norm else int(norm)
    except ValueError:
        return None

async def get_valor_ia(texto):
    response = await asyncio.to_thread(answer_question, texto)
    return extract_valor_ia(response)

async def get_tattoo_by_id(id_tatuagem, table="tatuagem"):
    conn = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME or None,
            port=DB_PORT,
        ),
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
    # Insert row first and get inserted id, then schedule AI estimation in background
    conn = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME or None,
            port=DB_PORT,
        ),
    )
    try:
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO {table} (cliente, tamanho, sombreamento, colorido, estilo, area_tatuada, regiao_especifica) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (cliente, tamanho, sombreamento, colorido, estilo, area_tatuada, regiao_especifica),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Background task: compute estimated value and update row
    async def _compute_and_update(id_, area, region, style, size, shade, colored, table_name):
        try:
            prompt = (
                f"Qual o valor estimado para uma tatuagem com as seguintes características: "
                f"tamanho {size}, sombreamento {'sim' if shade else 'nao'}, colorido {'sim' if colored else 'nao'}, "
                f"estilo {style}, area tatuada {area}, regiao especifica {region}? Responda apenas com o valor estimado em reais, sem texto adicional."
            )
            valor = await get_valor_ia(prompt)
            if valor is None:
                # couldn't extract a value from AI response; skip update or log
                return
            await add_estim_value(id_, valor, table_name)
        except Exception:
            import traceback

            traceback.print_exc()

    asyncio.create_task(_compute_and_update(new_id, area_tatuada, regiao_especifica, estilo, tamanho, sombreamento, colorido, table))
    return new_id
        
# route to add the estimated value returned from the AI model
async def add_estim_value(id_tatuagem, valor_estimado, table="tatuagem"):
    
    conn = await asyncio.get_event_loop().run_in_executor(None, lambda: mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME or None,
        port=DB_PORT,
    ),
)
    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE {table} SET valor = %s WHERE id_tatuagem = %s",
            (valor_estimado, id_tatuagem),
        )
        conn.commit()
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass