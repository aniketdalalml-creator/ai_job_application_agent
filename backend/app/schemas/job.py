from __future__ import annotations

from pydantic import BaseModel


class ManualJobIn(BaseModel):
    company_name: str
    job_description: str
    title: str = ""
    location: str = ""
