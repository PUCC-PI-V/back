from fastapi import APIRouter, HTTPException, Request
from controllers.budgetControllers import budgetController

router = APIRouter()


def _parse_bool_to_int(value):
    if isinstance(value, bool):
        return 1 if value else 0
    if value is None or value == "":
        return None
    try:
        return 1 if int(value) != 0 else 0
    except (TypeError, ValueError):
        text = str(value).strip().lower()
        if text in ("1", "true", "yes", "y", "on"):
            return 1
        if text in ("0", "false", "no", "n", "off"):
            return 0
    return None


def _get_field(data: dict, *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


@router.post("/submit", status_code=201)
async def submit_budget(request: Request):
    data = await request.json()

    usuario = data.get("usuario") or {}
    tatuagem = data.get("tatuagem") or {}

    if not isinstance(usuario, dict) or not isinstance(tatuagem, dict):
        raise HTTPException(
            status_code=400,
            detail="Formato invalido. Envie os objetos 'usuario' e 'tatuagem'.",
        )

    nome = _get_field(usuario, "nome")
    data_nasc = _get_field(usuario, "data_nasc")
    telefone = _get_field(usuario, "telefone")
    email = _get_field(usuario, "email")

    cliente = _get_field(tatuagem, "cliente")
    tamanho = _get_field(tatuagem, "tamanho")
    sombreamento = _parse_bool_to_int(tatuagem.get("sombreamento"))
    colorido = _parse_bool_to_int(tatuagem.get("colorido"))
    estilo = _get_field(tatuagem, "estilo")
    area_tatuada = _get_field(tatuagem, "area_tatuada", "area")
    regiao_especifica = _get_field(
        tatuagem, "regiao_especifica", "regiao especifica"
    )
    descricao = _get_field(tatuagem, "descricao")

    missing_user_fields = not all([nome, data_nasc, telefone, email])
    missing_tattoo_fields = not all(
        [cliente, tamanho, estilo, area_tatuada, regiao_especifica, descricao]
    )
    invalid_flags = (
        "sombreamento" not in tatuagem
        or "colorido" not in tatuagem
        or sombreamento is None
        or colorido is None
    )

    if missing_user_fields or missing_tattoo_fields or invalid_flags:
        raise HTTPException(
            status_code=400,
            detail="Todos os campos sao obrigatorios e devem ser validos.",
        )

    result = await budgetController.create_budget(
        nome=nome,
        data_nasc=data_nasc,
        telefone=telefone,
        email=email,
        cliente=cliente,
        tamanho=tamanho,
        sombreamento=sombreamento,
        colorido=colorido,
        estilo=estilo,
        area_tatuada=area_tatuada,
        regiao_especifica=regiao_especifica,
        descricao=descricao,
    )

    return {
        "success": True,
        "message": "Orcamento criado com sucesso.",
        **result,
    }
