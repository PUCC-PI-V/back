from fastapi import HTTPException, Request

async def prompt_index(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        return {"response": prompt+" received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))