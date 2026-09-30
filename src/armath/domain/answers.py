"""Turning what the user typed into an exact number."""

import re
from fractions import Fraction

_ANSWER = re.compile(r"-?(?:\d+/\d+|\d+(?:\.\d*)?|\.\d+)%?")


def parse_answer(text: str) -> Fraction | None:
    """Parse a typed answer such as ``42``, ``-3``, ``0.125``, ``.5``, ``0,5``, ``3/8`` or ``15%``.

    A trailing ``%`` divides by 100, so ``15%`` and ``0.15`` are the same answer.
    Returns ``None`` for anything that is not a complete number.
    """
    normalized = text.strip().replace(" ", "").replace(",", ".").replace("−", "-")
    if not _ANSWER.fullmatch(normalized):
        return None
    number, percent = normalized.removesuffix("%"), normalized.endswith("%")
    try:
        value = Fraction(number)
    except ZeroDivisionError:
        return None
    return value / 100 if percent else value
