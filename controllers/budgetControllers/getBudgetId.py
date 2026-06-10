from datetime import datetime
from decimal import Decimal

from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
import mysql.connector
import asyncio
from fastapi import HTTPException

from controllers.orcamentoControllers import getOrcamentoByTatuagem

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


def _format_date(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    return str(value)


def _format_currency(cents: int | None) -> str:
    if cents is None:
        return "Nao informado"
    reais = cents / 100
    formatted = f"{reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _to_bool(value) -> bool:
    return bool(value)


def _to_number(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def _map_tatto_info(row: dict) -> dict:
    return {
        "id": row.get("id_tatuagem"),
        "usuario_id": row.get("usuario_id"),
        "nome": row.get("nome") or "",
        "email": row.get("email") or "",
        "telefone": row.get("telefone") or "",
        "data": _format_date(row.get("created_at")),
        "cliente": row.get("cliente") or "",
        "ideia": row.get("descricao") or "",
        "area": row.get("area_tatuada") or "",
        "local": row.get("regiao_especifica") or "",
        "estilo": row.get("estilo") or "",
        "tamanho": row.get("tamanho") or "",
        "sombreamento": _to_bool(row.get("sombreamento")),
        "colorido": _to_bool(row.get("colorido")),
        "valor": _format_currency(row.get("estimativa_valor")),
        "dificuldade": row.get("dificuldade_ia") or "",
        "justificativaIA": row.get("justificativa_ia") or "",
    }


def _map_calculate_info(row: dict) -> dict:
    return {
        "id_orcamento": row.get("id_orcamento"),
        "tatuagem": row.get("tatuagem"),
        "usuario": row.get("usuario"),
        "admin": row.get("admin"),
        "tinta": _to_number(row.get("tinta")),
        "materiais": _to_number(row.get("materiais")),
        "area": _to_number(row.get("area")),
        "taxa_fixa": _to_number(row.get("taxa_fixa")),
        "valor_hora": _to_number(row.get("valor_hora")),
        "tempo_estimado": row.get("tempo_estimado"),
        "dificuldade": row.get("dificuldade") or "",
        "valor_orcamento": row.get("valor_orcamento"),
        "valor": _format_currency(row.get("valor_orcamento")),
        "data": _format_date(row.get("created_at")),
    }


async def get_budget_by_id(budget_id: int):
    def _work():
        conn = _connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"""
                SELECT
                    t.id_tatuagem,
                    t.usuario_id,
                    t.cliente,
                    t.descricao,
                    t.area_tatuada,
                    t.regiao_especifica,
                    t.estilo,
                    t.tamanho,
                    t.sombreamento,
                    t.colorido,
                    t.estimativa_valor,
                    t.dificuldade_ia,
                    t.justificativa_ia,
                    t.created_at,
                    u.nome,
                    u.email,
                    u.telefone
                FROM {TATTOO_TABLE} t
                LEFT JOIN {USER_TABLE} u ON u.id = t.usuario_id
                WHERE t.id_tatuagem = %s
                LIMIT 1
                """,
                (budget_id,),
            )
            row = cur.fetchone()
            cur.close()
            return row
        finally:
            conn.close()

    row = await asyncio.to_thread(_work)
    if row is None:
        raise HTTPException(status_code=404, detail="Orcamento nao encontrado.")

    orcamento = await getOrcamentoByTatuagem.get_orcamento_by_tatuagem(budget_id)

    return {
        "tatto_info": _map_tatto_info(row),
        "calculate_info": _map_calculate_info(orcamento) if orcamento else None,
    }
