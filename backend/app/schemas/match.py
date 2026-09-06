from __future__ import annotations

from pydantic import BaseModel


class SearchStartOut(BaseModel):
    id: str
    status: str
