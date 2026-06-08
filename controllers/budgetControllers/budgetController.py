import os
from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
import mysql.connector
import asyncio
from fastapi import HTTPException
from services.iaServices import iaService
from services.emailServices import emailService

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")

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


async def get_user_by_email(email: str):
    def _work():
        conn = _connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                f"SELECT * FROM {USER_TABLE} WHERE email = %s LIMIT 1",
                (email,),
            )
            row = cur.fetchone()
            cur.close()
            return row
        finally:
            conn.close()

    return await asyncio.to_thread(_work)


async def create_user(nome, data_nasc, telefone, email):
    def _work():
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute(
                f"""
                INSERT INTO {USER_TABLE}
                    (nome, data_nasc, telefone, email)
                VALUES (%s, %s, %s, %s)
                """,
                (nome, data_nasc, telefone, email),
            )
            conn.commit()
            cur.close()
        finally:
            conn.close()

    await asyncio.to_thread(_work)


async def create_tattoo(
    cliente,
    tamanho,
    sombreamento,
    colorido,
    estilo,
    area_tatuada,
    regiao_especifica,
    descricao,
    estimativa_valor,
    dificuldade_ia,
    justificativa_ia,
):
    def _work():
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute(
                f"""
                INSERT INTO {TATTOO_TABLE}
                    (
                        cliente, tamanho, sombreamento, colorido, estilo,
                        area_tatuada, regiao_especifica, descricao,
                        estimativa_valor, dificuldade_ia, justificativa_ia
                    )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    cliente,
                    tamanho,
                    sombreamento,
                    colorido,
                    estilo,
                    area_tatuada,
                    regiao_especifica,
                    descricao,
                    estimativa_valor,
                    dificuldade_ia,
                    justificativa_ia,
                ),
            )
            conn.commit()
            tattoo_id = cur.lastrowid
            cur.close()
            return tattoo_id
        finally:
            conn.close()

    return await asyncio.to_thread(_work)


async def _analyze_budget_with_ia(
    cliente,
    tamanho,
    sombreamento,
    colorido,
    estilo,
    area_tatuada,
    regiao_especifica,
    descricao,
):
    def _work():
        return iaService.analyze_budget(
            cliente,
            tamanho,
            sombreamento,
            colorido,
            estilo,
            area_tatuada,
            regiao_especifica,
            descricao,
        )

    return await asyncio.to_thread(_work)


async def create_budget(
    nome,
    data_nasc,
    telefone,
    email,
    cliente,
    tamanho,
    sombreamento,
    colorido,
    estilo,
    area_tatuada,
    regiao_especifica,
    descricao,
):
    existing_user = await get_user_by_email(email)
    created_user = False

    if existing_user is None:
        await create_user(nome, data_nasc, telefone, email)
        created_user = True

    try:
        ia_result = await _analyze_budget_with_ia(
            cliente,
            tamanho,
            sombreamento,
            colorido,
            estilo,
            area_tatuada,
            regiao_especifica,
            descricao,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Falha ao analisar orcamento com IA: {exc}",
        ) from exc

    tattoo_id = await create_tattoo(
        cliente,
        tamanho,
        sombreamento,
        colorido,
        estilo,
        area_tatuada,
        regiao_especifica,
        descricao,
        ia_result["estimativaValor"],
        ia_result["dificuldadeIa"],
        ia_result["justificativaIa"],
    )

    form_link = f"{FRONTEND_URL}/admin/calculate/{tattoo_id}"

    try:
        await asyncio.to_thread(
            emailService.send_email,
            tattoo_description=descricao,
            form_link=form_link,
            client_name=cliente,
            dificuldade_ia=ia_result["dificuldadeIa"],
            estimativa_valor=ia_result["estimativaValor"],
            justificativa_ia=ia_result["justificativaIa"],
        )
        email_sent = True
    except Exception as exc:
        print(f"Falha ao enviar email do orcamento {tattoo_id}: {exc}")
        email_sent = False

    return {
        "created_user": created_user,
        "cliente": cliente,
        "tattoo_id": tattoo_id,
        "estimativaValor": ia_result["estimativaValor"],
        "dificuldadeIa": ia_result["dificuldadeIa"],
        "justificativaIa": ia_result["justificativaIa"],
        "form_link": form_link,
        "email_sent": email_sent,
    }
