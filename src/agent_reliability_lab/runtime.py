from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .models import ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        self._tools[tool.name] = tool

    def register_many(self, tools: list[ToolSpec]) -> None:
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def all(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)


def tool(name: str, description: str, *, requires_approval: bool = False, max_retries: int = 0, risk_level: str = "low"):
    def decorator(func: Callable[[dict[str, Any]], Any]) -> ToolSpec:
        return ToolSpec(
            name=name,
            description=description,
            executor=func,
            requires_approval=requires_approval,
            max_retries=max_retries,
            risk_level=risk_level,
        )

    return decorator
