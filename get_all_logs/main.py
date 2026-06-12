from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from core.db import get_db_session
from models.logs import Log
from models.module import Module
from models.course import Course
from models.user import User
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
    cid = uuid.UUID(course_id)
    
    try:
        
        old_mod = Module.__table__.alias("old_mod")
        new_mod = Module.__table__.alias("new_mod")
        logs_t = Log.__table__
        courses_t = Course.__table__
        users_t = User.__table__

        stmt = (
            select(
                courses_t.c.nm.label("course"),
                old_mod.c.nm.label("old_module"),
                new_mod.c.nm.label("new_module"),
                users_t.c.first_name.label("updby_fnm"),
                users_t.c.last_name.label("updby_lnm"),
                logs_t.c.updat.label("updated_at"),
            )
            .select_from(logs_t)
            .outerjoin(courses_t, logs_t.c.cid == courses_t.c.id)
            .outerjoin(old_mod, logs_t.c.oldmoid == old_mod.c.id)
            .outerjoin(new_mod, logs_t.c.newmoid == new_mod.c.id)
            .outerjoin(users_t, logs_t.c.updby == users_t.c.id)
            .where(logs_t.c.cid == cid)
            .order_by(logs_t.c.updat.desc())
        )

        result = await db.execute(stmt)
        rows = result.mappings().all()

        return [
            {
                "course_name": row["course"],
                "old_module_name": row["old_module"],
                "new_module_name": row["new_module"],
                "updated_by_name": f"{row['updby_fnm'] or ''} {row['updby_lnm'] or ''}".strip() or None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")
