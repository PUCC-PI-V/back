from fastapi import APIRouter, HTTPException, Request
from controllers.orcamentoControllers import orcamentoController
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)


@router.get("/list")
@limiter.limit("10/minute")
async def list_orcamentos(request: Request):
    return await orcamentoController.get_all_orcamentos()


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

    # Basic expected fields
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

    if tatuagem is None or usuario is None:
        raise HTTPException(status_code=400, detail="Campos obrigatorios: 'tatuagem' e 'usuario'")

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
    )

    return {"success": True, "message": "Orcamento criado", **result}
