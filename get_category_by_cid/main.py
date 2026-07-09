from typing import List

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.main import get_current_user
from core.db import get_db_session
from core.id_cypher import decrypt_id
from get_category_by_cid.schema import CategoryResponse
from models.cat_course import CatCourse
from models.category import Category

router = APIRouter()


@router.get(
    "/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/{cid}",
    response_model=List[CategoryResponse],
)
async def get_category_by_cid(
    ctx_orgid: str = Path(..., description="Organization ID"),
    ctx_ndid: str = Path(..., description="Node ID"),
    ctx_ndty: str = Path(..., description="Node Type"),
    cid: str = Path(..., description="Course ID"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        # node_id = decrypt_id(ctx_ndid)
        # node_id is currently not used 
        course_id = decrypt_id(cid)

        

        response = await db.execute(
            select(Category.id, Category.nm)
            .join(CatCourse, CatCourse.catid == Category.id)
            .where(CatCourse.cid == course_id)
        )

        categories = response.all()

        if not categories:
            raise HTTPException(
                status_code=404,
                detail="No categories found for this course",
            )

        return [
            CategoryResponse(
                catid=category.id,
                catnm=category.nm,
            )
            for category in categories
        ]

    except InvalidToken:
        raise HTTPException(
            status_code=400,
            detail="Invalid encrypted ID",
        )