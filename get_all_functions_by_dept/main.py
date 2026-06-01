from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.db import get_db_session
from models.nodes import Func
from get_all_functions_by_dept.schema import (
    FunctionResponse,
    GetAllFunctionsByDeptResponse
)

router = APIRouter()


@router.get("/{org_id}/{dept_id}", response_model=GetAllFunctionsByDeptResponse)
async def get_all_functions_by_dept(
    org_id: UUID,
    dept_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Func).where(
            Func.org_id == org_id,
            Func.parent_id == dept_id,
            Func.is_active == True,  # or .is_(True)
        )
    )
    funcs = result.scalars().all()

    return GetAllFunctionsByDeptResponse(
        status_code=200,
        success=True,
        functions=[
            FunctionResponse(
                ndid=func.node_id,
                prtndid=func.parent_id,
                name=func.name,
            )
            for func in funcs
        ],
    )