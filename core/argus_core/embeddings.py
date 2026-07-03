"""Local embeddings with bge-small-en-v1.5 via fastembed (ONNX, no torch).

Zero embedding cost; the model is downloaded once at first use and cached.
fastembed is synchronous — async callers should wrap in `asyncio.to_thread`.
"""
from fastembed import TextEmbedding

from argus_core.config import settings

_model: TextEmbedding | None = None

# bge family: queries should be prefixed for retrieval, passages should not.
_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=settings.embedding_model)
    return _model


def embed_passages(texts: list[str]) -> list[list[float]]:
    return [list(map(float, v)) for v in _get_model().embed(texts, batch_size=32)]


def embed_query(text: str) -> list[float]:
    return embed_passages([_QUERY_PREFIX + text])[0]
