"""Turning what the user typed into an exact number."""

import re
from fractions import Fraction

_ANSWER = re.compile(r"-?(?:\d+/\d+|\d+(?:\.\d*)?|\.\d+)")


def parse_answer(text: str) -> Fraction | None:
    """Parse a typed answer such as ``42``, ``-3``, ``0.125``, ``.5``, ``0,5`` or ``3/8``.

    Returns ``None`` for anything that is not a complete number.
    """
    normalized = text.strip().replace(" ", "").replace(",", ".").replace("−", "-")
    if not _ANSWER.fullmatch(normalized):
        return None
    try:
        return Fraction(normalized)
    except ZeroDivisionError:
        return None
