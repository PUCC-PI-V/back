from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import uvicorn
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from routes.iaRoutes import iaRoute
from routes.loginRoute import loginRoute
from database.prisma.client import connect_db, disconnect_db
from utils.installModels.autoInstallModels import autoInstallModels

app = FastAPI()
app.state.limiter = iaRoute.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
load_dotenv()

# Get the port from environment variable, default to 8000 if not set
PORT = int(os.getenv("PORT", 8000))


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Simple route to check if the backend is running
@app.get("/status")
async def root():
    return {"message": f"Backend is running, listening on port {PORT}"}


app.include_router(iaRoute.router, prefix="/ia")
app.include_router(loginRoute.router, prefix="/admin")


@app.on_event("startup")
async def startup():
    await connect_db()


@app.on_event("shutdown")
async def shutdown():
    await disconnect_db()


if __name__ == "__main__":
    autoInstallModels()
    uvicorn.run(app, host="127.0.0.1", port=PORT)
