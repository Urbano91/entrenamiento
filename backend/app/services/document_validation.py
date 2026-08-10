from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path

from fastapi import HTTPException, status


MAX_DOCUMENT_BYTES = int(os.getenv("DOCUMENT_MAX_BYTES", str(20 * 1024 * 1024)))

MIME_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

OLE_EXTENSIONS = {".doc", ".xls", ".ppt"}
TEXT_EXTENSIONS = {".csv", ".txt"}
ZIP_PREFIXES = {".docx": "word/", ".xlsx": "xl/", ".pptx": "ppt/"}


def validate_document(filename: str, declared_mime: str | None, data: bytes) -> tuple[str, str]:
    clean_name = Path(filename).name.strip()
    extension = Path(clean_name).suffix.lower()
    if not clean_name or extension not in MIME_BY_EXTENSION:
        raise HTTPException(status_code=415, detail="Tipo de archivo no permitido")
    if not data:
        raise HTTPException(status_code=422, detail="El archivo está vacío")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el máximo de {MAX_DOCUMENT_BYTES // (1024 * 1024)} MB",
        )

    valid_content = False
    if extension == ".pdf":
        valid_content = data.startswith(b"%PDF-")
    elif extension in {".jpg", ".jpeg"}:
        valid_content = data.startswith(b"\xff\xd8\xff")
    elif extension == ".png":
        valid_content = data.startswith(b"\x89PNG\r\n\x1a\n")
    elif extension == ".webp":
        valid_content = len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    elif extension in OLE_EXTENSIONS:
        valid_content = data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
    elif extension in ZIP_PREFIXES:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = archive.namelist()
                valid_content = "[Content_Types].xml" in names and any(
                    name.startswith(ZIP_PREFIXES[extension]) for name in names
                )
        except (zipfile.BadZipFile, OSError):
            valid_content = False
    elif extension in TEXT_EXTENSIONS:
        valid_content = b"\x00" not in data
        if valid_content:
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    data.decode("latin-1")
                except UnicodeDecodeError:
                    valid_content = False

    if not valid_content:
        raise HTTPException(
            status_code=415,
            detail="El contenido del archivo no coincide con el tipo permitido",
        )

    expected_mime = MIME_BY_EXTENSION[extension]
    allowed_declared = {
        expected_mime, "application/octet-stream", "binary/octet-stream", "",
    }
    if extension == ".csv":
        allowed_declared.update({"application/csv", "application/vnd.ms-excel", "text/plain"})
    if declared_mime and declared_mime.lower() not in allowed_declared:
        raise HTTPException(
            status_code=415,
            detail="El MIME declarado no coincide con el archivo",
        )
    return clean_name, expected_mime
