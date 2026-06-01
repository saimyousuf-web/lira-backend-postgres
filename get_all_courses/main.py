from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from dependencies.auth import require_permission
from core.db import get_db_session
from models.course import Course
from models.course_node import CourseNode

router = APIRouter()


@router.get("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}")
async def get_all_courses(
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    # auth_data=Depends(require_permission("view_all_courses")),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        node_id = uuid.UUID(ctx_ndid)

        stmt = (
            select(
                Course.id.label("cid"),
                Course.name.label("cnm"),
                Course.description.label("dec"),
                Course.created_at.label("crtat"),
            )
            .join(CourseNode, CourseNode.cid == Course.id)
            .where(CourseNode.ndid == node_id)
            .order_by(Course.crtat.desc())
        )

        result = await db.execute(stmt)
        courses = result.mappings().all()

        return {
            "status": "success",
            "status_code": 200,
            "data": [dict(course) for course in courses],
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid node id")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")