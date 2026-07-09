from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db_session
from core.id_cypher import decrypt_id
from models.nodes import Func
from get_all_functions_by_dept.schema import (
    FunctionResponse,
    GetAllFunctionsByDeptResponse,
)

router = APIRouter()


@router.get(
    "/{orgid}/{dept_id}",
    response_model=GetAllFunctionsByDeptResponse,
)
async def get_all_functions_by_dept(
    orgid_enc: str = Path(..., alias="orgid"),
    dept_id_enc: str = Path(..., alias="dept_id"),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        orgid = decrypt_id(orgid_enc)
        dept_id = decrypt_id(dept_id_enc)

        result = await db.execute(
            select(Func).where(
                Func.orgid == orgid,
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

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")