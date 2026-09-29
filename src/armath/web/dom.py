"""Browser adapter: implements the view protocols on the DOM and forwards events to :class:`App`.

This is the only module that imports Pyodide's ``js``/``pyodide`` modules. JS objects are typed as
``Any``; the module is excluded from coverage and verified by running the site instead.
"""

from collections.abc import Callable, Sequence
from contextlib import suppress
from datetime import datetime
from itertools import groupby
from random import Random
from typing import Any, ClassVar

from js import Date, Object, document, localStorage, window  # type: ignore[import-not-found]
from pyodide.ffi import create_proxy, to_js  # type: ignore[import-not-found]

from armath.analytics import SessionSummary
from armath.domain import Operation
from armath.learning import DrillReport, LibraryEntry, ReviewItem, TrickLesson
from armath.modes import SystemClock
from armath.persistence import MemoryStore, StoredHistory, StoredSettings
from armath.tricks import default_registry
from armath.ui import App, HistoryRow, RangeFields, Screen, SettingsForm

_OPERATION_IDS = {
    Operation.ADD: "op-add",
    Operation.SUBTRACT: "op-sub",
    Operation.MULTIPLY: "op-mul",
    Operation.DIVIDE: "op-div",
}
_OPERATION_NAMES = {
    Operation.ADD: "Addition",
    Operation.SUBTRACT: "Subtraction",
    Operation.MULTIPLY: "Multiplication",
    Operation.DIVIDE: "Division",
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


def _create(tag: str, text: str = "", class_name: str = "") -> Any:
    element = document.createElement(tag)
    if text:
        element.textContent = text
    if class_name:
        element.className = class_name
    return element


def _listen(target: Any, event: str, handler: Callable[[Any], None]) -> None:
    proxy = create_proxy(handler)
    _listeners.append(proxy)
    target.addEventListener(event, proxy)


def _percent(value: float | None) -> str:
    return _MISSING if value is None else f"{value:.0%}"


def _seconds(value: float | None) -> str:
    return _MISSING if value is None else f"{value:.1f}s"


def _format_date(when: datetime) -> str:
    """Local date and time in the browser's locale (Python in Pyodide only knows UTC)."""
    options = to_js(
        {"dateStyle": "medium", "timeStyle": "short"}, dict_converter=Object.fromEntries
    )
    return str(Date.new(when.isoformat()).toLocaleString([], options))


def _practise_button(trick_id: str) -> Any:
    button = _create("button", "Practise this trick", "button primary small")
    button.type = "button"
    button.dataset.trick = trick_id
    return button


def _lesson(
    lesson: TrickLesson,
    *,
    practise: bool = True,
    show_rule: bool = True,
    show_problem: bool = False,
) -> Any:
    """A trick's rule and worked steps; buttons with ``data-trick`` start a drill."""
    box = _create("div", class_name="lesson")
    if show_rule:
        head = _create("p", class_name="lesson-rule")
        head.appendChild(_create("strong", lesson.trick_name))
        head.appendChild(document.createTextNode(f" — {lesson.summary}"))
        box.appendChild(head)
    if show_problem:
        box.appendChild(_create("p", lesson.problem, "lesson-problem"))
    steps = _create("ol", class_name="steps")
    for step in lesson.steps:
        item = _create("li")
        item.appendChild(_create("span", step.label, "step-label"))
        item.appendChild(_create("code", step.work, "step-work"))
        steps.appendChild(item)
    box.appendChild(steps)
    if practise:
        box.appendChild(_practise_button(lesson.trick_id))
    return box


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
        Screen.LIBRARY: "library-title",
    }

    def __init__(self) -> None:
        self.current: Screen | None = None

    def go_to(self, screen: Screen) -> None:
        self.current = screen
        for candidate in Screen:
            _element(f"screen-{candidate.value}").hidden = candidate is not screen
        document.body.dataset.screen = screen.value
        for nav, target in (("nav-home", Screen.HOME), ("nav-library", Screen.LIBRARY)):
            _element(nav).classList.toggle("active", screen is target)
        window.scrollTo(0, 0)
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
            box.appendChild(_create("li", message))
        box.hidden = not errors

    def show_history(self, rows: Sequence[HistoryRow]) -> None:
        body = _element("history-rows")
        body.replaceChildren()
        for row in rows:
            tr = _create("tr")
            tr.appendChild(_create("td", _format_date(row.started_at)))
            tr.appendChild(_create("td", row.mode))
            tr.appendChild(_create("td", str(row.score), "num"))
            tr.appendChild(_create("td", _percent(row.first_try_rate), "num"))
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

    def show_status(self, label: str, value: str) -> None:
        _element("status-label").textContent = label
        _element("status-value").textContent = value

    def show_hint(self, text: str | None) -> None:
        hint = _element("hint")
        hint.textContent = text or ""
        hint.hidden = text is None

    def show_steps(self, lesson: TrickLesson | None) -> None:
        panel = _element("steps")
        panel.replaceChildren()
        if lesson is not None:
            panel.appendChild(_lesson(lesson, practise=False))
        panel.hidden = lesson is None

    def enable_reveal(self, enabled: bool) -> None:
        _element("reveal").hidden = not enabled


class DomResultsView:
    def show_summary(self, summary: SessionSummary) -> None:
        _element("result-mode").textContent = summary.mode
        _element("result-score").textContent = str(summary.score)
        _element("result-answered").textContent = str(summary.answered)
        _element("result-first-try").textContent = _percent(summary.first_try_rate)
        _element("result-mean").textContent = _seconds(summary.mean_seconds)

    def show_review(self, items: Sequence[ReviewItem]) -> None:
        box = _element("review-list")
        box.replaceChildren()
        for index, item in enumerate(items):
            details = _create("details", class_name="review-item")
            details.open = index == 0
            summary = _create("summary")
            summary.appendChild(_create("span", item.equation, "equation"))
            meta = _seconds(item.seconds)
            if item.corrections:
                meta += f" · {item.corrections} correction{'s' if item.corrections > 1 else ''}"
            summary.appendChild(_create("span", meta, "meta"))
            if item.lesson is not None:
                summary.appendChild(_create("span", item.lesson.trick_name, "tag"))
            details.appendChild(summary)
            if item.lesson is not None:
                details.appendChild(_lesson(item.lesson))
            box.appendChild(details)
        _element("review").hidden = not items

    def show_drill_report(self, report: DrillReport | None) -> None:
        _element("drill-report").hidden = report is None
        if report is None:
            return
        _element("drill-focused").textContent = _seconds(report.focused_seconds)
        _element("drill-mixed").textContent = _seconds(report.mixed_trick_seconds)
        _element("drill-lookalike").textContent = _seconds(report.lookalike_seconds)


class DomLibraryView:
    def show_library(self, entries: Sequence[LibraryEntry]) -> None:
        box = _element("library-list")
        box.replaceChildren()
        for operation, group in groupby(entries, key=lambda entry: entry.operation):
            section = _create("section", class_name="library-group")
            section.appendChild(_create("h2", _OPERATION_NAMES[operation]))
            for entry in group:
                card = _create("article", class_name="card trick-card")
                title = _create("h3", entry.name)
                if entry.is_general:
                    title.appendChild(_create("span", "general method", "tag"))
                card.appendChild(title)
                card.appendChild(_create("p", entry.summary, "muted"))
                card.appendChild(_create("p", "Example", "eyebrow"))
                card.appendChild(_lesson(entry.example, show_rule=False, show_problem=True))
                section.appendChild(card)
            box.appendChild(section)


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
        library_view=DomLibraryView(),
        history=StoredHistory(store),
        settings=StoredSettings(store),
        registry=default_registry(),
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

    def on_answer_key(event: Any) -> None:
        if event.key == "?":
            event.preventDefault()
            app.reveal_steps()

    def on_click(event: Any) -> None:
        button = event.target.closest("[data-trick]")
        if button is not None:
            app.start_drill(str(button.dataset.trick))

    def on_reveal(_: Any) -> None:
        app.reveal_steps()
        _element("answer").focus()

    _listen(_element("settings-form"), "submit", on_start)
    _listen(_element("answer"), "input", lambda event: app.answer(event.target.value))
    _listen(_element("answer"), "keydown", on_answer_key)
    _listen(_element("reveal"), "click", on_reveal)
    _listen(_element("play-again"), "click", lambda _: app.play_again())
    _listen(_element("back-home"), "click", lambda _: app.open_home())
    _listen(_element("quit"), "click", lambda _: app.open_home())
    _listen(_element("nav-home"), "click", lambda _: app.open_home())
    _listen(_element("nav-library"), "click", lambda _: app.open_library())
    _listen(document, "keydown", on_key)
    _listen(document, "click", on_click)

    tick = create_proxy(app.tick)
    _listeners.append(tick)
    window.setInterval(tick, 100)

    app.open_home()
    document.body.classList.remove("loading")
