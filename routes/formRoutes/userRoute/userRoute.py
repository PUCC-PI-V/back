from fastapi import APIRouter, Request
from controllers.userControllers import userController

router = APIRouter()

@router.post("/create_user")
async def create_user(request: Request):
    data = await request.json()
    nome = str(data.get("nome") or "").strip()
    data_nasc = str(data.get("data_nasc") or "").strip()
    cpf = str(data.get("cpf") or "").strip()
    telefone = str(data.get("telefone") or "").strip()
    email = str(data.get("email") or "").strip()
    password = str(data.get("password") or "")

    if not nome or not data_nasc or not cpf or not telefone or not email or not password:
        return {"error": False, "message": "Todos os campos sao obrigatorios."}

    existing_user = await userController.get_user_by_email(email)
    if existing_user is not None:
        return {"success": False, "message": "Email ja cadastrado."}

    await userController.create_user(nome, data_nasc, cpf, telefone, email, password)
    return {"success": True, "message": "Usuario criado com sucesso."}