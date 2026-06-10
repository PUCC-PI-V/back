from fastapi import APIRouter, HTTPException, Request
from controllers.orcamentoControllers import (
    getOrcamento,
    getOrcamentoByTatuagem,
    orcamentoController,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)


def _parse_cents(value):
    if value is None or value == "":
        return None
    try:
        cents = int(value)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="O campo 'valor_orcamento' deve ser um inteiro em centavos.",
        )
    if cents < 0:
        raise HTTPException(
            status_code=400,
            detail="O campo 'valor_orcamento' nao pode ser negativo.",
        )
    return cents


@router.get("/list")
@limiter.limit("10/minute")
async def list_orcamentos(request: Request):
    return await getOrcamento.get_all_orcamentos()


@router.get("/tatuagem/{tatuagem_id}")
@limiter.limit("10/minute")
async def get_orcamento_by_tatuagem(request: Request, tatuagem_id: int):
    row = await getOrcamentoByTatuagem.get_orcamento_by_tatuagem(tatuagem_id)
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Orcamento ativo nao encontrado para esta tatuagem.",
        )
    return row


@router.get("/{orcamento_id}")
@limiter.limit("10/minute")
async def get_orcamento(request: Request, orcamento_id: int):
    row = await orcamentoController.get_orcamento_by_id(orcamento_id)
    if not row:
        raise HTTPException(status_code=404, detail="Orcamento nao encontrado")
    return row


@router.post("/submit", status_code=201)
@limiter.limit("5/minute")
async def submit_orcamento(request: Request):
    data = await request.json()

    tatuagem = data.get("tatuagem")
    usuario = data.get("usuario")
    admin = data.get("admin")
    tinta = data.get("tinta")
    materiais = data.get("materiais")
    area = data.get("area")
    taxa_fixa = data.get("taxa_fixa")
    valor_hora = data.get("valor_hora")
    tempo_estimado = data.get("tempo_estimado")
    dificuldade = data.get("dificuldade")
    valor_orcamento = _parse_cents(data.get("valor_orcamento"))

    if tatuagem is None or usuario is None or valor_orcamento is None:
        raise HTTPException(
            status_code=400,
            detail="Campos obrigatorios: 'tatuagem', 'usuario' e 'valor_orcamento' (centavos).",
        )

    result = await orcamentoController.create_orcamento(
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
    )

    return {"success": True, "message": "Orcamento criado", **result}
