from __future__ import annotations

from typing import Any


class InMemoryStateStore:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._history: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._data.clear()
        self._history.clear()

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._history.append({"key": key, "value": value})

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def snapshot(self) -> dict[str, Any]:
        return dict(self._data)

    def history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def update(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            self.set(key, value)
