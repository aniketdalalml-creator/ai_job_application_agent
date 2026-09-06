from __future__ import annotations

from pydantic import BaseModel


class OkOut(BaseModel):
    ok: bool = True
