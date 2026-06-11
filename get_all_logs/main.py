from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from core.db import get_db_session
from models.module_update_log import ModuleUpdateLog
from models.nodes import Node
# from dependencies.auth import require_permission

router = APIRouter()


@router.get("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}/{course_id}")
async def get_logs_by_courseid(
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    course_id: str = Path(...),
    # auth_data=Depends(require_permission("get_all_logs")),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        node_id = uuid.UUID(ctx_ndid)
        cid = uuid.UUID(course_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    try:
        stmt = (
            select(
                ModuleUpdateLog.id,
                ModuleUpdateLog.moid,
                ModuleUpdateLog.action,
                ModuleUpdateLog.prev_sts,
                ModuleUpdateLog.new_sts,
                ModuleUpdateLog.crtby,
                ModuleUpdateLog.crtat,
            )
            .where(
                ModuleUpdateLog.cid == cid,
                ModuleUpdateLog.ndid == node_id,
            )
            .order_by(ModuleUpdateLog.crtat.desc())
        )

        result = await db.execute(stmt)
        rows = result.mappings().all()

        return [
            {
                "id": str(row["id"]),
                "moid": str(row["moid"]),
                "action": row["action"],
                "prev_sts": row["prev_sts"],
                "new_sts": row["new_sts"],
                "crtby": str(row["crtby"]) if row["crtby"] else None,
                "crtat": row["crtat"].isoformat() if row["crtat"] else None,
            }
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")
