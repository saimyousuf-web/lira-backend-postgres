from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select
import uuid

from core.db import get_db_session
from dependencies.auth import require_permission

from models.course import Course
from models.category import Category
from models.cat_course import CatCourse
from create_catcourse.schema import CreateCatCourseRequest
router = APIRouter()


@router.post("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}", response_model=dict)
async def create_catcourse(
    payload: CreateCatCourseRequest = Body(...),
    # user=Depends(require_permission("create:catcourse")),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        user_id = uuid.UUID("6418e458-50a1-70fe-9d3e-b52f5d2df57c")

        course_id = uuid.UUID(payload.course_id)
        category_id = uuid.UUID(payload.category_id)

        # Verify course exists
        result = await db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = result.scalar_one_or_none()

        if not course:
            raise HTTPException(
                status_code=404,
                detail="Course not found",
            )

        # Verify category exists
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found",
            )

        mapping = CatCourse(
            cid=course_id,
            catid=category_id,
            crtby=user_id,
            updby=user_id,
        )

        db.add(mapping)

        await db.commit()

        return {
            "status": "success",
            "status_code": 201,
            "message": "Course mapped to category successfully",
        }

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid UUID format",
        )

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Course already mapped to category",
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}",
        )