"""Immutable logical Schema model."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, replace

from pytransformkit.domain.data.field import Field
from pytransformkit.errors.schema import (
    DuplicateFieldError,
    FieldCollisionError,
    FieldNotFoundError,
)


@dataclass(frozen=True, slots=True)
class Schema:
    """Ordered immutable collection of uniquely named logical fields."""

    fields: tuple[Field, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.fields, tuple):
            raise TypeError("Schema fields must be provided as a tuple.")

        seen: set[str] = set()
        for field in self.fields:
            if not isinstance(field, Field):
                raise TypeError("Schema fields must contain only Field instances.")
            if field.name in seen:
                raise DuplicateFieldError(field.name)
            seen.add(field.name)

    def __iter__(self) -> Iterator[Field]:
        return iter(self.fields)

    def __len__(self) -> int:
        return len(self.fields)

    def names(self) -> tuple[str, ...]:
        """Return field names in logical order."""
        return tuple(field.name for field in self.fields)

    def has_field(self, name: str) -> bool:
        """Return whether a field exists using case-sensitive matching."""
        return any(field.name == name for field in self.fields)

    def field(self, name: str) -> Field:
        """Return a field by exact logical name."""
        for field in self.fields:
            if field.name == name:
                return field
        raise FieldNotFoundError(name)

    def select(self, names: tuple[str, ...]) -> Schema:
        """Create a Schema containing fields in the requested order."""
        selected = tuple(self.field(name) for name in names)
        return Schema(selected)

    def drop(self, names: tuple[str, ...]) -> Schema:
        """Create a Schema without the requested fields."""
        for name in names:
            if not self.has_field(name):
                raise FieldNotFoundError(name)

        names_to_drop = set(names)
        return Schema(
            tuple(field for field in self.fields if field.name not in names_to_drop)
        )

    def rename(self, mapping: Mapping[str, str]) -> Schema:
        """Create a Schema with explicitly renamed fields."""
        for source in mapping:
            if not self.has_field(source):
                raise FieldNotFoundError(source)

        renamed_fields = tuple(
            replace(field, name=mapping.get(field.name, field.name))
            for field in self.fields
        )
        renamed_names = tuple(field.name for field in renamed_fields)

        duplicate = _first_duplicate(renamed_names)
        if duplicate is not None:
            raise FieldCollisionError(duplicate)

        return Schema(renamed_fields)

    def append(self, field: Field) -> Schema:
        """Append a new field while protecting unique field names."""
        if self.has_field(field.name):
            raise FieldCollisionError(field.name)
        return Schema(self.fields + (field,))

    def replace(self, field: Field) -> Schema:
        """Replace an existing field while preserving its logical position."""
        if not self.has_field(field.name):
            raise FieldNotFoundError(field.name)

        return Schema(
            tuple(
                field if current.name == field.name else current
                for current in self.fields
            )
        )


def _first_duplicate(values: tuple[str, ...]) -> str | None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None
