"""Engine-independent logical data types."""

from dataclasses import dataclass


class DataType:
    """Marker base class for logical PyTransformKit data types."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class StringType(DataType):
    """Logical string type."""


@dataclass(frozen=True, slots=True)
class BooleanType(DataType):
    """Logical boolean type."""


@dataclass(frozen=True, slots=True)
class IntegerType(DataType):
    """Logical signed or unsigned integer type."""

    bits: int = 64
    signed: bool = True

    def __post_init__(self) -> None:
        if self.bits not in {8, 16, 32, 64}:
            raise ValueError("Integer bits must be one of 8, 16, 32, or 64.")


@dataclass(frozen=True, slots=True)
class FloatType(DataType):
    """Logical floating-point type."""

    bits: int = 64

    def __post_init__(self) -> None:
        if self.bits not in {32, 64}:
            raise ValueError("Float bits must be either 32 or 64.")


@dataclass(frozen=True, slots=True)
class DecimalType(DataType):
    """Logical fixed-precision decimal type."""

    precision: int
    scale: int

    def __post_init__(self) -> None:
        if self.precision <= 0:
            raise ValueError("Decimal precision must be greater than zero.")
        if self.scale < 0:
            raise ValueError("Decimal scale must be non-negative.")
        if self.scale > self.precision:
            raise ValueError("Decimal scale must not exceed precision.")


@dataclass(frozen=True, slots=True)
class DateType(DataType):
    """Logical calendar date type."""


@dataclass(frozen=True, slots=True)
class TimeType(DataType):
    """Logical time-of-day type."""

    unit: str = "us"

    def __post_init__(self) -> None:
        _validate_time_unit(self.unit)


@dataclass(frozen=True, slots=True)
class TimestampType(DataType):
    """Logical timestamp type with optional timezone."""

    unit: str = "us"
    timezone: str | None = None

    def __post_init__(self) -> None:
        _validate_time_unit(self.unit)
        if self.timezone is not None and not self.timezone.strip():
            raise ValueError("Timestamp timezone must not be blank.")


@dataclass(frozen=True, slots=True)
class BinaryType(DataType):
    """Logical binary type."""


@dataclass(frozen=True, slots=True)
class UnknownType(DataType):
    """Logical type used when a precise type cannot be inferred."""


def _validate_time_unit(unit: str) -> None:
    if unit not in {"s", "ms", "us", "ns"}:
        raise ValueError("Time unit must be one of 's', 'ms', 'us', or 'ns'.")
