"""
One-time re-index of all existing chunks into Qdrant using the local
gte-large-en-v1.5 embeddings (replaces the old Titan vectors).

Why: chunk text already lives in Postgres (`chunks.txt`), and the RAG query path only
needs `chunk_id` + `course_id` from the vector store (everything else is hydrated from
Postgres via `get_chunk_context`). So we can rebuild the vector store purely from Postgres
without re-extracting source files.

Run from the backend root:

    python -m scripts.reindex_embeddings

Idempotent: points are upserted by chunk id, so re-running overwrites rather than duplicates.
"""
import asyncio
import sys

# On Windows, asyncio.run() defaults to ProactorEventLoop, which the async psycopg
# driver cannot use. Switch to the selector loop before any async DB work.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select
from qdrant_client.models import PointStruct, VectorParams, Distance

from core.db import AsyncSessionLocal
from core.embeddings import embed_texts
from models.chunks import Chunk
from models.course import Course
from workers.qdrnt_vector import (
    get_qdrant_client,
    QDRANT_COLLECTION,
    VECTOR_DIM,
    normalize_vector,
)

BATCH_SIZE = 100


async def _fetch_chunks():
    """Return rows of (chunk_id, course_id, course_name, module_id, text)."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                Chunk.id,
                Chunk.cid,
                Course.nm,
                Chunk.moid,
                Chunk.txt,
            ).join(Course, Chunk.cid == Course.id)
        )
        return result.all()


def _reindex(rows) -> int:
    client = get_qdrant_client()
    total = 0

    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start:start + BATCH_SIZE]
        texts = [row[4] or "" for row in batch]

        vectors = embed_texts(texts)

        points = []
        for row, vector in zip(batch, vectors):
            chunk_id, course_id, course_name, module_id, _ = row
            points.append(
                PointStruct(
                    id=str(chunk_id),
                    vector=normalize_vector(vector),
                    payload={
                        "chunk_id": str(chunk_id),
                        "course_id": str(course_id),
                        "course_name": course_name,
                        "module_id": str(module_id) if module_id else None,
                    },
                )
            )

        client.upsert(collection_name=QDRANT_COLLECTION, points=points)
        total += len(points)
        print(f"  upserted {total}/{len(rows)}")

    return total


def _recreate_collection():
    """
    Drop and recreate the collection with a single unnamed 1024-dim cosine vector.

    All app code (extractors, rag_service query, this script) uses an unnamed vector;
    if the existing collection was created with named vectors, upserts fail with
    "Not existing vector name error". We rebuild from Postgres anyway, so a clean
    recreate guarantees the schema matches every read/write path.
    """
    client = get_qdrant_client()
    if client.collection_exists(QDRANT_COLLECTION):
        client.delete_collection(QDRANT_COLLECTION)
    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
    )


async def main():
    print(f"Recreating Qdrant collection '{QDRANT_COLLECTION}' (unnamed 1024-dim, cosine)...")
    _recreate_collection()

    print("Fetching chunks from Postgres...")
    rows = await _fetch_chunks()
    print(f"Found {len(rows)} chunks to re-index.")

    if not rows:
        print("Nothing to do.")
        return

    total = _reindex(rows)
    count = get_qdrant_client().count(QDRANT_COLLECTION).count
    print(f"Done. Re-indexed {total} chunks. Qdrant now holds {count} points.")


if __name__ == "__main__":
    asyncio.run(main())
