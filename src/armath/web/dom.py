"""Browser adapter: implements the view protocols on the DOM and forwards events to :class:`App`.

This is the only module that imports Pyodide's ``js``/``pyodide`` modules. JS objects are typed as
``Any``; the module is excluded from coverage and verified by running the site instead.
"""

from collections.abc import Callable, Sequence
from contextlib import suppress
from datetime import datetime
from random import Random
from typing import Any, ClassVar

from js import Date, Object, document, localStorage, window  # type: ignore[import-not-found]
from pyodide.ffi import create_proxy, to_js  # type: ignore[import-not-found]

from armath.analytics import SessionSummary
from armath.domain import Operation
from armath.modes import SystemClock
from armath.persistence import MemoryStore, StoredHistory, StoredSettings
from armath.ui import App, HistoryRow, RangeFields, Screen, SettingsForm

_OPERATION_IDS = {
    Operation.ADD: "op-add",
    Operation.SUBTRACT: "op-sub",
    Operation.MULTIPLY: "op-mul",
    Operation.DIVIDE: "op-div",
}
_RANGE_IDS = ("addition_left", "addition_right", "multiplication_left", "multiplication_right")

_MISSING = "—"

# Proxies must stay alive as long as the page listens to them.
_listeners: list[Any] = []


def _element(element_id: str) -> Any:
    element = document.getElementById(element_id)
    if element is None:
        raise LookupError(f"missing element #{element_id}")
    return element


def _listen(target: Any, event: str, handler: Callable[[Any], None]) -> None:
    proxy = create_proxy(handler)
    _listeners.append(proxy)
    target.addEventListener(event, proxy)


def _cell(row: Any, text: str, class_name: str = "") -> None:
    cell = document.createElement("td")
    cell.textContent = text
    if class_name:
        cell.className = class_name
    row.appendChild(cell)


def _percent(value: float | None) -> str:
    return _MISSING if value is None else f"{value:.0%}"


def _format_date(when: datetime) -> str:
    """Local date and time in the browser's locale (Python in Pyodide only knows UTC)."""
    options = to_js(
        {"dateStyle": "medium", "timeStyle": "short"}, dict_converter=Object.fromEntries
    )
    return str(Date.new(when.isoformat()).toLocaleString([], options))


class LocalStorageStore:
    """localStorage can be missing or throw (private mode, blocked storage); fall back to memory."""

    def __init__(self) -> None:
        self._fallback = MemoryStore()

    def get(self, key: str) -> str | None:
        try:
            value = localStorage.getItem(key)
        except Exception:
            return self._fallback.get(key)
        return None if value is None else str(value)

    def set(self, key: str, value: str) -> None:
        self._fallback.set(key, value)
        with suppress(Exception):
            localStorage.setItem(key, value)


class DomNavigator:
    _FOCUS: ClassVar[dict[Screen, str]] = {
        Screen.HOME: "start",
        Screen.GAME: "answer",
        Screen.RESULTS: "play-again",
    }

    def __init__(self) -> None:
        self.current: Screen | None = None

    def go_to(self, screen: Screen) -> None:
        self.current = screen
        for candidate in Screen:
            _element(f"screen-{candidate.value}").hidden = candidate is not screen
        document.body.dataset.screen = screen.value
        _element(self._FOCUS[screen]).focus()


class DomHomeView:
    def show_settings(self, form: SettingsForm) -> None:
        for operation, element_id in _OPERATION_IDS.items():
            _element(element_id).checked = operation in form.operations
        for name in _RANGE_IDS:
            fields: RangeFields = getattr(form, name)
            _element(f"{name}-low").value = fields.low
            _element(f"{name}-high").value = fields.high
        _element("duration").value = form.duration_seconds

    def read_form(self) -> SettingsForm:
        ranges = {
            name: RangeFields(_element(f"{name}-low").value, _element(f"{name}-high").value)
            for name in _RANGE_IDS
        }
        operations = frozenset(
            operation
            for operation, element_id in _OPERATION_IDS.items()
            if _element(element_id).checked
        )
        return SettingsForm(
            **ranges, operations=operations, duration_seconds=_element("duration").value
        )

    def show_form_errors(self, errors: Sequence[str]) -> None:
        box = _element("form-errors")
        box.replaceChildren()
        for message in errors:
            item = document.createElement("li")
            item.textContent = message
            box.appendChild(item)
        box.hidden = not errors

    def show_history(self, rows: Sequence[HistoryRow]) -> None:
        body = _element("history-rows")
        body.replaceChildren()
        for row in rows:
            tr = document.createElement("tr")
            _cell(tr, _format_date(row.started_at))
            _cell(tr, row.mode)
            _cell(tr, str(row.score), "num")
            _cell(tr, _percent(row.first_try_rate), "num")
            body.appendChild(tr)
        _element("history-empty").hidden = bool(rows)
        _element("history-table").hidden = not rows


class DomGameView:
    def show_problem(self, prompt: str) -> None:
        _element("problem").textContent = prompt

    def clear_answer(self) -> None:
        _element("answer").value = ""

    def show_score(self, score: int) -> None:
        _element("score").textContent = str(score)

    def show_time(self, text: str) -> None:
        _element("timer").textContent = text


class DomResultsView:
    def show_summary(self, summary: SessionSummary) -> None:
        _element("result-mode").textContent = summary.mode
        _element("result-score").textContent = str(summary.score)
        _element("result-answered").textContent = str(summary.answered)
        _element("result-first-try").textContent = _percent(summary.first_try_rate)
        mean = summary.mean_seconds
        _element("result-mean").textContent = _MISSING if mean is None else f"{mean:.1f}s"
        body = _element("slowest-rows")
        body.replaceChildren()
        for slow in summary.slowest:
            tr = document.createElement("tr")
            _cell(tr, slow.equation, "equation")
            _cell(tr, f"{slow.seconds:.1f}s", "num")
            body.appendChild(tr)
        _element("slowest").hidden = not summary.slowest


def main() -> None:
    """Build the app, attach event listeners and show the home screen."""
    store = LocalStorageStore()
    navigator = DomNavigator()
    home_view = DomHomeView()
    app = App(
        navigator=navigator,
        home_view=home_view,
        game_view=DomGameView(),
        results_view=DomResultsView(),
        history=StoredHistory(store),
        settings=StoredSettings(store),
        clock=SystemClock(),
        rng=Random(),
    )

    def on_start(event: Any) -> None:
        event.preventDefault()
        app.start(home_view.read_form())

    def on_key(event: Any) -> None:
        if event.key == "Escape" and navigator.current is not Screen.HOME:
            event.preventDefault()
            app.open_home()

    _listen(_element("settings-form"), "submit", on_start)
    _listen(_element("answer"), "input", lambda event: app.answer(event.target.value))
    _listen(_element("play-again"), "click", lambda _: app.play_again())
    _listen(_element("back-home"), "click", lambda _: app.open_home())
    _listen(_element("quit"), "click", lambda _: app.open_home())
    _listen(document, "keydown", on_key)

    tick = create_proxy(app.tick)
    _listeners.append(tick)
    window.setInterval(tick, 100)

    app.open_home()
    document.body.classList.remove("loading")
