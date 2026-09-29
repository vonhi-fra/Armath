"""Terminal front end: play a session, or explain a problem with the trick catalogue."""

import argparse
from collections.abc import Callable, Sequence
from datetime import timedelta
from random import Random

from armath import presets
from armath.domain import Operation, parse_problem
from armath.domain.numbers import format_value
from armath.modes import Session, SystemClock
from armath.tricks import Explanation, Trick, TrickRegistry, default_registry

Read = Callable[[str], str]
Write = Callable[[str], None]

_OPERATION_NAMES = {
    Operation.ADD: "Addition",
    Operation.SUBTRACT: "Subtraction",
    Operation.MULTIPLY: "Multiplication",
    Operation.DIVIDE: "Division",
}


def run_session(session: Session, read: Read, write: Write) -> None:
    """Ask problems until the session ends; wrong answers are retried like on Zetamac."""
    while not session.is_over:
        text = read(f"{session.current.prompt}  ")
        if session.is_over:
            write("Time's up!")
            break
        if session.answer(text) is None:
            write("  ✗ try again")
    write(f"Score: {session.score}")


def format_explanation(explanation: Explanation, trick: Trick) -> list[str]:
    lines = [f"{trick.name}: {trick.summary}"]
    lines += [
        f"  {number}. {step.label}:  {step.work}"
        for number, step in enumerate(explanation.steps, start=1)
    ]
    lines.append(f"  Answer: {format_value(explanation.result)}")
    return lines


def explain(text: str, registry: TrickRegistry, write: Write, *, every_trick: bool = False) -> int:
    """Print how to solve ``text``; returns a process exit code."""
    try:
        problem = parse_problem(text)
    except ValueError as error:
        write(str(error))
        return 2
    tricks = registry.applicable(problem)
    if not tricks:
        write(f"{problem.prompt}\nNo trick covers this problem yet.")
        return 1
    write(problem.prompt)
    shown, others = (tricks, []) if every_trick else (tricks[:1], tricks[1:])
    for trick in shown:
        write("")
        for line in format_explanation(trick.explain(problem), trick):
            write(line)
    if others:
        write("")
        write("Also works: " + ", ".join(trick.name for trick in others) + "  (use --all)")
    return 0


def list_tricks(registry: TrickRegistry, write: Write) -> None:
    for operation, title in _OPERATION_NAMES.items():
        write(title)
        for trick in registry.for_operation(operation):
            suffix = " (general method)" if trick.fallback else ""
            write(f"  {trick.name}{suffix}: {trick.summary}")


def _parser() -> argparse.ArgumentParser:
    play_options = argparse.ArgumentParser(add_help=False)
    play_options.add_argument("--seconds", type=int, default=120, help="session length")
    play_options.add_argument("--seed", type=int, default=None, help="random seed")

    parser = argparse.ArgumentParser(
        prog="armath", description="Mental arithmetic trainer.", parents=[play_options]
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("play", parents=[play_options], help="play a Zetamac session (default)")
    explain_command = commands.add_parser("explain", help="show how to solve a problem")
    explain_command.add_argument("problem", help="e.g. '858 / 11' or '67 x 11'")
    explain_command.add_argument("--all", action="store_true", help="every applicable trick")
    commands.add_parser("tricks", help="list the trick catalogue")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    match args.command:
        case "explain":
            return explain(args.problem, default_registry(), print, every_trick=args.all)
        case "tricks":
            list_tricks(default_registry(), print)
            return 0
        case _:
            return _play(args.seconds, args.seed)


def _play(seconds: int, seed: int | None) -> int:
    plan = presets.zetamac(duration=timedelta(seconds=seconds))
    session = Session(plan, SystemClock(), Random(seed))
    try:
        run_session(session, input, print)
    except (EOFError, KeyboardInterrupt):
        print(f"\nStopped. Score: {session.score}")
    return 0
