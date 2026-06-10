import os
from database.conn import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
import mysql.connector
import asyncio
from services.iaServices import iaService
from services.emailServices.emails import budgetEmail, userBudgetThankYouEmail

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


async def create_user(nome, telefone, email):
    def _work():
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute(
                f"""
                INSERT INTO {USER_TABLE}
                    (nome, telefone, email)
                VALUES (%s, %s, %s)
                """,
                (nome, telefone, email),
            )
            conn.commit()
            user_id = cur.lastrowid
            cur.close()
            return user_id
        finally:
            conn.close()

    return await asyncio.to_thread(_work)


async def create_tattoo(
    usuario_id,
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
                        usuario_id, cliente, tamanho, sombreamento, colorido, estilo,
                        area_tatuada, regiao_especifica, descricao,
                        estimativa_valor, dificuldade_ia, justificativa_ia
                    )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    usuario_id,
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


async def update_tattoo_ia_result(
    tattoo_id,
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
                UPDATE {TATTOO_TABLE}
                SET estimativa_valor = %s,
                    dificuldade_ia = %s,
                    justificativa_ia = %s
                WHERE id_tatuagem = %s
                """,
                (estimativa_valor, dificuldade_ia, justificativa_ia, tattoo_id),
            )
            conn.commit()
            cur.close()
        finally:
            conn.close()

    await asyncio.to_thread(_work)


async def _process_budget_ia_background(
    tattoo_id,
    nome,
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
        print(f"Falha ao analisar orcamento {tattoo_id} com IA: {exc}")
        return

    try:
        await update_tattoo_ia_result(
            tattoo_id,
            ia_result["estimativaValor"],
            ia_result["dificuldadeIa"],
            ia_result["justificativaIa"],
        )
    except Exception as exc:
        print(f"Falha ao salvar analise da IA do orcamento {tattoo_id}: {exc}")
        return

    form_link = f"{FRONTEND_URL}/admin/calculate/{tattoo_id}"

    try:
        await asyncio.to_thread(
            budgetEmail.send,
            tattoo_description=descricao,
            form_link=form_link,
            client_name=cliente,
            dificuldade_ia=ia_result["dificuldadeIa"],
            estimativa_valor=ia_result["estimativaValor"],
            justificativa_ia=ia_result["justificativaIa"],
        )
    except Exception as exc:
        print(f"Falha ao enviar email admin do orcamento {tattoo_id}: {exc}")

    try:
        await asyncio.to_thread(
            userBudgetThankYouEmail.send,
            to=email,
            client_name=nome,
            estimativa_valor=ia_result["estimativaValor"],
        )
    except Exception as exc:
        print(f"Falha ao enviar email de agradecimento ao usuario {tattoo_id}: {exc}")


async def create_budget(
    nome,
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
        usuario_id = await create_user(nome, telefone, email)
        created_user = True
    else:
        usuario_id = existing_user["id"]

    tattoo_id = await create_tattoo(
        usuario_id,
        cliente,
        tamanho,
        sombreamento,
        colorido,
        estilo,
        area_tatuada,
        regiao_especifica,
        descricao,
        None,
        None,
        None,
    )

    asyncio.create_task(
        _process_budget_ia_background(
            tattoo_id,
            nome,
            email,
            cliente,
            tamanho,
            sombreamento,
            colorido,
            estilo,
            area_tatuada,
            regiao_especifica,
            descricao,
        )
    )

    return {
        "created_user": created_user,
        "cliente": cliente,
        "tattoo_id": tattoo_id,
        "estimativaValor": None,
        "dificuldadeIa": None,
        "justificativaIa": None,
        "ia_processing": True,
        "form_link": f"{FRONTEND_URL}/admin/calculate/{tattoo_id}",
    }
