from fastapi import APIRouter, Body, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import uuid
from dependencies.auth import require_permission
from core.db import get_db_session
from models.category import Category

router = APIRouter()

@router.post("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}", response_model=dict)
async def create_category(
    payload: dict = Body(...),
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    # auth_data=Depends(require_permission("create_organization")),
    db: AsyncSession = Depends(get_db_session),
):
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")  # placeholder for testing
    # user_id = uuid.UUID(auth_data["userId"])
    try:
        category = Category(
            id=uuid.uuid4(),
            name=payload["name"].strip(),
            description=payload.get("description"),
            created_by=user_id,
            updated_by=user_id,
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
            "name": category.name,
        }
    }