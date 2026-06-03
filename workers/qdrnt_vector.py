# vector.py
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

QDRANT_URL        = os.environ.get("QDRANT_URL")      
QDRANT_API_KEY    = os.environ.get("QDRANT_API_KEY")   
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "lira_vector")
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


def normalize_vector(vec: list[float]) -> list[float]:
    """L2-normalise so cosine similarity == dot product."""
    arr = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(arr)
    return (arr / norm).tolist() if norm > 0 else arr.tolist()