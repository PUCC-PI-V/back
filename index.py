from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database.conn import connect_db, disconnect_db
import os
import uvicorn
import asyncio
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from utils.installModels.autoInstallModels import autoInstallModels
from routes.iaRoutes import iaRoute
from routes.loginRoute import loginRoute
from routes.formRoutes.userRoute import userRoute
from routes.formRoutes.tattooRoute import tattooRoute
from utils.installModels.autoInstallModels import autoInstallModels

app = FastAPI()
app.state.limiter = iaRoute.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
load_dotenv()

# Get the port from environment variable, default to 8000 if not set
PORT = int(os.getenv("PORT", 8000))


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8080", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Simple route to check if the backend is running
@app.get("/status")
async def root():
    return {"message": f"Backend is running on port {PORT}"}


app.include_router(iaRoute.router, prefix="/ia")
app.include_router(loginRoute.router, prefix="/admin")
app.include_router(userRoute.router, prefix="/user")
app.include_router(tattooRoute.router, prefix="/tattoo")

@app.on_event("startup")
async def startup():
    await connect_db()
    await asyncio.to_thread(autoInstallModels)


@app.on_event("shutdown")
async def shutdown():
    await disconnect_db()


if __name__ == "__main__":
    # Models/downloads run in the startup event now; don't call the installer synchronously.
    uvicorn.run(app, host="127.0.0.1", port=PORT)
