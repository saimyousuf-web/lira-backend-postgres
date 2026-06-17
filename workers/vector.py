import numpy as np
import boto3
import os

from core.embeddings import embed_text

REGION = os.environ.get("REGION")

# ---------- AWS CLIENTS (SAFE) ----------
# boto3 clients are lazy internally, OK to define

dynamodb = boto3.resource("dynamodb", region_name=REGION)


def generate_embedding(text: str) -> list[float]:
    """Generate a 1024-dim embedding for `text` using the local bge model."""
    return embed_text(text)


def normalize_vector(vec):
    arr = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(arr)
    return (arr / norm).tolist() if norm else arr.tolist()