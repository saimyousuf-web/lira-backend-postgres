from fastapi import FastAPI
from shared.middleware import cors_middleware
from sqlalchemy.ext.asyncio import AsyncEngine

from core.db import Base, engine
from create_departments.main import router as create_departments_router
from health import router as health_router


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def create_app() -> FastAPI:
    app = FastAPI()
    cors_middleware(app)

    @app.on_event("startup")
    async def on_startup():
        await init_db()

    app.include_router(create_departments_router, prefix="/create-departments")
    app.include_router(health_router, prefix="/health")

    return app


app = create_app()