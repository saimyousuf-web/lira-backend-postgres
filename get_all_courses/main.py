from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from dependencies.auth import require_permission
from core.db import get_db_session
from get_all_courses.schema import CourseResponse
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
        stmt = (
            select(
                Course.id.label("id"),
                Course.nm.label("nm"),
                Course.dsc.label("dsc"),
                Course.crtat.label("crtat"),
            )
            .order_by(Course.crtat.desc())
        )

        result = await db.execute(stmt)
        courses = result.mappings().all()

        
        return [
            CourseResponse(
                cid=course["id"],
                cnm=course["nm"],
                desc=course["dsc"],
                crtat=course["crtat"],
            )
            for course in courses
        ]
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid node id")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")