from fastapi import APIRouter, Depends, HTTPException
from dependencies.auth import require_permission
from ingest.handlers import process_document
import uuid
from core.db import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("")
async def process_uploaded_file(
    # user=Depends(require_permission("upload_content"))
    db: AsyncSession = Depends(get_db_session)
    ):

    module_id = "affba56a-71a3-4dd5-bd7d-74068544da1c" 
    # ctx_orgid = payload.get('orgid') 


    return await process_document(
        db,
        userId=uuid.UUID("6418e458-50a1-70fe-9d3e-b52f5d2df57c"),
        organization_id=uuid.UUID("476a5b85-3c35-4c05-8647-2dd79babd839"),
        course_id=uuid.UUID("385a2e04-5f45-436f-98bc-e592f82c451f"),
        module_id=uuid.UUID(module_id),
        s3_key="476a5b85-3c35-4c05-8647-2dd79babd839/385a2e04-5f45-436f-98bc-e592f82c451f/20260724T130233_Module 12 -  Clinical investigations, SSCP, and PRRC.zip",
        file_name="Module 12 -  Clinical investigations, SSCP, and PRRC.zip",
        file_type="zip",
        course_name="Implementation of the Medical Device Regulation 2017/745 (MDR) for CE Marking On-demand Training",
        approval_sts=True,
        description=" Implementation of the Medical Device Regulation 2017/745 (MDR) for CE Marking On-demand Training"
    )