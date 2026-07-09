from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import uuid

from core.db import get_db_session
from models.course import Course
from models.cat_course import CatCourse
from models.course_node import CourseNode
from models.nodes import Node, NodeType
from dependencies.auth import require_permission

router = APIRouter()


@router.get("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/{catid}")
async def get_course_by_catid(
    ctx_orgid: str,
    ctx_ndid: str,
    ctx_ndty: str,
    catid: str,
    # user=Depends(require_permission("read:course")),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        node_id = uuid.UUID(ctx_ndid)
        category_id = uuid.UUID(catid)

        # Validate node
        stmt = (
            select(Node)
            .join(Node.ndty)
            .where(
                Node.id == node_id,
                NodeType.ty == ctx_ndty,
            )
        )

        result = await db.execute(stmt)
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(
                status_code=404,
                detail="Node not found"
            )

        # Get courses for category + node
        stmt = (
        select(
        Course.id,
        Course.nm,
        Course.dsc,
        Course.crtat,
        Course.updat
        )
            .join(CatCourse, CatCourse.cid == Course.id)
            # .join(CourseNode, CourseNode.cid == Course.id)
            .where(
                CatCourse.catid == category_id
                # CourseNode.ndid == node.id,
            )
        )

        result = await db.execute(stmt)
        courses = result.all()

        data = [
            {
                "cid": course.id,
                "cnm": course.nm,
                "desc": course.dsc,
                "crtat": course.crtat,
                "updat": course.updat,
            }
            for course in courses
        ]

        return {
            "status": "success",
            "status_code": 200,
            "data": data,
            "message": "Course retrieved successfully",
        }

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid UUID format"
        )

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}"
        )