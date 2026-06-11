from uuid import UUID

from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db_session
from models.nodes import Dept, Func

router = APIRouter()


@router.get("/{orgid}")
async def get_all_dept_func_by_org(
    orgid: UUID = Path(...),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        dept_stmt = (
            select(
                Dept.ndid,
                Dept.nm,
            )
            .where(
                Dept.prtndid == orgid,
                Dept.isact.is_(True),
            )
        )

        dept_result = await db.execute(dept_stmt)
        depts = dept_result.all()

        dept_ids = [row.ndid for row in depts]

        funcs = []

        if dept_ids:
            func_stmt = (
                select(
                    Func.ndid,
                    Func.nm,
                    Func.prtndid,
                )
                .where(
                    Func.prtndid.in_(dept_ids),
                    Func.isact.is_(True),
                )
            )

            func_result = await db.execute(func_stmt)
            funcs = func_result.all()

        return {
            "orgid": str(orgid),
            "departments": [
                {
                    "deptid": str(dept.ndid),
                    "name": dept.nm,
                }
                for dept in depts
            ],
            "functions": [
                {
                    "funcid": str(func.ndid),
                    "name": func.nm,
                    "deptid": str(func.prtndid),
                }
                for func in funcs
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch hierarchy: {str(e)}",
        )