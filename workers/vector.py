import numpy as np
import boto3
from pinecone import Pinecone
import os

REGION = os.environ.get("REGION")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")

# ---------- AWS CLIENTS (SAFE) ----------
# boto3 clients are lazy internally, OK to define

dynamodb = boto3.resource("dynamodb", region_name=REGION)
bedrock_client = boto3.client("bedrock-runtime", region_name=REGION)

# ---------- PINECONE (LAZY INIT) ----------
_pc = None
_pinecone_index = None


def get_pinecone_index():
    """
    Lazily initialize Pinecone index.
    Safe for reloads, threads, and Lambda cold starts.
    """
    global _pc, _pinecone_index

    if _pinecone_index is None:
        if not PINECONE_API_KEY:
            raise RuntimeError("PINECONE_API_KEY not set")

        _pc = Pinecone(api_key=PINECONE_API_KEY)
        _pinecone_index = _pc.Index("lira-vector-index")

    return _pinecone_index


def normalize_vector(vec):
    arr = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(arr)
    return (arr / norm).tolist() if norm else arr.tolist()