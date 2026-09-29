import json
from dataclasses import replace
from datetime import timedelta

import pytest
from factories import START, attempt, record

from armath.domain import SessionRecord
from armath.persistence import (
    Backup,
    BackupError,
    MemoryStore,
    StoredHistory,
    StoredSettings,
    backup_filename,
)
from armath.settings import PracticeSettings


def _record(days: int, mode: str = "Zetamac 120s") -> SessionRecord:
    return replace(record(attempt(), mode=mode), started_at=START + timedelta(days=days))


class Data:
    def __init__(self) -> None:
        self.store = MemoryStore()
        self.history = StoredHistory(self.store)
        self.settings = StoredSettings(self.store)
        self.backup = Backup(self.history, self.settings)


def test_export_then_restore_into_an_empty_browser() -> None:
    old = Data()
    old.history.add(_record(0))
    old.history.add(_record(1))
    old.settings.save(PracticeSettings(duration_seconds=60))
    fresh = Data()

    summary = fresh.backup.restore(old.backup.export(START))

    assert (summary.added, summary.already_present) == (2, 0)
    assert fresh.history.all() == old.history.all()
    assert fresh.settings.load().duration_seconds == 60


def test_restore_merges_without_duplicates_in_date_order() -> None:
    source = Data()
    source.history.add(_record(0))
    source.history.add(_record(2))
    target = Data()
    target.history.add(_record(1))
    target.history.add(_record(2))

    summary = target.backup.restore(source.backup.export(START))

    assert (summary.added, summary.already_present) == (1, 1)
    assert [r.started_at for r in target.history.all()] == [
        START + timedelta(days=day) for day in (0, 1, 2)
    ]


def test_export_is_tagged_json() -> None:
    document = json.loads(Data().backup.export(START))

    assert document["format"] == "armath-backup"
    assert document["sessions"] == []


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("not json", "not valid JSON"),
        ('["a list"]', "not an Armath backup"),
        ('{"format": "something-else"}', "not an Armath backup"),
        ('{"format": "armath-backup"}', "damaged"),
        ('{"format": "armath-backup", "sessions": [{"mode": 1}]}', "damaged"),
    ],
)
def test_unreadable_backups_are_rejected_and_change_nothing(text: str, message: str) -> None:
    data = Data()
    data.history.add(_record(0))

    with pytest.raises(BackupError, match=message):
        data.backup.restore(text)

    assert len(data.history.all()) == 1


def test_backup_without_settings_keeps_current_settings() -> None:
    data = Data()
    data.settings.save(PracticeSettings(duration_seconds=30))

    data.backup.restore('{"format": "armath-backup", "sessions": []}')

    assert data.settings.load().duration_seconds == 30


def test_filename_has_the_date() -> None:
    assert backup_filename(START) == "armath-backup-2026-09-29.json"
