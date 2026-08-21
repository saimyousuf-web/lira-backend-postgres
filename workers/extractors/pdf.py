"""
PDF chunking + embedding endpoint.
Migrated from DynamoDB / raw function → FastAPI + PostgreSQL (async SQLAlchemy).

Pre-requisites
--------------
1.  Add an optional `img_keys` column to the Chunk model (see NOTE below).
2.  `_fetch_pdf_bytes(location)` must be implemented for your storage layer.

NOTE: Chunk model addition required
------------------------------------
    img_keys = Column(
        ARRAY(Text),        # from sqlalchemy.dialects.postgresql import ARRAY
        nullable=True,
    )
Add the matching Alembic migration before running this endpoint.
"""

import json
import re
import uuid
from datetime import datetime, timezone
import boto3
import fitz  # PyMuPDF
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.db import get_db_session
from models.chunks import Chunk
from models.course_module import CourseModule
from models.module import Module
from workers.vector import bedrock_client,  normalize_vector
from qdrant_client.models import PointStruct
import os
from workers.qdrnt_vector import QDRANT_COLLECTION, QDRANT_COLLECTION, get_qdrant_client

REGION = os.environ.get("REGION")
S3_BUCKET = os.environ.get("S3_BUCKET")

s3 = boto3.client("s3", region_name=REGION)
textract = boto3.client("textract", region_name=REGION)

router = APIRouter()

# ---------------------------------------------------------------------------
# Image quality filters  (tune as needed)
# ---------------------------------------------------------------------------
MIN_WIDTH = 229
MIN_HEIGHT = 180
MIN_AREA = MIN_WIDTH * MIN_HEIGHT
MIN_BYTES = 8_999
MAX_BYTES = 1_000_000
MIN_BYTES_PER_PIXEL = 0.02


# ===========================================================================
# Pure helpers  (no I/O — easy to unit-test)
# ===========================================================================

def _group_images_with_previous_text(content: list[dict]) -> list[dict]:
    """
    Merge image items into the preceding text block so each chunk carries
    both its text and any immediately-following images.
    """
    result: list[dict] = []
    current: dict | None = None

    for item in content:
        t = item["text"].strip()
        imgs = item["image"]
        img_txts = item.get("image_texts", [])

        if not imgs:                            # text-only item
            if t:
                if current is None or current["image"]:
                    if current:
                        result.append(current)
                    current = {"text": t, "image": []}
                else:
                    current["text"] += "\n" + t
        else:                                   # image (+ optional OCR) item
            if current is None:
                current = {"text": "", "image": []}
            current["image"].extend(imgs)
            for img_txt in img_txts:
                if img_txt:
                    current["text"] += "\n " + img_txt

    if current:
        result.append(current)

    return result


def _split_text_with_images(
    text: str,
    images: list[str],
    max_chars: int = 1200,
    overlap: int = 150,
) -> list[dict]:
    """
    Sliding-window text split.  Images are attached to the *first* chunk only.
    Returns list of dicts with keys: chunk_id, text, image.
    """
    if not text:
        return [{"chunk_id": uuid.uuid4(), "text": "", "image": images}]

    chunks: list[dict] = []
    start = 0
    first = True

    while start < len(text):
        end = start + max_chars
        chunks.append({
            "chunk_id": uuid.uuid4(),
            "text": text[start:end].strip(),
            "image": images if first else [],
        })
        first = False
        start = end - overlap if overlap else end

    return chunks


# ===========================================================================
# S3 + Textract helpers
# ===========================================================================

def _upload_page_images(
    doc: fitz.Document,
    s3_prefix: str,
) -> int:
    """
    Extract qualifying images from every page and upload them to S3.
    Returns the total number of images saved.
    """
    total_saved = 0

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_xrefs = {
            info["xref"]
            for info in page.get_image_info(xrefs=True)
            if info.get("bbox")
        }
        saved_on_page = 0

        for xref in page_xrefs:
            try:
                base = doc.extract_image(xref)
                if not base or "image" not in base:
                    continue

                img_bytes = base["image"]
                ext = base.get("ext", "png").lower()
                w = base.get("width", 0)
                h = base.get("height", 0)
                size = len(img_bytes)
                area = w * h

                # Quality gate
                if (
                    w < MIN_WIDTH
                    or h < MIN_HEIGHT
                    or area < MIN_AREA
                    or size < MIN_BYTES
                    or size > MAX_BYTES
                    or (size / area) < MIN_BYTES_PER_PIXEL
                ):
                    continue

                saved_on_page += 1
                total_saved += 1
                bpp = size / area
                filename = (
                    f"page{page_index + 1}_img{saved_on_page}_"
                    f"{w}x{h}_{size // 1024}KB_bpp{bpp:.3f}.{ext}"
                )
                s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=s3_prefix + filename,
                    Body=img_bytes,
                    ContentType=f"image/{ext}",
                )

            except Exception as e:
                print(f"Image extraction / upload failed for xref {xref}: {e}")

    print(f"Uploaded {total_saved} images to S3 under {s3_prefix}")
    return total_saved


def _load_page_images_from_s3(s3_prefix: str) -> dict[int, list[dict]]:
    """
    List objects under *s3_prefix*, run Textract OCR on each, and return
    a mapping  {page_number: [{filename, text, s3_key}, ...]}.
    """
    page_images: dict[int, list[dict]] = {}
    pattern = re.compile(r"page(\d+)_", re.IGNORECASE)

    paginator = s3.get_paginator("list_objects_v2")
    for s3_page in paginator.paginate(Bucket=S3_BUCKET, Prefix=s3_prefix):
        for obj in s3_page.get("Contents") or []:
            key = obj["Key"]
            filename = key.split("/")[-1]
            match = pattern.match(filename)
            if not match:
                continue

            page_num = int(match.group(1))
            ocr_text = ""
            try:
                resp = textract.detect_document_text(
                    Document={"S3Object": {"Bucket": S3_BUCKET, "Name": key}}
                )
                ocr_text = "\n".join(
                    b.get("Text", "")
                    for b in resp.get("Blocks", [])
                    if b.get("BlockType") == "LINE" and b.get("Text")
                )
            except Exception as e:
                print(f"Textract OCR failed for {key}: {e}")

            page_images.setdefault(page_num, []).append(
                {"filename": filename, "text": ocr_text, "s3_key": key}
            )

    # Sort images within each page by filename for deterministic ordering
    for imgs in page_images.values():
        imgs.sort(key=lambda x: x["filename"])

    return page_images


def _build_all_page_chunks(
    doc: fitz.Document,
    page_images: dict[int, list[dict]],
) -> list[dict]:
    """
    For each PDF page: extract digital text, merge with OCR'd image text,
    split into overlapping chunks, and collect them with page metadata.

    Returns a flat list of chunk dicts:
        {chunk_id, text, image (list[str] of filenames), page_num}
    """
    flat_chunks: list[dict] = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_num = page_index + 1

        # --- Digital text blocks ---
        text_blocks: list[str] = []
        for b in page.get_text("dict")["blocks"]:
            if b["type"] == 0:
                text = ""
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        text += span.get("text", "")
                    text += "\n"
                text = text.strip()
                if text:
                    text_blocks.append(text)

        # --- Build content list: text items + image items ---
        content: list[dict] = [{"text": t, "image": []} for t in text_blocks]
        for img in page_images.get(page_num, []):
            content.append({
                "text": "",
                "image": [img],
                "image_texts": [img.get("text", "")],
            })

        # --- Group images under preceding text ---
        content = _group_images_with_previous_text(content)

        # --- Flatten image dicts → filename strings ---
        for item in content:
            item["image"] = [
                img["filename"] if isinstance(img, dict) else img
                for img in item.get("image", [])
            ]

        # --- Sliding-window split ---
        for item in content:
            for chunk in _split_text_with_images(item["text"], item["image"]):
                flat_chunks.append({**chunk, "page_num": page_num})

    return flat_chunks


def _embed_and_upsert(
    chunk_id: uuid.UUID,
    text: str,
    org_id: str,
    course_id: uuid.UUID,
    course_name: str,
    module_id: uuid.UUID,
    page_num: int,
) -> tuple[str, int]:
    """Embed one chunk and upsert into Pinecone. Returns (status, dim)."""
    try:
        response = bedrock_client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            contentType="application/json",
            body=json.dumps({"inputText": text}),
        )
        body = json.loads(response["body"].read())
        embedding = body.get("embedding")

        if not (isinstance(embedding, list) and len(embedding) == 1024):
            return "failed", 0
        
        normalized = normalize_vector(embedding)
        
        get_qdrant_client().upsert(
        collection_name=QDRANT_COLLECTION,
        points=[
            PointStruct(
                id=str(chunk_id),
                vector=normalized,
                payload={
                    "chunk_id":        str(chunk_id),
                    "organization_id": org_id,
                    "course_id":       str(course_id),
                    "course_name":     course_name,
                    "module_id":       str(module_id),
                    "slide_index":     page_num,
                },
            )
        ],
        )
        return "completed", len(embedding)

    except Exception as e:
        print(f"Embedding failed for chunk {chunk_id}: {e}")
        return "failed", 0


async def chunk_and_embed_pdf(
    file_bytes: bytes,
    ctx_moid: str,
    ctx_cid: str,
    ctx_orgid: str,
    course_name: str,
    db,
):
    """
    Extract, chunk, embed, and persist a PDF module.
    """
    # Hardcoded user — replace with real auth dependency
    user_id = uuid.UUID("6418e458-50a1-70fe-9d3e-b52f5d2df57c")

    try:
        course_id = ctx_cid
        module_id = ctx_moid
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format in path")

    # ------------------------------------------------------------------
    # 1. Validate Module + CourseModule
    # ------------------------------------------------------------------
    try:
        mod_result = await db.execute(select(Module).where(Module.id == module_id))
        module: Module | None = mod_result.scalar_one_or_none()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

        cm_result = await db.execute(
            select(CourseModule).where(
                CourseModule.cid == course_id,
                CourseModule.moid == module_id,
            )
        )
        course_module: CourseModule | None = cm_result.scalar_one_or_none()
        if not course_module:
            raise HTTPException(status_code=404, detail="CourseModule association not found")

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    # # ------------------------------------------------------------------
    # # 2. Fetch PDF bytes
    # # ------------------------------------------------------------------
    # try:
    #     pdf_bytes = _fetch_pdf_bytes(file_bytes)
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Failed to fetch PDF: {e}")

    # ------------------------------------------------------------------
    # 3. Extract images → S3 → Textract OCR
    # ------------------------------------------------------------------
    s3_prefix = (
        f"material/{ctx_orgid}/pdf/{ctx_cid}/{ctx_moid}/images/"
    )

    doc = fitz.open(stream=file_bytes, filetype="pdf")

    try:
        _upload_page_images(doc, s3_prefix)
        page_images = _load_page_images_from_s3(s3_prefix)
    except Exception as e:
        # Non-fatal: continue without images if S3/Textract fails
        print(f"Image pipeline failed (continuing without images): {e}")
        page_images = {}

    # ------------------------------------------------------------------
    # 4. Build chunks
    # ------------------------------------------------------------------
    flat_chunks = _build_all_page_chunks(doc, page_images)
    print("This is flat chunks:", flat_chunks)
    doc.close()

    print(f"Total chunks created from PDF: {len(flat_chunks)}")
    if not flat_chunks:
        raise HTTPException(status_code=422, detail="No content could be extracted from PDF")

    # ------------------------------------------------------------------
    # 5 + 6. Embed → Pinecone, persist Chunk rows
    # ------------------------------------------------------------------
    course_name = module.nm   # use real Course.nm if you join on it

    failed_count = 0
    for chunk_data in flat_chunks:
        chunk_id: uuid.UUID = chunk_data["chunk_id"]
        text: str = chunk_data["text"]
        img_keys: list[str] = chunk_data["image"]          # S3 filenames
        page_num: int = chunk_data["page_num"]

        print(f"Processing chunk: {chunk_id}")
        print(f"Chunk text: {text}")

        status, _ = _embed_and_upsert(
            chunk_id=chunk_id,
            text=text,
            org_id=ctx_orgid,
            course_id=course_id,
            course_name=course_name,
            module_id=module_id,
            page_num=page_num,
        )

        if status == "failed":
            failed_count += 1
            # Skip persisting a chunk whose vector is missing
            continue

        chunk_row = Chunk(
            id=chunk_id,
            moid=module_id,
            cid=course_id,
            txt=text,
            imgkeys=img_keys,
            crtby=user_id,
            updby=user_id,
            slideidx=page_num,
        )
        db.add(chunk_row)

    # ------------------------------------------------------------------
    # Mark Module + CourseModule as vectorised / processed
    # ------------------------------------------------------------------
    now = datetime.now(timezone.utc)

    module.isvec = True
    module.sts = "APPROVED"
    module.updat = now
    module.updby = user_id

    course_module.updat = now
    course_module.updby = user_id

    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Integrity error: {e.orig}")
    except SQLAlchemyError as e:
        await db.rollback()
        # Best-effort: mark module as failed
        try:
            module.sts = "FAILED"
            module.updat = now
            await db.commit()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    total = len(flat_chunks)
    saved = total - failed_count
    print(f"PDF chunking + embedding complete. {saved}/{total} chunks saved.")

    return {
        "status": "success",
        "status_code": 200,
        "message": "PDF chunked and embedded successfully",
        "chunks_total": total,
        "chunks_saved": saved,
        "chunks_failed": failed_count,
    }


# ---------------------------------------------------------------------------
# Storage stub — implement for your S3 / GCS / local setup
# ---------------------------------------------------------------------------

def _fetch_pdf_bytes(file_bytes: bytes):
    return fitz.open(stream=file_bytes, filetype="pdf")
