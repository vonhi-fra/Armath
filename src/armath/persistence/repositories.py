"""Session history and settings, stored as JSON in a key-value store."""

import json
from typing import Protocol

from armath.domain import SessionRecord
from armath.persistence.serialization import (
    record_from_dict,
    record_to_dict,
    settings_from_dict,
    settings_to_dict,
)
from armath.persistence.store import KeyValueStore
from armath.settings import PracticeSettings

FORMAT_VERSION = 1
HISTORY_KEY = "armath.history"
SETTINGS_KEY = "armath.settings"
BACKUP_SUFFIX = ".unreadable"

_MALFORMED = (KeyError, TypeError, ValueError)


class HistoryRepository(Protocol):
    def add(self, record: SessionRecord) -> None: ...

    def all(self) -> list[SessionRecord]:
        """Every stored session, oldest first."""
        ...


class SettingsRepository(Protocol):
    def load(self) -> PracticeSettings: ...

    def save(self, settings: PracticeSettings) -> None: ...


class StoredHistory:
    """History as one JSON document.

    Unreadable data is never silently dropped: it is copied to ``<key>.unreadable`` first.
    """

    def __init__(self, store: KeyValueStore, key: str = HISTORY_KEY) -> None:
        self._store = store
        self._key = key

    def add(self, record: SessionRecord) -> None:
        records = [*self.all(), record]
        document = {"version": FORMAT_VERSION, "sessions": [record_to_dict(r) for r in records]}
        self._store.set(self._key, json.dumps(document, separators=(",", ":")))

    def all(self) -> list[SessionRecord]:
        raw = self._store.get(self._key)
        if raw is None:
            return []
        try:
            return [record_from_dict(item) for item in json.loads(raw)["sessions"]]
        except _MALFORMED:
            self._store.set(self._key + BACKUP_SUFFIX, raw)
            self._store.set(self._key, json.dumps({"version": FORMAT_VERSION, "sessions": []}))
            return []


class StoredSettings:
    """Settings as JSON; falls back to defaults when missing or unreadable."""

    def __init__(self, store: KeyValueStore, key: str = SETTINGS_KEY) -> None:
        self._store = store
        self._key = key

    def load(self) -> PracticeSettings:
        raw = self._store.get(self._key)
        if raw is None:
            return PracticeSettings()
        try:
            return settings_from_dict(json.loads(raw))
        except _MALFORMED:
            return PracticeSettings()

    def save(self, settings: PracticeSettings) -> None:
        self._store.set(self._key, json.dumps(settings_to_dict(settings)))
