from fastapi import APIRouter, HTTPException, Depends, Path, Body
from pydantic import BaseModel
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

class ApprovalUpdate(BaseModel):
    isapr: bool

@router.patch("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/{cid}/{moid}")
async def update_module_approval(
    payload: ApprovalUpdate = Body(...),
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    cid: str = Path(...),
    moid: str = Path(...),
    # user=Depends(require_permission("update:module")),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        node_id = uuid.UUID(ctx_ndid)
        course_id = uuid.UUID(cid)
        module_id = uuid.UUID(moid)

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
                detail="Node not found",
            )

        # Validate module belongs to course
        stmt = (
            select(Module)
            .join(
                CourseModule,
                CourseModule.moid == Module.id,
            )
            .where(
                Module.id == module_id,
                CourseModule.cid == course_id,
            )
        )

        result = await db.execute(stmt)
        module = result.scalar_one_or_none()

        if not module:
            raise HTTPException(
                status_code=404,
                detail="Module not found for this course",
            )

        # Update approval status
        module.isapr = payload.isapr

        await db.commit()
        await db.refresh(module)

        return {
            "moid": str(module.id),
            "isapr": module.isapr,
            "message": "Module approval updated successfully",
        }

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid UUID format",
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}",
        )