from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT, ORCAMENTO_TABLE
import mysql.connector
import asyncio

from services.emailServices.emails import orcamentoConfirmacaoEmail


def _connect():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
    )


async def get_orcamento_by_id(id_orcamento, table=ORCAMENTO_TABLE):
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
        cur.execute(
            f"SELECT * FROM {table} WHERE id_orcamento = %s AND active = 1 LIMIT 1",
            (id_orcamento,),
        )
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
    valor_orcamento,
    email,
    client_name="",
    table=ORCAMENTO_TABLE,
):
    def _work():
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute(
                f"UPDATE {table} SET active = 0 WHERE tatuagem = %s AND active = 1",
                (tatuagem,),
            )
            cur.execute(
                f"""
                INSERT INTO {table}
                    (tatuagem, usuario, admin, tinta, materiais, area,
                     taxa_fixa, valor_hora, tempo_estimado, dificuldade, valor_orcamento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
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
                    valor_orcamento,
                ),
            )
            conn.commit()
            last_id = cur.lastrowid
            cur.close()
            return {"id_orcamento": last_id}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    result = await asyncio.to_thread(_work)

    email_sent = False
    try:
        await asyncio.to_thread(
            orcamentoConfirmacaoEmail.send,
            to=email,
            client_name=client_name,
            valor_orcamento=valor_orcamento,
            dificuldade=dificuldade or "",
        )
        email_sent = True
    except Exception as exc:
        print(f"Falha ao enviar email de confirmacao do orcamento {result['id_orcamento']}: {exc}")

    return {**result, "email_sent": email_sent}
