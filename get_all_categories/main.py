from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.db import get_db_session
from models.category import Category

router = APIRouter()

@router.get("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}")
async def get_all_categories(
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        stmt = (
            select(
                Category.id,
                Category.nm,
                Category.dsc,
                Category.crtat,
            )
            .order_by(Category.crtat.desc())
        )

        result = await db.execute(stmt)
        rows = result.all()

        items = [
            {
                "catid": row.id,
                "catnm": row.nm,
                "desc": row.dsc,
                "crtat": row.crtat,
            }
            for row in rows
        ]

        return items

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")