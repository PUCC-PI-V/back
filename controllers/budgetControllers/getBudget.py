from datetime import datetime

from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
import mysql.connector
import asyncio

USER_TABLE = "usuario"
TATTOO_TABLE = "tatuagem"


def _connect():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
    )


def _format_currency(cents: int | None) -> str:
    if cents is None:
        return "Nao informado"
    reais = cents / 100
    formatted = f"{reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _format_date(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    return str(value)


def _map_budget_row(row: dict) -> dict:
    return {
        "id": row["id_tatuagem"],
        "nome": row.get("nome") or "",
        "email": row.get("email") or "",
        "ideia": row.get("descricao") or "",
        "valor": _format_currency(row.get("estimativa_valor")),
        "data": _format_date(row.get("created_at")),
    }


async def get_all_budgets():
    def _work():
        conn = _connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                SELECT
                    t.id_tatuagem,
                    t.descricao,
                    t.estimativa_valor,
                    t.created_at,
                    u.nome,
                    u.email
                FROM {TATTOO_TABLE} t
                LEFT JOIN {USER_TABLE} u ON u.id = t.usuario_id
                ORDER BY t.created_at DESC, t.id_tatuagem DESC
                """
            )
            rows = cur.fetchall()
            cur.close()
            return [_map_budget_row(row) for row in rows]
        finally:
            conn.close()

    return await asyncio.to_thread(_work)
