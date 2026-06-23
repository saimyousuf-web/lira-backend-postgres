from fastapi import APIRouter, Body, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select
import uuid

from core.db import get_db_session
from models.course import Course
from models.cat_course import CatCourse
from models.nodes import Node
from models.course_node import CourseNode
from create_course.schema import CreateCourseRequest

router = APIRouter()

@router.post("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}", response_model=dict)
async def create_course(
    payload: CreateCourseRequest = Body(...),
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    user_id = uuid.UUID("6418e458-50a1-70fe-9d3e-b52f5d2df57c")

    try:
        node_ids = [uuid.UUID(node_id) for node_id in payload.node_ids]

        stmt = (
            select(Node)
            .where(
                Node.id.in_(node_ids)
            )
        )
        result = await db.execute(stmt)
        nodes = result.scalars().all()

        if len(nodes) != len(node_ids):
            raise HTTPException(
            status_code=404,
            detail="One or more node IDs do not exist"
            )

        course = Course(
            nm=payload.name.strip(),
            dsc=payload.description,
            crtby=user_id,
            updby=user_id,
        )

        db.add(course)
        await db.flush()  # generates course.id

        for node in nodes:
            course_node = CourseNode(
                cid=course.id,
                ndid=node.id,
                crtby=user_id,
                updby=user_id,
            )
            db.add(course_node)

        cat_course = CatCourse(
            catid=payload.category_id,
            cid=course.id,
            crtby=user_id,
            updby=user_id,
        )

        db.add(cat_course)

        await db.commit()
        await db.refresh(course)

        return {
            "status": "success",
            "status_code": 201,
            "message": "Course created successfully"
        }

    except ValueError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e.orig}")

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")