from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import uuid

from core.db import get_db_session
from dependencies.auth import require_permission

from models.module import Module
from models.course_module import CourseModule
from models.nodes import Node, NodeType

router = APIRouter()


@router.get("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/{cid}")
async def get_module_by_cid(
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    cid: str = Path(...),
    # user=Depends(require_permission("read:course")),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        node_id = uuid.UUID(ctx_ndid)
        course_id = uuid.UUID(cid)

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

        # Fetch modules linked to course
        stmt = (
            select(Module)
            .join(
                CourseModule,
                CourseModule.moid == Module.id,
            )
            .where(
                CourseModule.cid == course_id
            )
        )

        result = await db.execute(stmt)
        modules = result.scalars().all()

        data = [
            {
                "moid": module.id,
                "monm": module.nm,
                "moty": module.ty,
                "crtat": module.crtat,
                "sts": module.sts,
                "isapr": module.isapr,
                "s3loc": module.loc,
            }
            for module in modules
        ]

        return data

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