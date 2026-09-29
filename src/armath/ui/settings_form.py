"""The raw home-screen form and its validation into :class:`PracticeSettings`."""

from dataclasses import dataclass, field

from armath.domain import Operation
from armath.generators import IntRange, ZetamacSettings
from armath.settings import PracticeSettings


class FormError(ValueError):
    def __init__(self, messages: list[str]) -> None:
        super().__init__("; ".join(messages))
        self.messages = messages


@dataclass(frozen=True)
class RangeFields:
    low: str
    high: str

    @classmethod
    def of(cls, int_range: IntRange) -> "RangeFields":
        return cls(str(int_range.low), str(int_range.high))


@dataclass(frozen=True)
class SettingsForm:
    """Exactly what the user entered, as text; nothing here is validated yet."""

    addition_left: RangeFields
    addition_right: RangeFields
    multiplication_left: RangeFields
    multiplication_right: RangeFields
    operations: frozenset[Operation] = field(default_factory=lambda: frozenset(Operation))
    duration_seconds: str = "120"

    @classmethod
    def from_settings(cls, settings: PracticeSettings) -> "SettingsForm":
        zetamac = settings.zetamac
        return cls(
            addition_left=RangeFields.of(zetamac.addition_left),
            addition_right=RangeFields.of(zetamac.addition_right),
            multiplication_left=RangeFields.of(zetamac.multiplication_left),
            multiplication_right=RangeFields.of(zetamac.multiplication_right),
            operations=zetamac.operations,
            duration_seconds=str(settings.duration_seconds),
        )

    def parse(self) -> PracticeSettings:
        """Validate every field, reporting all problems at once via :class:`FormError`."""
        check = _Validator()
        addition_left = check.range("Addition, left", self.addition_left)
        addition_right = check.range("Addition, right", self.addition_right)
        multiplication_left = check.range("Multiplication, left", self.multiplication_left)
        multiplication_right = check.range("Multiplication, right", self.multiplication_right)
        duration = check.integer("Duration", self.duration_seconds, minimum=1)
        if not self.operations:
            check.errors.append("Pick at least one operation.")
        if Operation.DIVIDE in self.operations and 0 in multiplication_left:
            check.errors.append("Division needs a left multiplication range without 0.")
        if check.errors:
            raise FormError(check.errors)

        zetamac = ZetamacSettings(
            addition_left=addition_left,
            addition_right=addition_right,
            multiplication_left=multiplication_left,
            multiplication_right=multiplication_right,
            operations=self.operations,
        )
        return PracticeSettings(zetamac=zetamac, duration_seconds=duration)


class _Validator:
    """Collects errors; an invalid field yields a harmless placeholder that must not be used
    once :attr:`errors` is non-empty."""

    _PLACEHOLDER = IntRange(1, 1)

    def __init__(self) -> None:
        self.errors: list[str] = []

    def integer(self, label: str, text: str, minimum: int | None = None) -> int:
        try:
            value = int(text.strip())
        except ValueError:
            self.errors.append(f"{label}: '{text}' is not a whole number.")
            return 1
        if minimum is not None and value < minimum:
            self.errors.append(f"{label} must be at least {minimum}.")
        return value

    def range(self, label: str, fields: RangeFields) -> IntRange:
        errors_before = len(self.errors)
        low = self.integer(f"{label} (from)", fields.low)
        high = self.integer(f"{label} (to)", fields.high)
        if len(self.errors) > errors_before:
            return self._PLACEHOLDER
        if low > high:
            self.errors.append(f"{label}: 'from' must not be greater than 'to'.")
            return self._PLACEHOLDER
        return IntRange(low, high)
