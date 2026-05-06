from fastapi import FastAPI
from dotenv import load_dotenv
import os
import uvicorn
from routes.iaRoutes import iaRoute

app = FastAPI()
load_dotenv()
# Get the port from environment variable, default to 8000 if not set
PORT = int(os.getenv("PORT", 8000))

# Simple route to check if the backend is running
@app.get("/status")
async def root():
    return {"message": f"Backend is running, listening on port {PORT}"}


app.include_router(iaRoute.router, prefix="/ia")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
