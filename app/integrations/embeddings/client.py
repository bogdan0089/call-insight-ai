import hashlib
import math
import re
from typing import Protocol

import httpx

from app.core.config import settings

WORD_RE = re.compile(r"\w+", re.UNICODE)


class Embedder(Protocol):
    model_name: str
    dimensions: int

    async def embed(self, text: str) -> list[float]: ...


class FakeEmbedder:
    model_name = "fake-bow"

    def __init__(self, dimensions: int = 1024) -> None:
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions

        for word in WORD_RE.findall(text.lower()):
            digest = hashlib.blake2b(word.encode(), digest_size=8).digest()
            index = int.from_bytes(digest, "big") % self.dimensions
            vector[index] += 1.0

        return _normalize(vector)


class VoyageEmbedder:
    model_name = "voyage-3"
    dimensions = 1024

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient(
            base_url="https://api.voyageai.com/v1",
            headers={"Authorization": f"Bearer {settings.voyage_api_key}"},
            timeout=settings.llm_timeout_seconds,
        )

    async def embed(self, text: str) -> list[float]:
        response = await self.client.post(
            "/embeddings",
            json={"model": self.model_name, "input": [text], "input_type": "document"},
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]


def _normalize(vector: list[float]) -> list[float]:
    length = math.sqrt(sum(value * value for value in vector))
    if length == 0:
        return vector
    return [value / length for value in vector]


def build_embedder() -> Embedder:
    if settings.voyage_api_key:
        return VoyageEmbedder()
    return FakeEmbedder()
