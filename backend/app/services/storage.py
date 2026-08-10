from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


ROOT = Path(__file__).resolve().parents[3]


class StorageService(ABC):
    """Contrato común para almacenamiento local o proveedores futuros."""

    @abstractmethod
    def save(self, key: str, data: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def open(self, key: str) -> BinaryIO:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError


class LocalStorageService(StorageService):
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if path != self.root and self.root not in path.parents:
            raise ValueError("Referencia de almacenamiento no válida")
        return path

    def save(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)

    def open(self, key: str) -> BinaryIO:
        return self._path(key).open("rb")

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()
        parent = path.parent
        while parent != self.root:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent


def get_storage_service() -> StorageService:
    configured = os.getenv("DOCUMENT_STORAGE_PATH")
    root = Path(configured) if configured else ROOT / "database" / "documentos"
    return LocalStorageService(root)
