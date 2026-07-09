from fastapi import APIRouter, Path, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.main import get_current_user
from core.config import settings
from core.db import get_db_session
from core.id_cypher import decrypt_id
from models.nodes import Org
from get_logo.schema import OrganizationDetailsResponse

router = APIRouter()


@router.get(
    "/{org_id}",
    response_model=OrganizationDetailsResponse,
)
async def get_org_id(
    org_id_enc: str = Path(..., alias="org_id", description="Organization ID"),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    try:
        org_id = decrypt_id(org_id_enc)

        org = await db.scalar(
            select(Org).where(Org.ndid == org_id)
        )

        if not org:
            raise HTTPException(
                status_code=404,
                detail="Organization not found"
            )

        logo_url = f"{settings.S3_BASE_FILE_URL}/{org.logo_path}"
        favicon_url = f"{settings.S3_BASE_FILE_URL}/{org.favicon_path}"

        return OrganizationDetailsResponse(
            name=org.nm,
            logo=logo_url,
            favicon=favicon_url,
            title=org.title,
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid organization ID: {e}"
        )