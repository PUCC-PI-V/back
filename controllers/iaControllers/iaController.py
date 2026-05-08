from fastapi import HTTPException, Request
import torch
from services.iaServices import iaService

async def prompt_index(request: Request):
    
    data = await request.json()
    question = str(data.get("input") or data.get("prompt") or "").strip()
    
    try:
        tokenizar, model, collection = iaService.load_resources()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if torch.cuda.is_available():
        print("Modelo carregado em GPU.")
    else:
        print("Modelo carregado em CPU. As respostas podem demorar.")
    
    try:
        if not question:
            raise HTTPException(status_code=400, detail="A pergunta nao pode ser vazia.")
        
        answer = iaService.rag_chain(question, tokenizar, model, collection)

        return {"answer": answer}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))