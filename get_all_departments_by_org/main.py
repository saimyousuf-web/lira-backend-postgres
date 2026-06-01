from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.db import get_db_session
from models.nodes import Dept
from get_all_departments_by_org.schema import DepartmentResponse, GetAllDepartmentsByOrgResponse

router = APIRouter()


@router.get("/{orgid}", response_model=GetAllDepartmentsByOrgResponse)
async def get_all_departments_by_org(orgid: UUID,db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(
        select(Dept).where(Dept.orgid == orgid)
    )
    depts = result.scalars().all()


    return GetAllDepartmentsByOrgResponse(
        status_code=200,
        success=True,
        departments=[
            DepartmentResponse(
                ndid=dept.ndid,
                prtndid=dept.prtndid,
                name=dept.nm
            )
            for dept in depts
        ]
    )