"""Engine-neutral data-quality rule declarations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.quality.results import (
    ValidationPolicy,
    ValidationThreshold,
)


class ValidationRule:
    """Marker base class for immutable logical validation rules."""

    __slots__ = ()

    identifier: ClassVar[str]
    name: str
    threshold: ValidationThreshold


@dataclass(frozen=True, slots=True)
class NotNull(ValidationRule):
    name: str
    field: FieldPath
    threshold: ValidationThreshold = ValidationThreshold()

    identifier: ClassVar[str] = "quality.not_null"

    def __post_init__(self) -> None:
        _validate_rule_name(self.name)
        _validate_field(self.field)


@dataclass(frozen=True, slots=True)
class Unique(ValidationRule):
    name: str
    fields: tuple[FieldPath, ...]
    threshold: ValidationThreshold = ValidationThreshold()

    identifier: ClassVar[str] = "quality.unique"

    def __post_init__(self) -> None:
        _validate_rule_name(self.name)
        if not isinstance(self.fields, tuple):
            raise TypeError("Unique fields must be provided as a tuple.")
        if not self.fields:
            raise ValueError("Unique requires at least one field.")
        if any(not isinstance(field, FieldPath) for field in self.fields):
            raise TypeError("Unique fields must contain FieldPath values.")
        if len(set(self.fields)) != len(self.fields):
            raise ValueError("Unique fields must be unique.")


@dataclass(frozen=True, slots=True)
class Range(ValidationRule):
    name: str
    field: FieldPath
    minimum: object | None = None
    maximum: object | None = None
    include_minimum: bool = True
    include_maximum: bool = True
    threshold: ValidationThreshold = ValidationThreshold()

    identifier: ClassVar[str] = "quality.range"

    def __post_init__(self) -> None:
        _validate_rule_name(self.name)
        _validate_field(self.field)
        if self.minimum is None and self.maximum is None:
            raise ValueError("Range requires minimum, maximum, or both.")


@dataclass(frozen=True, slots=True)
class AllowedValues(ValidationRule):
    name: str
    field: FieldPath
    values: tuple[object, ...]
    threshold: ValidationThreshold = ValidationThreshold()

    identifier: ClassVar[str] = "quality.allowed_values"

    def __post_init__(self) -> None:
        _validate_rule_name(self.name)
        _validate_field(self.field)
        if not isinstance(self.values, tuple):
            raise TypeError("AllowedValues values must be provided as a tuple.")
        if not self.values:
            raise ValueError("AllowedValues requires at least one allowed value.")


@dataclass(frozen=True, slots=True)
class Regex(ValidationRule):
    name: str
    field: FieldPath
    pattern: str
    threshold: ValidationThreshold = ValidationThreshold()

    identifier: ClassVar[str] = "quality.regex"

    def __post_init__(self) -> None:
        _validate_rule_name(self.name)
        _validate_field(self.field)
        if not self.pattern:
            raise ValueError("Regex pattern must not be empty.")
        re.compile(self.pattern)


@dataclass(frozen=True, slots=True)
class SchemaValidation(ValidationRule):
    name: str
    expected_schema: Schema
    exact: bool = True
    threshold: ValidationThreshold = ValidationThreshold()

    identifier: ClassVar[str] = "quality.schema"

    def __post_init__(self) -> None:
        _validate_rule_name(self.name)
        if not isinstance(self.expected_schema, Schema):
            raise TypeError("expected_schema must be a Schema.")


@dataclass(frozen=True, slots=True)
class RowCount(ValidationRule):
    name: str
    minimum: int | None = None
    maximum: int | None = None
    threshold: ValidationThreshold = ValidationThreshold()

    identifier: ClassVar[str] = "quality.row_count"

    def __post_init__(self) -> None:
        _validate_rule_name(self.name)
        if self.minimum is None and self.maximum is None:
            raise ValueError("RowCount requires minimum, maximum, or both.")
        for value, label in (
            (self.minimum, "minimum"),
            (self.maximum, "maximum"),
        ):
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 0
            ):
                raise ValueError(f"RowCount {label} must be a non-negative integer.")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("RowCount minimum must not exceed maximum.")


@dataclass(frozen=True, slots=True)
class ExpressionValidation(ValidationRule):
    name: str
    expression: Expression
    threshold: ValidationThreshold = ValidationThreshold()

    identifier: ClassVar[str] = "quality.expression"

    def __post_init__(self) -> None:
        _validate_rule_name(self.name)
        if not isinstance(self.expression, Expression):
            raise TypeError("ExpressionValidation expression must be an Expression.")


@dataclass(frozen=True, slots=True)
class ValidationSpec:
    """Immutable ordered quality rule set."""

    name: str
    rules: tuple[ValidationRule, ...]
    policy: ValidationPolicy = ValidationPolicy.FAIL_FAST

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("ValidationSpec name must not be empty.")
        if not isinstance(self.rules, tuple):
            raise TypeError("ValidationSpec rules must be provided as a tuple.")
        if not self.rules:
            raise ValueError("ValidationSpec requires at least one rule.")
        if any(not isinstance(rule, ValidationRule) for rule in self.rules):
            raise TypeError("ValidationSpec rules must contain ValidationRule values.")
        names = tuple(rule.name for rule in self.rules)
        if len(names) != len(set(names)):
            raise ValueError("ValidationSpec rule names must be unique.")
        if not isinstance(self.policy, ValidationPolicy):
            raise TypeError("ValidationSpec policy must be a ValidationPolicy.")


def _validate_rule_name(name: str) -> None:
    if not name or not name.strip():
        raise ValueError("Validation rule name must not be empty.")


def _validate_field(field: FieldPath) -> None:
    if not isinstance(field, FieldPath):
        raise TypeError("Validation rule field must be a FieldPath.")
