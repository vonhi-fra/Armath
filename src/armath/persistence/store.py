"""The minimal storage interface the app needs; the browser's localStorage fits it."""

from typing import Protocol


class KeyValueStore(Protocol):
    def get(self, key: str) -> str | None: ...

    def set(self, key: str, value: str) -> None: ...


class MemoryStore:
    """A store kept in a dict; for tests and as a fallback when storage is unavailable."""

    def __init__(self) -> None:
        self._items: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._items.get(key)

    def set(self, key: str, value: str) -> None:
        self._items[key] = value
