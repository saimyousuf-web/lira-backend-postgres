from fastapi import APIRouter, HTTPException, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

from core.db import get_db_session
from auth.main import get_current_user
from models.cat_course import CatCourse
from models.course import Course
from models.nodes import Node, NodeType

import logging


router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/")
async def get_courses_by_category(
    catid: UUID = Query(None, description="Filter by Category ID"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        result = await db.execute(
            select(Course)
            .join(CatCourse, CatCourse.cid == Course.id)
            .where(CatCourse.catid == catid)
        )

        courses = result.scalars().all()

        if not courses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No courses found for the given category.",
            )

        return [
            {
                "id": course.id,
                "name": course.nm,
                "description": course.dsc,
                "status": course.sts,
            }
            for course in courses
        ]

    except HTTPException:
        raise

    except SQLAlchemyError as ex:
        logger.exception("Database error while fetching courses by category.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while fetching courses.",
        ) from ex

    except Exception as ex:
        logger.exception("Unexpected error while fetching courses by category.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from ex
        