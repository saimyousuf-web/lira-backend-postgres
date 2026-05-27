from fastapi import APIRouter
from sqlalchemy import text
from core.db import engine

router = APIRouter(tags=["Health Check"])

@router.get("/health")
async def health():

    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        return {
            "database": "connected"
        }

    except Exception as e:
        return {
            "database": "failed",
            "error": str(e)
        }