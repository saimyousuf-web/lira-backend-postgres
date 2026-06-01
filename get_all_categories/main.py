from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from sqlalchemy import select
from dependencies.auth import require_permission
from core.db import get_db_session
from models.category import Category  # adjust import to your actual model path

router = APIRouter()


@router.get("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}")
async def get_all_categories(
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    # user=Depends(require_permission('get_all_categories')),
    db: Session = Depends(get_db_session),
):

    try:
        stmt = (
            select(
                Category.catid,
                Category.catnm,
                Category.desc,
                Category.crtat,
            )
            .where(Category.orgid == ctx_orgid)
            .order_by(Category.crtat.desc())
        )

        result = db.execute(stmt).all()

        items = [
            {
                "catid": row.catid,
                "catnm": row.catnm,
                "desc": row.desc,
                "crtat": row.crtat,
            }
            for row in result
        ]

        return items

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")