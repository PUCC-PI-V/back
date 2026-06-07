
from fastapi import APIRouter, Request, HTTPException
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
        raise HTTPException(
            status_code=400,
            detail="Todos os campos sao obrigatorios."
        )

    existing_user = await userController.get_user_by_email(email)
    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="Email ja cadastrado."
        )

    await userController.create_user(nome, data_nasc, cpf, telefone, email, password)
    raise HTTPException(status_code=201, detail="Usuario criado com sucesso.")