"""Exporting and restoring all data as one JSON file.

Browser storage can be cleared at any time, so a backup is the only durable copy. Restoring
merges: sessions already present (same start time and mode) are skipped, nothing is deleted.
"""

import json
from dataclasses import dataclass
from datetime import datetime

from armath.domain import SessionRecord
from armath.persistence.repositories import HistoryRepository, SettingsRepository
from armath.persistence.serialization import (
    record_from_dict,
    record_to_dict,
    settings_from_dict,
    settings_to_dict,
)
from armath.settings import PracticeSettings

BACKUP_FORMAT = "armath-backup"
BACKUP_VERSION = 1


class BackupError(ValueError):
    """The file is not a readable Armath backup."""


@dataclass(frozen=True)
class RestoreSummary:
    added: int
    already_present: int


def backup_filename(now: datetime) -> str:
    return f"armath-backup-{now:%Y-%m-%d}.json"


class Backup:
    def __init__(self, history: HistoryRepository, settings: SettingsRepository) -> None:
        self._history = history
        self._settings = settings

    def export(self, now: datetime) -> str:
        document = {
            "format": BACKUP_FORMAT,
            "version": BACKUP_VERSION,
            "exported_at": now.isoformat(),
            "settings": settings_to_dict(self._settings.load()),
            "sessions": [record_to_dict(record) for record in self._history.all()],
        }
        return json.dumps(document, ensure_ascii=False)

    def restore(self, text: str) -> RestoreSummary:
        """Merge a backup into the current data; raises :class:`BackupError` if unreadable."""
        records, settings = self._read(text)
        existing = self._history.all()
        seen = {_identity(record) for record in existing}
        new = [record for record in records if _identity(record) not in seen]
        merged = sorted([*existing, *new], key=lambda record: record.started_at)
        self._history.replace_all(merged)
        if settings is not None:
            self._settings.save(settings)
        return RestoreSummary(added=len(new), already_present=len(records) - len(new))

    @staticmethod
    def _read(text: str) -> tuple[list[SessionRecord], PracticeSettings | None]:
        try:
            document = json.loads(text)
        except ValueError as error:
            raise BackupError("This file is not valid JSON.") from error
        if not isinstance(document, dict) or document.get("format") != BACKUP_FORMAT:
            raise BackupError("This file is not an Armath backup.")
        try:
            records = [record_from_dict(item) for item in document["sessions"]]
            settings = settings_from_dict(document["settings"]) if "settings" in document else None
        except (KeyError, TypeError, ValueError) as error:
            raise BackupError("This backup is damaged and could not be read.") from error
        return records, settings


def _identity(record: SessionRecord) -> tuple[datetime, str]:
    return record.started_at, record.mode
