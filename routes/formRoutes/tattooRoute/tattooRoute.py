from fastapi import APIRouter, Request
from controllers.tattooControllers import tattooController

router = APIRouter()

@router.post("/create_tattoo")
async def create_tattoo(request: Request):
    data = await request.json()
    name = str(data.get("name") or "").strip()
    description = str(data.get("description") or "").strip()
    price = data.get("price")

    if not name or not description or price is None:
        return {"success": False, "message": "Todos os campos sao obrigatorios."}

    try:
        price = float(price)
    except ValueError:
        return {"success": False, "message": "Preco deve ser um numero valido."}

    await tattooController.create_tattoo(name, description, price)
    return {"success": True, "message": "Tatuagem criada com sucesso."}