"""main処理"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.routes.router import api_router
from core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> any:
    """FastAPIの開始と終了のライフサイクルをフックしている

    :app FastAPIのライブラリ
    """
    setup_logging()
    yield
    print("shutdown event")


app = FastAPI(lifespan=lifespan)


app.include_router(api_router, prefix="/api")
