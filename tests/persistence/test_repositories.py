from factories import attempt, record

from armath.generators import ZetamacSettings
from armath.persistence import MemoryStore, StoredHistory, StoredSettings
from armath.persistence.repositories import HISTORY_KEY, SETTINGS_KEY
from armath.settings import PracticeSettings


def test_empty_history() -> None:
    assert StoredHistory(MemoryStore()).all() == []


def test_history_keeps_sessions_in_order() -> None:
    store = MemoryStore()
    first, second = record(attempt(), mode="A"), record(attempt(correct=False), mode="B")

    StoredHistory(store).add(first)
    StoredHistory(store).add(second)

    assert StoredHistory(store).all() == [first, second]


def test_unreadable_history_is_backed_up_not_lost() -> None:
    store = MemoryStore()
    store.set(HISTORY_KEY, "{not json")
    history = StoredHistory(store)

    assert history.all() == []
    assert store.get(HISTORY_KEY + ".unreadable") == "{not json"

    history.add(record(attempt()))
    assert len(history.all()) == 1


def test_settings_default_when_missing() -> None:
    assert StoredSettings(MemoryStore()).load() == PracticeSettings()


def test_settings_round_trip_through_store() -> None:
    store = MemoryStore()
    settings = PracticeSettings(zetamac=ZetamacSettings(), duration_seconds=30)

    StoredSettings(store).save(settings)

    assert StoredSettings(store).load() == settings


def test_unreadable_settings_fall_back_to_defaults() -> None:
    store = MemoryStore()
    store.set(SETTINGS_KEY, '{"zetamac": 5}')

    assert StoredSettings(store).load() == PracticeSettings()
