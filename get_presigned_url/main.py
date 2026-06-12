from datetime import datetime, UTC
from fastapi import APIRouter ,Depends, HTTPException
import boto3
from core.config import settings
from dependencies.auth import require_permissions

router = APIRouter()

s3_client = boto3.client(
    "s3",
    region_name=settings.REGION
)
S3_BUCKET=settings.S3_BUCKET_NAME

@router.post("")
def get_presigned_url(payload: dict,
user=Depends(require_permissions('create_presigned_url'))
):
    
    module_name = payload.get("module_name")
    course_id = payload.get("course_id")
    content_type = payload.get("content_type")
    ctx_orgid = payload.get('orgid') 


    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    key = f"{ctx_orgid}/{course_id}/{ts}_{module_name}"
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": key,
                "ContentType": content_type
            },
            ExpiresIn=300,
        )

        return {"url": url, "s3_key": key}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



