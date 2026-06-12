from fastapi import APIRouter
import boto3
from urllib.parse import urlparse

s3_client = boto3.client(
    "s3",
    region_name="us-east-1"
)

router = APIRouter()

def get_presigned_url(s3_url: str, expiry: int = 3600) -> str:
    """Convert plain S3 URL to presigned URL"""
    parsed = urlparse(s3_url)
    # Extract bucket and key from URL
    # https://lira-ingestion-bucket-us.s3.us-east-1.amazonaws.com/material/...
    bucket = parsed.netloc.split(".")[0]  # lira-ingestion-bucket-us
    key = parsed.path.lstrip("/")         # material/476a5b85.../image.jpeg

    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiry
    )

    return presigned_url

@router.get("/presign")
async def presign_url(url: str):
    presigned = get_presigned_url(url)
    return { "presigned_url": presigned }