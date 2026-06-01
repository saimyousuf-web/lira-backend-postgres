from fastapi import APIRouter, Body, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import uuid
from create_category.schema import CreateCategoryRequest
from dependencies.auth import require_permission
from core.db import get_db_session
from models.category import Category

router = APIRouter()

@router.post("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}", response_model=dict)
async def create_category(
    payload: CreateCategoryRequest = Body(...),
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    # auth_data=Depends(require_permission("create_organization")),
    db: AsyncSession = Depends(get_db_session),
):
    user_id = uuid.UUID("6418e458-50a1-70fe-9d3e-b52f5d2df57c")  # placeholder for testing
    # user_id = uuid.UUID(auth_data["userId"])
    try:
        category = Category(
            nm=payload.name.strip(),
            dsc=payload.description,
            crtby=user_id,
            updby=user_id,
        )       
        db.add(category)
        
        await db.flush()
        await db.commit()


    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return {
        "status": "success",
        "status_code": 201,
        "message": "Category created successfully",
        "data": {
            "category_id": str(category.id),
            "name": category.nm,
            "description": category.dsc,
        }
    }