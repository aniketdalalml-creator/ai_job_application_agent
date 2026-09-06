from __future__ import annotations

from typing import Protocol


class ObjectStorage(Protocol):
    """Future resume/file storage. Local disk or S3 can implement this."""

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        ...

    def get(self, key: str) -> bytes:
        ...
