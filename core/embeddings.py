"""
Local text-embedding client backed by sentence-transformers
(default model: BAAI/bge-large-en-v1.5, 1024-dim).

Replaces the previous AWS Bedrock Titan (amazon.titan-embed-text-v2) embeddings.
Output dimension (1024) matches Titan v2, so the Qdrant collection size is unchanged.
Existing vectors must still be re-indexed because the embedding space differs.
"""
from threading import Lock

from core.config import settings

EMBED_DIM = 1024

_model = None
_lock = Lock()


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
    """Return a 1024-dim embedding for `text` (un-normalized)."""
    model = _get_model()
    return model.encode(text, normalize_embeddings=False).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of strings (un-normalized)."""
    if not texts:
        return []
    model = _get_model()
    return [v.tolist() for v in model.encode(texts, normalize_embeddings=False)]
