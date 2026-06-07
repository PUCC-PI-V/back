from fastapi import APIRouter, Request, HTTPException
from controllers.tattooControllers import tattooController

router = APIRouter()

@router.post("/create_tattoo")
async def create_tattoo(request: Request):
    data = await request.json()
    cliente = str(data.get("cliente") or "").strip()
    tamanho = str(data.get("tamanho") or "").strip()
    def parse_bool_to_int(v):
        if isinstance(v, bool):
            return 1 if v else 0
        if v is None or v == "":
            return None
        try:
            return 1 if int(v) != 0 else 0
        except Exception:
            s = str(v).strip().lower()
            if s in ("1", "true", "yes", "y", "on"):
                return 1
            if s in ("0", "false", "no", "n", "off"):
                return 0
            return None

    sombreamento = parse_bool_to_int(data.get("sombreamento"))
    colorido = parse_bool_to_int(data.get("colorido"))
    estilo = str(data.get("estilo") or "").strip()
    area_tatuada = str(data.get("area_tatuada") or "").strip()
    regiao_especifica = str(data.get("regiao_especifica") or "").strip()

    if (
        not cliente
        or not tamanho
        or not estilo
        or not area_tatuada
        or not regiao_especifica
        or ("sombreamento" not in data)
        or ("colorido" not in data)
        or sombreamento is None
        or colorido is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Todos os campos sao obrigatorios e devem ser válidos.",
        )

    await tattooController.create_tattoo(cliente, tamanho, sombreamento, colorido, estilo, area_tatuada, regiao_especifica)
    raise HTTPException(status_code=201, detail="Tatuagem criada com sucesso.")