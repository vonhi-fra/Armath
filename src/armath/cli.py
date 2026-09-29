"""Terminal front end: a quick way to play a session without the web UI."""

import argparse
from collections.abc import Callable, Sequence
from datetime import timedelta
from random import Random

from armath import presets
from armath.modes import Session, SystemClock

Read = Callable[[str], str]
Write = Callable[[str], None]


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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="armath", description="Zetamac-style practice.")
    parser.add_argument("--seconds", type=int, default=120, help="session length")
    parser.add_argument("--seed", type=int, default=None, help="random seed")
    args = parser.parse_args(argv)

    plan = presets.zetamac(duration=timedelta(seconds=args.seconds))
    session = Session(plan, SystemClock(), Random(args.seed))
    try:
        run_session(session, input, print)
    except (EOFError, KeyboardInterrupt):
        print(f"\nStopped. Score: {session.score}")
    return 0
