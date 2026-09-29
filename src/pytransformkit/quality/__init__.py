"""Public data-quality authoring surface."""

from __future__ import annotations

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.quality import (
    AllowedValues,
    ExpressionValidation,
    NotNull,
    Range,
    Regex,
    RowCount,
    SchemaValidation,
    Unique,
    ValidationPolicy,
    ValidationResult,
    ValidationRule,
    ValidationRuleResult,
    ValidationSpec,
    ValidationThreshold,
)


def not_null(
    field: str,
    *,
    name: str | None = None,
    threshold: ValidationThreshold = ValidationThreshold(),
) -> NotNull:
    return NotNull(
        name=name or f"{field}.not_null",
        field=FieldPath.of(field),
        threshold=threshold,
    )


def unique(
    *fields: str,
    name: str | None = None,
    threshold: ValidationThreshold = ValidationThreshold(),
) -> Unique:
    if not fields:
        raise ValueError("quality.unique requires at least one field.")
    joined = ",".join(fields)
    return Unique(
        name=name or f"{joined}.unique",
        fields=tuple(FieldPath.of(field) for field in fields),
        threshold=threshold,
    )


def range_(
    field: str,
    *,
    minimum: object | None = None,
    maximum: object | None = None,
    include_minimum: bool = True,
    include_maximum: bool = True,
    name: str | None = None,
    threshold: ValidationThreshold = ValidationThreshold(),
) -> Range:
    return Range(
        name=name or f"{field}.range",
        field=FieldPath.of(field),
        minimum=minimum,
        maximum=maximum,
        include_minimum=include_minimum,
        include_maximum=include_maximum,
        threshold=threshold,
    )


def allowed_values(
    field: str,
    values: tuple[object, ...],
    *,
    name: str | None = None,
    threshold: ValidationThreshold = ValidationThreshold(),
) -> AllowedValues:
    return AllowedValues(
        name=name or f"{field}.allowed_values",
        field=FieldPath.of(field),
        values=values,
        threshold=threshold,
    )


def regex(
    field: str,
    pattern: str,
    *,
    name: str | None = None,
    threshold: ValidationThreshold = ValidationThreshold(),
) -> Regex:
    return Regex(
        name=name or f"{field}.regex",
        field=FieldPath.of(field),
        pattern=pattern,
        threshold=threshold,
    )


def schema(
    expected_schema: Schema,
    *,
    exact: bool = True,
    name: str = "schema",
    threshold: ValidationThreshold = ValidationThreshold(),
) -> SchemaValidation:
    return SchemaValidation(
        name=name,
        expected_schema=expected_schema,
        exact=exact,
        threshold=threshold,
    )


def row_count(
    *,
    minimum: int | None = None,
    maximum: int | None = None,
    name: str = "row_count",
    threshold: ValidationThreshold = ValidationThreshold(),
) -> RowCount:
    return RowCount(
        name=name,
        minimum=minimum,
        maximum=maximum,
        threshold=threshold,
    )


def expression(
    condition: Expression,
    *,
    name: str,
    threshold: ValidationThreshold = ValidationThreshold(),
) -> ExpressionValidation:
    return ExpressionValidation(
        name=name,
        expression=condition,
        threshold=threshold,
    )


__all__ = [
    "AllowedValues",
    "ExpressionValidation",
    "NotNull",
    "Range",
    "Regex",
    "RowCount",
    "SchemaValidation",
    "Unique",
    "ValidationPolicy",
    "ValidationResult",
    "ValidationRule",
    "ValidationRuleResult",
    "ValidationSpec",
    "ValidationThreshold",
    "allowed_values",
    "expression",
    "not_null",
    "range_",
    "regex",
    "row_count",
    "schema",
    "unique",
]
