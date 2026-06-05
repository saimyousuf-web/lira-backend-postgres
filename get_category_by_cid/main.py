from typing import List
from uuid import UUID
from fastapi import APIRouter,Path,Depends,HTTPException
from core.db import get_db_session
from dependencies.auth import get_current_user
from get_category_by_cid.schema import CategoryResponse
from models.cat_course import CatCourse
from models.category import Category
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
router = APIRouter()

@router.get('/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/{cid}')
async def get_category_by_cid(
    ctx_orgid: UUID = Path(..., description="Organization ID"),
    ctx_ndid: UUID = Path(..., description="Node ID"),
    ctx_ndty: str = Path(..., description="Node Type"),
    cid: UUID = Path(..., description="Course ID"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    response_model=List[CategoryResponse]
):
    # add depencey if needed to check permission view categories)
    response = await db.execute(
        select(Category.id,Category.nm).join(CatCourse,CatCourse.catid == Category.id)
        .where(CatCourse.cid == cid)
        )
    categories = response.all()
    if not categories:
        raise HTTPException(status_code=404,detail="No categories found for this course")
    
    return [
        CategoryResponse(
            catid=category.id,
            catnm=category.nm
        )

        for category in categories
    ]
    





