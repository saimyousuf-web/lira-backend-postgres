from fastapi import APIRouter, Body, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from update_category.schema import UpdateCategoryRequest
from core.db import get_db_session
from models.category import Category
# from dependencies.auth import require_permission

router = APIRouter()


@router.put("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/category/{category_id}", response_model=dict)
async def update_category(
    category_id: str = Path(...),
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    payload: UpdateCategoryRequest = Body(...),
    # auth_data=Depends(require_permission("update_category")),
    db: AsyncSession = Depends(get_db_session),
):
    user_id = uuid.UUID("6418e458-50a1-70fe-9d3e-b52f5d2df57c")  # placeholder for testing
    # user_id = uuid.UUID(auth_data["userId"])

    try:
        cat_id = uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category_id format")

    category = await db.scalar(
        select(Category).where(Category.id == cat_id)
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if payload.nm:
        category.nm = payload.nm.strip()
    if payload.dsc is not None:
        category.dsc = payload.dsc

    category.updby = user_id

    await db.commit()
    await db.refresh(category)

    return {
        "status": "success",
        "status_code": 200,
        "message": "Category updated successfully",
        "data": {
            "category_id": str(category.id),
            "nm": category.nm,
            "dsc": category.dsc,
            "updat": category.updat.isoformat() if category.updat else None,
        },
    }
