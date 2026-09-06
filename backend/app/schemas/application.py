from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ApplicationPatch(BaseModel):
    status: Literal[
        "saved",
        "generating",
        "ready",
        "failed",
        "applied",
        "interviewing",
        "offer",
        "rejected",
        "withdrawn",
    ] | None = None
    notes: str | None = None
