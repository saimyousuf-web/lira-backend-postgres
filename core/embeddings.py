"""
Text-embedding client with two interchangeable 1024-dim providers:

  - "bge"   → local BAAI/bge-large-en-v1.5 via sentence-transformers
  - "titan" → AWS Bedrock amazon.titan-embed-text-v2

Both output 1024 dims, so the Qdrant collection size is identical across providers
(only the vector space differs). The provider is selectable per role for the
embedding A/B/C evaluation:
  - embed_docs()  → settings.INGEST_EMBED_PROVIDER  (ingestion / re-index)
  - embed_query() → settings.QUERY_EMBED_PROVIDER   (chat query time)
"""
from threading import Lock

from core.config import settings

EMBED_DIM = 1024

_model = None
_lock = Lock()
_bedrock = None


# ---------------- bge (local sentence-transformers) ----------------
def _get_model():
    """Lazily load the SentenceTransformer model as a process-wide singleton."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                # Imported lazily so the heavy torch import only happens on first use.
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_text(text: str) -> list[float]:
    """Return a 1024-dim bge embedding for `text` (un-normalized)."""
    model = _get_model()
    vector = model.encode(text, normalize_embeddings=False)
    return vector.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch bge-embed a list of strings (un-normalized)."""
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=False)
    return [v.tolist() for v in vectors]


# ---------------- titan (AWS Bedrock) ----------------
def _get_bedrock():
    global _bedrock
    if _bedrock is None:
        with _lock:
            if _bedrock is None:
                import boto3

                _bedrock = boto3.client("bedrock-runtime", region_name=settings.REGION)
    return _bedrock


def embed_titan(text: str) -> list[float]:
    """Return a 1024-dim Titan embedding for `text` (un-normalized)."""
    import json

    resp = _get_bedrock().invoke_model(
        modelId=settings.TITAN_EMBED_MODEL,
        contentType="application/json",
        body=json.dumps({"inputText": text}),
    )
    body = json.loads(resp["body"].read())
    return body.get("embedding", [])


def embed_titan_batch(texts: list[str]) -> list[list[float]]:
    """Batch Titan-embed (Titan has no batch API, so loop)."""
    return [embed_titan(t) for t in texts]


# ---------------- provider dispatch ----------------
def _embed_one(provider: str, text: str) -> list[float]:
    return embed_titan(text) if provider == "titan" else embed_text(text)


def _embed_many(provider: str, texts: list[str]) -> list[list[float]]:
    return embed_titan_batch(texts) if provider == "titan" else embed_texts(texts)


def embed_query(text: str) -> list[float]:
    """Embed a query using the configured QUERY_EMBED_PROVIDER."""
    return _embed_one(settings.QUERY_EMBED_PROVIDER, text)


def embed_docs(texts: list[str]) -> list[list[float]]:
    """Batch-embed documents using the configured INGEST_EMBED_PROVIDER."""
    return _embed_many(settings.INGEST_EMBED_PROVIDER, texts)
