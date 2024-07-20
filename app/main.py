from fastapi import FastAPI
from api.routes.router import api_router
from core.logging import setup_logging
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield
    print("shutdown event")

app = FastAPI(lifespan=lifespan)


app.include_router(api_router, prefix="/api")