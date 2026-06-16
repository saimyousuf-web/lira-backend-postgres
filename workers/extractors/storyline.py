"""
Storyline ZIP extractor — Postgres version.

Migrated from DynamoDB (chunks_table.put_item + file_table.update_item)
to async SQLAlchemy, following the exact same pattern as chunk_and_embed_docx.

Only the persistence layer changed; all Storyline-specific logic
(ZIP detection, slide parsing, image filtering, chunking) is untouched.
"""

import io
import json
import logging
import os
import re
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from zipfile import ZipFile

import boto3
from PIL import Image
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client.models import PointStruct

from workers.extractors.pdf import _split_text_with_images
from models.chunks import Chunk
from models.course_module import CourseModule
from models.module import Module
from workers.vector import generate_embedding, normalize_vector
from workers.qdrnt_vector import get_qdrant_client, QDRANT_COLLECTION

logger = logging.getLogger(__name__)

REGION = os.environ.get("REGION")
s3 = boto3.client("s3", region_name=REGION)

SUPPORTED_EXT       = {".png", ".jpg", ".jpeg", ".webp"}
VAL_MIN_KB          = 60
VAL_MAX_KB          = 550
BG_MIN_KB           = 150
IMAGE_ID_REGEX      = re.compile(r"\[IMAGE_ID:\s*(.*?)\]")


# ===========================================================================
# Entry points
# ===========================================================================

async def handle_zip_file(
    organization_id: str,
    course_id: str,
    course_name: str,
    document_id: str,
    file_bytes: bytes,
    S3_BUCKET: str,
    db: AsyncSession,
):
    print("ZIP detected, determining authoring software...")
    tool = detect_authoring_tool_from_zip(file_bytes)

    if tool != "storyline":
        return {"status": "error", "message": f"Unsupported ZIP type: {tool}"}

    print("Storyline ZIP detected — processing + embedding...")

    try:
        await process_storyline_internal(
            file_bytes=file_bytes,
            course_id=course_id,
            course_name=course_name,
            org_id=organization_id,
            document_id=document_id,
            S3_BUCKET=S3_BUCKET,
            db=db,
        )
        return {"status": "success", "message": "Storyline processed and embedded successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print("Storyline processing failed:", str(e))
        return {"status": "error", "message": "Storyline processing failed"}


async def process_storyline_internal(
    file_bytes: bytes,
    course_id: str,
    course_name: str,
    org_id: str,
    document_id: str,
    S3_BUCKET: str,
    db: AsyncSession,
):
    print("Processing Storyline SCORM ZIP from file bytes...")

    # Hardcoded acting user — replace with real auth dependency
    user_id = uuid.UUID("6418e458-50a1-70fe-9d3e-b52f5d2df57c")

    try:
        course_uuid = uuid.UUID(course_id)
        module_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # ------------------------------------------------------------------
    # 1. Validate Module + CourseModule (same guard as docx/pdf)
    # ------------------------------------------------------------------
    try:
        mod_result = await db.execute(select(Module).where(Module.id == module_uuid))
        module: Module | None = mod_result.scalar_one_or_none()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

        cm_result = await db.execute(
            select(CourseModule).where(
                CourseModule.cid == course_uuid,
                CourseModule.moid == module_uuid,
            )
        )
        course_module: CourseModule | None = cm_result.scalar_one_or_none()
        if not course_module:
            raise HTTPException(status_code=404, detail="CourseModule association not found")

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    # ------------------------------------------------------------------
    # 2 – 4.  Parse ZIP, extract slides, upload images  (unchanged logic)
    # ------------------------------------------------------------------
    with ZipFile(BytesIO(file_bytes)) as z:

        # --- Extract Storyline JSON ---
        DATA_JS_PATH = "html5/data/js/data.js"
        data_js_text = z.read(DATA_JS_PATH).decode("utf-8", errors="ignore")

        match = re.search(
            r"globalProvideData\('data',\s*'(.+?)'\);",
            data_js_text,
            re.DOTALL,
        )
        if not match:
            raise ValueError("Could not extract Storyline JSON")

        data = json.loads(
            match.group(1).encode("utf-8").decode("unicode_escape")
        )

        # --- Map slides ---
        slide_short_to_title: dict[str, str] = {}
        slide_short_to_file:  dict[str, str] = {}

        for scene in data.get("scenes", []):
            if scene.get("isMessageScene"):
                continue
            for slide in scene.get("slides", []):
                sid   = slide.get("id")
                title = slide.get("title", "").strip()
                js    = slide.get("html5url")
                if sid and title and js:
                    slide_short_to_title[sid] = title
                    slide_short_to_file[sid]  = js

        slides = []
        for ref in data.get("slideMap", {}).get("slideRefs", []):
            full_id = ref.get("id", "")
            if "." not in full_id:
                continue
            short = full_id.split(".")[-1]
            if short in slide_short_to_title:
                slides.append({
                    "title":    slide_short_to_title[short],
                    "slide_js": slide_short_to_file[short],
                })

        print(f"Prepared {len(slides)} slides")

        # --- Images ---
        valuable_images = extract_valuable_images_from_storyline_zip(z)
        storyline_images_to_s3(z, valuable_images, course_id, org_id, document_id, S3_BUCKET)

        # --- Build normalised pages ---
        storyline_pages = []
        for idx, slide in enumerate(slides):
            content = extract_multimodal_content_from_slide_js(z, slide["slide_js"])

            slide_json = [{"slide": idx + 1, "title": slide["title"], "content": content}]
            slide_json = filter_storyline_json_by_valuable_images(slide_json, valuable_images)
            slide_json[0]["content"] = normalize_to_on_screen_content(slide_json[0]["content"])

            page_content = []
            for block in slide_json[0]["content"]:
                normalized_images = []
                for img in block.get("image", []):
                    if isinstance(img, dict):
                        normalized_images.append(
                            img.get("key") or img.get("src") or img.get("filename", "")
                        )
                    elif isinstance(img, str):
                        normalized_images.append(img)
                page_content.append({
                    "text":  block.get("text", ""),
                    "image": normalized_images,
                })

            storyline_pages.append({
                "page":        idx + 1,
                "slide_title": slide["title"],
                "content":     page_content,
            })

        # --- Chunk ---
        all_pages = []
        for page_obj in storyline_pages:
            chunked_content = []
            for item in page_obj["content"]:
                chunked_content.extend(
                    _split_text_with_images(
                        item["text"], item["image"], max_chars=1200, overlap=150
                    )
                )
            all_pages.append({
                "page":        page_obj["page"],
                "slide_title": page_obj.get("slide_title", ""),
                "content":     chunked_content,
            })

        print("Storyline chunking completed.")

        # ------------------------------------------------------------------
        # 5. Embed → Qdrant + accumulate Chunk rows  (replaces DynamoDB)
        # ------------------------------------------------------------------
        failed_count = 0

        for page_obj in all_pages:
            page_num    = page_obj["page"]
            slide_title = page_obj.get("slide_title", "")

            for chunk in page_obj["content"]:
                chunk_id: uuid.UUID = chunk["chunk_id"]
                text:     str       = chunk.get("text", "")
                img_keys: list[str] = [
                    os.path.basename(k) for k in chunk.get("image", [])
                ]

                status, _ = _embed_and_upsert_qdrant(
                    chunk_id=chunk_id,
                    text=text,
                    org_id=org_id,
                    course_id=course_uuid,
                    course_name=course_name,
                    module_id=module_uuid,
                    page_num=page_num,
                    slide_title=slide_title,
                )

                if status == "failed":
                    failed_count += 1
                    continue       # skip DB insert for unembedded chunks

                chunk_row = Chunk(
                    id=chunk_id,
                    moid=module_uuid,
                    cid=course_uuid,
                    txt=text,
                    # img_keys=img_keys or None,   # uncomment after adding column
                    crtby=user_id,
                    updby=user_id,
                )
                db.add(chunk_row)

        # ------------------------------------------------------------------
        # 6. Mark Module + CourseModule processed  (replaces update_item ×2)
        # ------------------------------------------------------------------
        now = datetime.now(timezone.utc)

        module.isvec = True
        module.sts   = "APPROVED"
        module.updat = now
        module.updby = user_id

        course_module.updat = now
        course_module.updby = user_id

        # ------------------------------------------------------------------
        # 7. Single commit
        # ------------------------------------------------------------------
        try:
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Integrity error: {e.orig}")
        except SQLAlchemyError as e:
            await db.rollback()
            try:
                module.sts   = "failed"
                module.updat = now
                await db.commit()
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

        total = sum(len(p["content"]) for p in all_pages)
        print(f"Storyline ingestion complete. {total - failed_count}/{total} chunks saved.")

        return {
            "status":         "success",
            "status_code":    200,
            "message":        "Storyline chunked and embedded successfully",
            "chunks_total":   total,
            "chunks_saved":   total - failed_count,
            "chunks_failed":  failed_count,
        }


# ===========================================================================
# Qdrant embed helper
# ===========================================================================

def _embed_and_upsert_qdrant(
    chunk_id:    uuid.UUID,
    text:        str,
    org_id:      str,
    course_id:   uuid.UUID,
    course_name: str,
    module_id:   uuid.UUID,
    page_num:    int,
    slide_title: str = "",
) -> tuple[str, int]:
    try:
        embedding = generate_embedding(text)

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
                        "chunk_index":     1,
                        "slide_title":     slide_title,
                    },
                )
            ],
        )
        return "completed", len(embedding)

    except Exception as e:
        print(f"Embedding failed for chunk {chunk_id}: {e}")
        return "failed", 0


# ===========================================================================
# Storyline-specific helpers  (logic unchanged from original)
# ===========================================================================

def detect_authoring_tool_from_zip(file_bytes: bytes) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            z.extractall(temp_dir)
        if detect_storyline(temp_dir):
            return "storyline"
        if detect_rise(temp_dir):
            return "rise"
        return "unknown"


def detect_storyline(root: str) -> bool:
    return (
        os.path.exists(os.path.join(root, "story.html"))
        and os.path.isdir(os.path.join(root, "story_content"))
    )


def detect_rise(root: str) -> bool:
    if os.path.isdir(os.path.join(root, "scormcontent")):
        return True
    return (
        os.path.exists(os.path.join(root, "index.html"))
        and os.path.isdir(os.path.join(root, "assets"))
        and os.path.exists(os.path.join(root, "data.json"))
    )


def extract_multimodal_content_from_slide_js(z: ZipFile, js_path: str) -> list[dict]:
    seen_texts  = set()
    seen_images = set()

    try:
        content = z.read(js_path).decode("utf-8", errors="ignore")
    except Exception:
        return []

    match = re.search(
        r"globalProvideData\('slide',\s*'(.+?)'\);", content, re.DOTALL
    )
    if not match:
        return []

    try:
        slide = json.loads(
            match.group(1).encode("utf-8").decode("unicode_escape")
        )
    except Exception:
        return []

    multimodal: list[dict] = []

    def emit_text(text: str):
        text = text.strip()
        if not text or text in seen_texts:
            return
        seen_texts.add(text)
        if re.match(r"^(Rectangle|Oval|Line|BG|Menu|Stage)$", text, re.I):
            return
        if re.match(r"^%[A-Z0-9_]+%$", text):
            return
        multimodal.append({"type": "text", "text": text})

    def emit_image(url: str):
        filename = os.path.basename(url)
        zip_path = f"mobile/{filename}"
        if zip_path in seen_images:
            return
        seen_images.add(zip_path)
        multimodal.append({"type": "text", "text": f"[IMAGE_ID: {zip_path}]"})

    def extract_from_object(obj: dict):
        for tdata in obj.get("textLib", []):
            for block in tdata.get("vartext", {}).get("blocks", []):
                spans = []
                for span in block.get("spans", []):
                    txt = span.get("text", "")
                    if txt:
                        txt = (
                            txt.replace("\r", " ")
                               .replace("\n", " ")
                               .replace("\u00c2", "")
                               .replace("\u00a0", " ")
                               .strip()
                        )
                        spans.append(txt)
                if spans:
                    emit_text(" ".join(spans))

        for img in obj.get("imagelib", []):
            url = img.get("url")
            if url:
                emit_image(url)

    for layer in slide.get("slideLayers", []):
        for obj in layer.get("objects", []):
            extract_from_object(obj)
            if obj.get("kind") == "stategroup":
                for state_obj in obj.get("objects", []):
                    extract_from_object(state_obj)

    return multimodal


def extract_valuable_images_from_storyline_zip(zip_file: ZipFile) -> list[str]:
    valuable: list[str] = []

    for name in zip_file.namelist():
        if not name.startswith("mobile/"):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext not in SUPPORTED_EXT:
            continue
        try:
            image_bytes = zip_file.read(name)
        except KeyError:
            continue

        size_kb = len(image_bytes) / 1024
        dims    = _get_image_dimensions(image_bytes)
        if not dims:
            continue
        w, h = dims

        if is_background(w, h, size_kb):
            continue
        if is_valuable_content(w, h, size_kb) and size_kb <= VAL_MAX_KB:
            valuable.append(os.path.basename(name))

    print(f"Valuable images: {len(valuable)}")
    return valuable


def is_background(w: int, h: int, size_kb: float) -> bool:
    if h == 0:
        return False
    ratio = round(w / h, 2)
    return w >= 960 and 1.70 <= ratio <= 1.85 and size_kb >= BG_MIN_KB


def is_valuable_content(w: int, h: int, size_kb: float) -> bool:
    return size_kb >= VAL_MIN_KB and (w >= 300 or h >= 300)


def _get_image_dimensions(image_bytes: bytes) -> tuple[int, int] | None:
    try:
        img = Image.open(BytesIO(image_bytes))
        return img.width, img.height
    except Exception:
        return None


def filter_storyline_json_by_valuable_images(
    storyline_json: list[dict],
    valuable_60_550_filenames: list[str],
) -> list[dict]:
    valuable_set = set(valuable_60_550_filenames)
    for slide in storyline_json:
        filtered = []
        for block in slide.get("content", []):
            if block.get("type") != "text":
                continue
            text  = block.get("text", "")
            match = IMAGE_ID_REGEX.match(text)
            if match:
                if os.path.basename(match.group(1)) in valuable_set:
                    filtered.append(block)
            else:
                filtered.append(block)
        slide["content"] = filtered
    return storyline_json


def normalize_to_on_screen_content(multimodal: list[dict]) -> list[dict]:
    normalized:      list[dict] = []
    current_text:    list[str]  = []
    current_images:  list[str]  = []

    for block in multimodal:
        text  = block.get("text", "").strip()
        match = IMAGE_ID_REGEX.match(text)
        if match:
            if current_text:
                normalized.append({
                    "text":  " ".join(current_text).strip(),
                    "image": current_images,
                })
                current_text   = []
                current_images = []
            current_images.append(os.path.basename(match.group(1)))
        else:
            if text:
                current_text.append(text)

    if current_text or current_images:
        normalized.append({
            "text":  " ".join(current_text).strip(),
            "image": current_images,
        })

    return normalized


def storyline_images_to_s3(
    zip_file:        ZipFile,
    valuable_images: list[str],
    course_id:       str,
    org_id:          str,
    document_id:     str,
    S3_BUCKET:       str,
) -> str:
    s3_prefix = f"material/{org_id}/zip/{course_id}/{document_id}/images/"
    print("Uploading Storyline valuable images to S3...")

    saved = skipped = 0
    for filename in valuable_images:
        zip_path = f"mobile/{filename}"
        try:
            img_bytes = zip_file.read(zip_path)
        except KeyError:
            skipped += 1
            continue

        ext          = os.path.splitext(filename)[1].replace(".", "").lower()
        content_type = f"image/{'jpeg' if ext == 'jpg' else ext}"

        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_prefix + filename,
                Body=img_bytes,
                ContentType=content_type,
            )
            saved += 1
        except Exception as e:
            print(f"Failed to upload {filename}: {e}")
            skipped += 1

    print(f"Uploaded {saved} images, skipped {skipped}")
    return s3_prefix