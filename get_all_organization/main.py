from fastapi import APIRouter, Depends
from models.nodes import Org
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db_session
from get_all_organization.schema import GetAllOrganizationsResponse, Organization

router = APIRouter()


@router.get("",response_model=GetAllOrganizationsResponse)
async def get_organizations(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Org))
    orgs = result.scalars().all()

    organizations = [
        Organization(
            name=org.nm,
            ndid=org.ndid
        )
        for org in orgs
    ]

    return GetAllOrganizationsResponse(
        status_code=200,
        status="success",
        count=len(organizations),
        organizations=organizations
    )