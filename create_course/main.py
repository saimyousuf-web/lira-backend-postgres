from fastapi import APIRouter, Body, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select
import uuid

from core.db import get_db_session
from models.course import Course
from models.nodes import Node, NodeType
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
        node_id = uuid.UUID(ctx_ndid)

        stmt = (
            select(Node)
            .join(Node.node_type)
            .where(
                Node.id == node_id,
                NodeType.type == ctx_ndty,
            )
        )
        result = await db.execute(stmt)
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        course = Course(
            name=payload.name.strip(),
            description=payload.description,
            created_by=user_id,
            updated_by=user_id,
        )

        db.add(course)
        await db.flush()  # generates course.id

        course_node = CourseNode(
            course_id=course.id,
            node_id=node.id,
            created_by=user_id,
            updated_by=user_id,
        )

        db.add(course_node)
        await db.commit()
        await db.refresh(course)

        return {
            "status": "success",
            "status_code": 201,
            "message": "Course created successfully",
            "data": {
                "course_id": str(course.id),
                "name": course.name,
                "node_id": str(node.id),
            },
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