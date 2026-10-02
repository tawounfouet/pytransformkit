"""Immutable declarative schema definition values.

These values represent normalized authoring intent. They deliberately contain no
YAML, filesystem, engine, or canonical Domain behavior. Validation here is limited
to local Python invariants; rich declarative diagnostics belong to later services.
"""

from __future__ import annotations

from dataclasses import dataclass

_INTEGER_BITS = frozenset({8, 16, 32, 64})
_FLOAT_BITS = frozenset({32, 64})
_TIME_UNITS = frozenset({"s", "ms", "us", "ns"})


def _require_non_blank_text(value: object, *, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    if not value.strip():
        raise ValueError(f"{name} must contain non-whitespace text.")


def _require_bool(value: object, *, name: str) -> None:
    if type(value) is not bool:
        raise TypeError(f"{name} must be a bool.")


def _require_int(value: object, *, name: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be an int.")


def _require_type_definition(value: object, *, name: str) -> None:
    if not isinstance(value, TypeDefinition):
        raise TypeError(f"{name} must be a TypeDefinition.")


def _require_tuple_items(
    value: object,
    *,
    name: str,
    item_type: type[object],
) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{name} must be a tuple.")
    if not all(isinstance(item, item_type) for item in value):
        raise TypeError(f"{name} must contain only {item_type.__name__} values.")


class TypeDefinition:
    """Marker base for normalized declarative logical types."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class StringTypeDefinition(TypeDefinition):
    """Declarative string logical type."""


@dataclass(frozen=True, slots=True)
class BooleanTypeDefinition(TypeDefinition):
    """Declarative boolean logical type."""


@dataclass(frozen=True, slots=True)
class IntegerTypeDefinition(TypeDefinition):
    """Declarative integer logical type."""

    bits: int = 64
    signed: bool = True

    def __post_init__(self) -> None:
        _require_int(self.bits, name="bits")
        _require_bool(self.signed, name="signed")
        if self.bits not in _INTEGER_BITS:
            raise ValueError(f"bits must be one of {sorted(_INTEGER_BITS)!r}.")


@dataclass(frozen=True, slots=True)
class FloatTypeDefinition(TypeDefinition):
    """Declarative floating-point logical type."""

    bits: int = 64

    def __post_init__(self) -> None:
        _require_int(self.bits, name="bits")
        if self.bits not in _FLOAT_BITS:
            raise ValueError(f"bits must be one of {sorted(_FLOAT_BITS)!r}.")


@dataclass(frozen=True, slots=True)
class DecimalTypeDefinition(TypeDefinition):
    """Declarative fixed-precision decimal logical type."""

    precision: int
    scale: int

    def __post_init__(self) -> None:
        _require_int(self.precision, name="precision")
        _require_int(self.scale, name="scale")
        if self.precision <= 0:
            raise ValueError("precision must be greater than zero.")
        if self.scale < 0:
            raise ValueError("scale must be non-negative.")
        if self.scale > self.precision:
            raise ValueError("scale must not exceed precision.")


@dataclass(frozen=True, slots=True)
class BinaryTypeDefinition(TypeDefinition):
    """Declarative binary logical type."""


@dataclass(frozen=True, slots=True)
class DateTypeDefinition(TypeDefinition):
    """Declarative date logical type."""


@dataclass(frozen=True, slots=True)
class TimeTypeDefinition(TypeDefinition):
    """Declarative time logical type."""

    unit: str = "us"

    def __post_init__(self) -> None:
        _require_non_blank_text(self.unit, name="unit")
        if self.unit not in _TIME_UNITS:
            raise ValueError(f"unit must be one of {sorted(_TIME_UNITS)!r}.")


@dataclass(frozen=True, slots=True)
class TimestampTypeDefinition(TypeDefinition):
    """Declarative timestamp logical type."""

    unit: str = "us"
    timezone: str | None = None

    def __post_init__(self) -> None:
        _require_non_blank_text(self.unit, name="unit")
        if self.unit not in _TIME_UNITS:
            raise ValueError(f"unit must be one of {sorted(_TIME_UNITS)!r}.")
        if self.timezone is not None:
            _require_non_blank_text(self.timezone, name="timezone")


@dataclass(frozen=True, slots=True)
class DurationTypeDefinition(TypeDefinition):
    """Declarative duration logical type."""

    unit: str = "us"

    def __post_init__(self) -> None:
        _require_non_blank_text(self.unit, name="unit")
        if self.unit not in _TIME_UNITS:
            raise ValueError(f"unit must be one of {sorted(_TIME_UNITS)!r}.")


@dataclass(frozen=True, slots=True)
class UnknownTypeDefinition(TypeDefinition):
    """Intentional unknown logical type, never a parse-error fallback."""


@dataclass(frozen=True, slots=True)
class ListTypeDefinition(TypeDefinition):
    """Declarative list logical type."""

    element_type: TypeDefinition
    element_nullable: bool = True

    def __post_init__(self) -> None:
        _require_type_definition(self.element_type, name="element_type")
        _require_bool(self.element_nullable, name="element_nullable")


@dataclass(frozen=True, slots=True)
class StructFieldDefinition:
    """Declarative nested struct field."""

    name: str
    data_type: TypeDefinition
    nullable: bool = True

    def __post_init__(self) -> None:
        _require_non_blank_text(self.name, name="name")
        _require_type_definition(self.data_type, name="data_type")
        _require_bool(self.nullable, name="nullable")


@dataclass(frozen=True, slots=True)
class StructTypeDefinition(TypeDefinition):
    """Declarative struct logical type."""

    fields: tuple[StructFieldDefinition, ...]

    def __post_init__(self) -> None:
        _require_tuple_items(
            self.fields,
            name="fields",
            item_type=StructFieldDefinition,
        )


@dataclass(frozen=True, slots=True)
class MapTypeDefinition(TypeDefinition):
    """Declarative map logical type."""

    key_type: TypeDefinition
    value_type: TypeDefinition
    value_nullable: bool = True

    def __post_init__(self) -> None:
        _require_type_definition(self.key_type, name="key_type")
        _require_type_definition(self.value_type, name="value_type")
        _require_bool(self.value_nullable, name="value_nullable")


@dataclass(frozen=True, slots=True)
class FieldDefinition:
    """Declarative top-level schema field."""

    name: str
    data_type: TypeDefinition
    nullable: bool = True
    description: str | None = None

    def __post_init__(self) -> None:
        _require_non_blank_text(self.name, name="name")
        _require_type_definition(self.data_type, name="data_type")
        _require_bool(self.nullable, name="nullable")
        if self.description is not None:
            _require_non_blank_text(self.description, name="description")


@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    """One named declarative schema definition."""

    name: str
    fields: tuple[FieldDefinition, ...]

    def __post_init__(self) -> None:
        _require_non_blank_text(self.name, name="name")
        _require_tuple_items(
            self.fields,
            name="fields",
            item_type=FieldDefinition,
        )


@dataclass(frozen=True, slots=True)
class SchemaDocument:
    """Format-neutral root for one declarative schema document."""

    version: int
    schemas: tuple[SchemaDefinition, ...]

    def __post_init__(self) -> None:
        _require_int(self.version, name="version")
        _require_tuple_items(
            self.schemas,
            name="schemas",
            item_type=SchemaDefinition,
        )
