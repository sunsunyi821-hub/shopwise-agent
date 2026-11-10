import hashlib
import logging
import math
from typing import Protocol

from openai import AsyncOpenAI

from app.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    name: str
    model: str

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAICompatibleEmbeddingProvider:
    """Works with Qwen, OpenAI, or any /embeddings-compatible endpoint."""

    name = "openai"

    def __init__(self, settings: Settings) -> None:
        api_key = settings.resolved_embedding_api_key
        if not api_key:
            raise ValueError(
                "EMBEDDING_API_KEY / DASHSCOPE_API_KEY is empty; semantic retrieval disabled."
            )
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.embedding_base_url,
            timeout=60.0,
        )
        self.model = settings.embedding_model
        self.batch_size = max(1, settings.embedding_batch_size)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            response = await self.client.embeddings.create(
                model=self.model,
                input=batch,
            )
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors.extend([list(item.embedding) for item in ordered])
        return vectors


class MockEmbeddingProvider:
    """Deterministic character-hash vectors for tests / offline demos.

    This is *not* a semantic model. It only gives us stable vectors so we can
    test the retrieval plumbing without an API key.
    """

    name = "mock"

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions
        self.model = f"mock-char-{dimensions}"

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for char in text:
            digest = hashlib.md5(char.encode("utf-8")).hexdigest()
            index = int(digest[:8], 16) % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def create_embedding_provider(settings: Settings) -> EmbeddingProvider | None:
    if settings.embedding_provider == "disabled":
        return None
    if settings.embedding_provider == "mock":
        return MockEmbeddingProvider()
    try:
        return OpenAICompatibleEmbeddingProvider(settings)
    except ValueError as exc:
        logger.warning("Embedding provider unavailable: %s", exc)
        return None
