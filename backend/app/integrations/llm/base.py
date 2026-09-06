from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        json_mode: bool = False,
    ) -> str:
        ...
