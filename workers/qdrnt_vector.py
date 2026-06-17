# vector.py
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np
from core.config import settings
QDRANT_URL        = settings.QDRANT_URL     
QDRANT_API_KEY    = settings.QDRANT_API_KEY   
QDRANT_COLLECTION = settings.QDRANT_COLLECTION
VECTOR_DIM        = 1024  

# Singleton client
_qdrant_client: QdrantClient | None = None

def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return _qdrant_client


def ensure_collection_exists():
    """
    Create the collection if it doesn't already exist.
    Call once at app startup (e.g. in lifespan or main.py).
    """
    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
    ensure_payload_indexes()


def ensure_payload_indexes():
    """
    Qdrant requires a payload index on any field used in a filter. We filter by
    course_id at query time, so it must be indexed (keyword). Idempotent.
    """
    client = get_qdrant_client()
    try:
        client.create_payload_index(
            collection_name=QDRANT_COLLECTION,
            field_name="course_id",
            field_schema="keyword",
        )
    except Exception:
        # Index already exists (or collection just created it) — safe to ignore.
        pass


def normalize_vector(vec: list[float]) -> list[float]:
    """L2-normalise so cosine similarity == dot product."""
    arr = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(arr)
    return (arr / norm).tolist() if norm > 0 else arr.tolist()