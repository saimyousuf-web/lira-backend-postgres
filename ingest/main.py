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

    module_id = str(uuid.uuid4())
    # ctx_orgid = payload.get('orgid') 


    return await process_document(
        db,
        userId=uuid.UUID("6418e458-50a1-70fe-9d3e-b52f5d2df57c"),
        organization_id=uuid.UUID("476a5b85-3c35-4c05-8647-2dd79babd835"),
        course_id=uuid.UUID("1dc223b7-ee5e-4f83-9cd6-03c4bf9a9c13"),
        module_id=uuid.UUID(module_id),
        s3_key="be7401db-7bcb-40ce-97ab-07a8eb7b6c58/18603901-92d6-45f1-9b96-860b8717a774/20260318T063031_1 APM_Product_Security_Engineering_Manual_Extended.docx",
        file_name="1 APM_Product_Security_Engineering_Manual_Extended.docx",
        file_type="docx",
        course_name="APM Product Security Engineering Manual",
        approval_sts=True,
        description="APM Product Security Engineering Manual"
    )
