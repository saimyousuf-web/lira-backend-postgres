import re
import logging
import select
import boto3
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config import settings
from models.module import Module
from models.course_module import CourseModule

from workers.processor import process_document_internal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3", region_name=settings.REGION)



async def process_document(
    db: AsyncSession,
    userId: str,
    organization_id: str,
    course_id: str,
    module_id: str,
    s3_key: str,
    file_name: str,
    file_type: str,
    course_name: str,
    approval_sts: bool,
    description: str,
):
    try:
        # 1) Create / update module in Postgres
        module = await db.execute(select(Module).filter(Module.id == module_id))
        module = module.scalar_one_or_none()

        if not module:
            module = Module(
                id=module_id,
                nm=file_name,
                ty=file_type,
                loc=s3_key,
                isapr=approval_sts,
                sts="PENDING",
                isvec=False,
                crtby=userId,
                updby=userId,
            )
            db.add(module)
        else:
            module.nm = file_name
            module.ty = file_type
            module.loc = s3_key
            module.isapr = approval_sts
            module.updby = userId
            module.updat = datetime.utcnow()

        # 2) Create course-module mapping

        result = await db.execute(
            select(CourseModule).where(
                CourseModule.cid == course_id,
                CourseModule.moid == module_id,
            )
        )

        existing_link = result.scalar_one_or_none()

        if not existing_link:
                db.add(
                CourseModule(
                    cid=course_id,
                    moid=module_id,
                    crtby=userId,
                    updby=userId,
                )
            )

        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Postgres error: {str(e)}")

    safe_doc_id = re.sub(r"[^A-Za-z0-9_-]", "-", str(module_id))

    payload = {
        "organization_id": organization_id,
        "course_id": course_id,
        "module_id": safe_doc_id,
        "s3_key": s3_key,
        "file_name": file_name,
        "file_type": file_type,
        "course_name": course_name,
        "description": description,
        "db": db,
    }

    await process_document_internal(payload)

    return {
        "status": "queued",
        "courseId": course_id,
        "moduleId": module_id,
    }


async def process_document_raw(
    db: AsyncSession,
    userId: str,
    organization_id: str,
    course_id: str,
    module_id: str,
    file_bytes: bytes,
    file_name: str,
    file_type: str,
    course_name: str,
    approval_sts: bool,
    description: str,
):
    """Process a raw uploaded file (bytes) without reading from S3.
    This creates/updates DB entries and then invokes the internal processor
    with `file_bytes` so no S3 read or S3 event is required.
    """
    print(f"Processing raw file: {file_name} for course {course_id}, module {module_id}")
    try:
        # 1) Create / update module in Postgres
        module = await db.execute(select(Module).filter(Module.id == module_id))
        module = module.scalar_one_or_none()

        if not module:
            module = Module(
                id=module_id,
                nm=file_name,
                ty=file_type,
                loc=None,
                isapr=approval_sts,
                sts="PENDING",
                isvec=False,
                crtby=userId,
                updby=userId,
            )
            db.add(module)
            print(f"Module created/updated: {module_id} - {file_name}")
        
        else:
            module.nm = file_name
            module.ty = file_type
            module.loc = None
            module.isapr = approval_sts
            module.updby = userId
            module.updat = datetime.utcnow()
            print(f"Module updated: {module_id} - {file_name}")

        # 2) Create course-module mapping

        result = await db.execute(
            select(CourseModule).where(
                CourseModule.cid == course_id,
                CourseModule.moid == module_id,
            
            )
        )

        existing_link = result.scalar_one_or_none()
        print(f"Existing course-module link: {existing_link}")

        if not existing_link:
                db.add(
                CourseModule(
                    cid=course_id,
                    moid=module_id,
                    crtby=userId,
                    updby=userId,
                )
            )

        await db.commit()

    except Exception as e:
        print(f"Error during Postgres operations: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Postgres error: {str(e)}")

    safe_doc_id = re.sub(r"[^A-Za-z0-9_-]", "-", str(module_id))

    payload = {
        "organization_id": organization_id,
        "course_id": course_id,
        "module_id": safe_doc_id,
        "file_bytes": file_bytes,
        "file_name": file_name,
        "file_type": file_type,
        "course_name": course_name,
        "description": description,
        "db": db,
    }

# Wrap this too — it can fail and currently has no safety net
    try:
        await process_document_internal(payload)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

    return {
        "status": "queued",
        "courseId": str(course_id),   # str() to avoid UUID serialization issues
        "moduleId": str(module_id),
    }