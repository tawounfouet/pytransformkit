"""Engine-independent logical data types."""

from dataclasses import dataclass


class DataType:
    """Marker base class for logical PyTransformKit data types."""

    __slots__ = ()

    @staticmethod
    def duration(unit: str = "us") -> DurationType:
        return DurationType(unit=unit)

    @staticmethod
    def list_of(
        element_type: DataType,
        *,
        element_nullable: bool = True,
    ) -> ListType:
        return ListType(
            element_type=element_type,
            element_nullable=element_nullable,
        )

    @staticmethod
    def struct(
        fields: tuple[StructField, ...],
    ) -> StructType:
        return StructType(fields=fields)

    @staticmethod
    def map_of(
        key: DataType,
        value: DataType,
        *,
        value_nullable: bool = True,
    ) -> MapType:
        return MapType(
            key_type=key,
            value_type=value,
            value_nullable=value_nullable,
        )


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
class DurationType(DataType):
    """Logical elapsed-time duration."""

    unit: str = "us"

    def __post_init__(self) -> None:
        _validate_time_unit(self.unit)


@dataclass(frozen=True, slots=True)
class BinaryType(DataType):
    """Logical binary type."""


@dataclass(frozen=True, slots=True)
class ListType(DataType):
    """Logical homogeneous list type."""

    element_type: DataType
    element_nullable: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.element_type, DataType):
            raise TypeError("List element_type must be a PyTransformKit DataType.")


@dataclass(frozen=True, slots=True)
class StructField:
    """Field definition embedded inside a StructType."""

    name: str
    data_type: DataType
    nullable: bool = True

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Struct field name must not be empty.")
        if not isinstance(self.data_type, DataType):
            raise TypeError("Struct field data_type must be a PyTransformKit DataType.")


@dataclass(frozen=True, slots=True)
class StructType(DataType):
    """Logical ordered struct type."""

    fields: tuple[StructField, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.fields, tuple):
            raise TypeError("Struct fields must be provided as a tuple.")
        if any(not isinstance(field, StructField) for field in self.fields):
            raise TypeError("Struct fields must contain only StructField values.")
        names = tuple(field.name for field in self.fields)
        if len(names) != len(set(names)):
            raise ValueError("Struct field names must be unique.")

    def field(self, name: str) -> StructField:
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)


@dataclass(frozen=True, slots=True)
class MapType(DataType):
    """Logical key/value map type."""

    key_type: DataType
    value_type: DataType
    value_nullable: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.key_type, DataType):
            raise TypeError("Map key_type must be a PyTransformKit DataType.")
        if not isinstance(self.value_type, DataType):
            raise TypeError("Map value_type must be a PyTransformKit DataType.")


@dataclass(frozen=True, slots=True)
class UnknownType(DataType):
    """Logical type used when a precise type cannot be inferred."""


def _validate_time_unit(unit: str) -> None:
    if unit not in {"s", "ms", "us", "ns"}:
        raise ValueError("Time unit must be one of 's', 'ms', 'us', or 'ns'.")
