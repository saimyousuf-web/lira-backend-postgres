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


@router.get("/{orgid}/{dept_id}", response_model=GetAllFunctionsByDeptResponse)
async def get_all_functions_by_dept(
    orgid : UUID,
    dept_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Func).where(
            Func.orgid  == orgid,
            Func.prtndid == dept_id,
            Func.isact == True, 
        )
    )
    funcs = result.scalars().all()

    return GetAllFunctionsByDeptResponse(
        status_code=200,
        success=True,
        functions=[
            FunctionResponse(
                ndid=func.ndid,
                prtndid=func.prtndid,
                name=func.nm,
            )
            for func in funcs
        ],
    )