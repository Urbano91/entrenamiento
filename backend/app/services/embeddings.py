"""Proveedores intercambiables de embeddings para ejercicios."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import unicodedata
from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class EmbeddingProviderError(RuntimeError):
    pass


class EmbeddingProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Genera un vector por texto conservando el orden de entrada."""


class LocalFeatureHashingEmbeddingProvider(EmbeddingProvider):
    """Embedding local reproducible basado en rasgos de palabras y bigramas.

    Es deliberadamente ligero para el MVP SQLite y no descarga modelos. La
    interfaz permite sustituirlo por un modelo semántico remoto sin cambiar la
    búsqueda, el almacenamiento ni el flujo de creación.
    """

    provider_name = "local"
    model_name = "feature-hashing-es-v2"

    _TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
    _SYNONYMS = {
        "balon": "pelota",
        "balones": "pelota",
        "pelotas": "pelota",
        "jugadores": "jugador",
        "jugadoras": "jugador",
        "pases": "pase",
        "conducciones": "conduccion",
        "finalizaciones": "finalizacion",
        "apoyos": "apoyo",
        "controles": "control",
    }
    _STOP_WORDS = {
        "a", "al", "con", "de", "del", "el", "en", "la", "las", "los",
        "para", "por", "que", "se", "un", "una", "y",
    }
    _SECTION_WEIGHTS = {
        "NOMBRE": 4.0,
        "OBJETIVOS": 2.5,
        "DESCRIPCIÓN": 1.0,
        "MATERIAL": 0.6,
        "JUGADORES": 0.35,
        "ESPACIO": 0.35,
        "DURACIÓN": 0.35,
    }

    def __init__(self, dimensions: int = 384):
        if dimensions < 32:
            raise ValueError("dimensions debe ser al menos 32")
        self.dimensions = dimensions

    @staticmethod
    def _fold(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.casefold())
        return "".join(char for char in normalized if not unicodedata.combining(char))

    def _weighted_features(self, text: str) -> Counter[str]:
        features: Counter[str] = Counter()
        current_weight = 1.0
        for line in text.splitlines():
            header = line.rstrip(":").upper()
            if header in self._SECTION_WEIGHTS:
                current_weight = self._SECTION_WEIGHTS[header]
                continue
            tokens = [
                self._SYNONYMS.get(token, token)
                for token in self._TOKEN_RE.findall(self._fold(line))
                if token not in self._STOP_WORDS
            ]
            for token in tokens:
                features[token] += current_weight
            for left, right in zip(tokens, tokens[1:]):
                features[f"{left}_{right}"] += current_weight
        return features

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for feature, frequency in self._weighted_features(text).items():
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            position = int.from_bytes(digest[:8], "big") % self.dimensions
            sign = 1.0 if digest[8] & 1 else -1.0
            vector[position] += sign * (1.0 + math.log(frequency))
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            vector = [value / norm for value in vector]
        return vector

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    provider_name = "openai"

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        if not api_key:
            raise EmbeddingProviderError("OPENAI_API_KEY no está configurada")
        self.api_key = api_key
        self.model_name = model
        self.endpoint = os.getenv(
            "OPENAI_EMBEDDINGS_URL", "https://api.openai.com/v1/embeddings"
        )

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = json.dumps({"model": self.model_name, "input": list(texts)}).encode()
        request = Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=60) as response:
                result = json.loads(response.read())
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise EmbeddingProviderError(f"No se pudo generar el embedding: {exc}") from exc
        rows = sorted(result.get("data", []), key=lambda row: row["index"])
        if len(rows) != len(texts):
            raise EmbeddingProviderError("El proveedor devolvió un número inesperado de vectores")
        return [row["embedding"] for row in rows]


def get_embedding_provider() -> EmbeddingProvider:
    provider = os.getenv("EMBEDDING_PROVIDER", "local").strip().casefold()
    if provider == "local":
        dimensions = int(os.getenv("LOCAL_EMBEDDING_DIMENSIONS", "384"))
        return LocalFeatureHashingEmbeddingProvider(dimensions=dimensions)
    if provider == "openai":
        return OpenAIEmbeddingProvider(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        )
    raise EmbeddingProviderError(f"Proveedor de embeddings no soportado: {provider}")
