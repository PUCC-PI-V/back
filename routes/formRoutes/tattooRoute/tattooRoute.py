from fastapi import APIRouter, Request, HTTPException
from controllers.tattooControllers import tattooController
from json import JSONDecodeError


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
            detail="Todos os campos sao obrigatorios e devem ser válidos.")

    await tattooController.create_tattoo(cliente, tamanho, sombreamento, colorido, estilo, area_tatuada, regiao_especifica)
    raise HTTPException(status_code=201, detail="Tatuagem criada com sucesso.")


"""@router.patch("/add_estim_value/{id_tatuagem}")
async def add_estim_value(id_tatuagem: int, request: Request):
    data = await request.json()
    valor_estimado = data.get("valor_estimado")
    if valor_estimado is None:
        raise HTTPException(status_code=400, detail="O campo 'valor_estimado' é obrigatório.")
    try:
        valor_estimado = float(valor_estimado)
    except ValueError:
        raise HTTPException(status_code=400, detail="O campo 'valor_estimado' deve ser um número.")
    
    await tattooController.add_estim_value(id_tatuagem, valor_estimado)
    raise HTTPException(status_code=200, detail="Valor estimado adicionado com sucesso.")"""
    
@router.patch("/add_estim_value/{id_tatuagem}")
async def add_estim_value(id_tatuagem: int, request: Request):
    raw = await request.body()
    if not raw:
        q = request.query_params.get("valor_estimado")
        if q is None:
            raise HTTPException(status_code=400, detail="Request body is empty. Send JSON: {\"valor_estimado\":1300}")
        valor_estimado = q
    else:
        try:
            data = await request.json()
        except (JSONDecodeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid JSON body")
        valor_estimado = data.get("valor_estimado")

    if valor_estimado is None:
        raise HTTPException(status_code=400, detail="O campo 'valor_estimado' é obrigatório.")

    try:
        valor_estimado = float(valor_estimado)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="O campo 'valor_estimado' deve ser um número.")

    await tattooController.add_estim_value(id_tatuagem, valor_estimado)
    raise HTTPException(status_code=200, detail="Valor estimado adicionado com sucesso.")