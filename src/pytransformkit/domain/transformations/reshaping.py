"""Portable reshaping Transformations."""

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.transformations.base import TransformationSpec
from pytransformkit.domain.transformations.properties import (
    CardinalityEffect,
    Determinism,
    Portability,
    Purity,
    SchemaEffect,
    TransformationProperties,
)
from pytransformkit.errors.transformation import InvalidTransformationError


class PivotAggregation(StrEnum):
    """Portable aggregation applied while pivoting duplicate cells."""

    SUM = "sum"
    MIN = "min"
    MAX = "max"
    MEAN = "mean"
    COUNT = "count"


@dataclass(frozen=True, slots=True)
class PivotTransformation(TransformationSpec):
    """Pivot one categorical field into explicitly declared output columns."""

    index: tuple[FieldPath, ...]
    columns: FieldPath
    values: FieldPath
    categories: tuple[str, ...]
    aggregation: PivotAggregation

    identifier: ClassVar[str] = "core.pivot"
    properties: ClassVar[TransformationProperties] = TransformationProperties(
        determinism=Determinism.DETERMINISTIC,
        portability=Portability.PORTABLE,
        purity=Purity.PURE,
        cardinality=CardinalityEffect.REDUCE,
        schema=SchemaEffect.MODIFY,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.index, tuple):
            raise TypeError("Pivot index must be provided as a tuple.")
        if any(not isinstance(field, FieldPath) for field in self.index):
            raise TypeError("Pivot index must contain only FieldPath values.")
        if not isinstance(self.columns, FieldPath):
            raise TypeError("Pivot columns must be a FieldPath.")
        if not isinstance(self.values, FieldPath):
            raise TypeError("Pivot values must be a FieldPath.")
        if not isinstance(self.categories, tuple):
            raise TypeError("Pivot categories must be provided as a tuple.")
        if not self.categories:
            raise InvalidTransformationError(
                "Pivot requires at least one explicit category."
            )
        if any(
            not isinstance(value, str) or not value.strip() for value in self.categories
        ):
            raise InvalidTransformationError(
                "Pivot categories must be non-empty strings."
            )
        if len(set(self.categories)) != len(self.categories):
            raise InvalidTransformationError("Pivot categories must be unique.")
        if not isinstance(self.aggregation, PivotAggregation):
            raise TypeError("Pivot aggregation must be a PivotAggregation.")


@dataclass(frozen=True, slots=True)
class UnpivotTransformation(TransformationSpec):
    """Convert explicitly selected value columns into name/value rows."""

    id_vars: tuple[FieldPath, ...]
    value_vars: tuple[FieldPath, ...]
    variable_name: str = "variable"
    value_name: str = "value"

    identifier: ClassVar[str] = "core.unpivot"
    properties: ClassVar[TransformationProperties] = TransformationProperties(
        determinism=Determinism.DETERMINISTIC,
        portability=Portability.PORTABLE,
        purity=Purity.PURE,
        cardinality=CardinalityEffect.EXPAND,
        schema=SchemaEffect.MODIFY,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.id_vars, tuple):
            raise TypeError("Unpivot id_vars must be provided as a tuple.")
        if not isinstance(self.value_vars, tuple):
            raise TypeError("Unpivot value_vars must be provided as a tuple.")
        if any(not isinstance(field, FieldPath) for field in self.id_vars):
            raise TypeError("Unpivot id_vars must contain FieldPath values.")
        if any(not isinstance(field, FieldPath) for field in self.value_vars):
            raise TypeError("Unpivot value_vars must contain FieldPath values.")
        if not self.value_vars:
            raise InvalidTransformationError(
                "Unpivot requires at least one value field."
            )
        if len(set(self.id_vars)) != len(self.id_vars):
            raise InvalidTransformationError("Unpivot id_vars must be unique.")
        if len(set(self.value_vars)) != len(self.value_vars):
            raise InvalidTransformationError("Unpivot value_vars must be unique.")
        if set(self.id_vars) & set(self.value_vars):
            raise InvalidTransformationError(
                "Unpivot id_vars and value_vars must not overlap."
            )
        if not self.variable_name or not self.variable_name.strip():
            raise InvalidTransformationError("Unpivot variable_name must not be empty.")
        if not self.value_name or not self.value_name.strip():
            raise InvalidTransformationError("Unpivot value_name must not be empty.")
        if self.variable_name == self.value_name:
            raise InvalidTransformationError(
                "Unpivot variable_name and value_name must differ."
            )


@dataclass(frozen=True, slots=True)
class ExplodeTransformation(TransformationSpec):
    """Expand one top-level List field into one row per element."""

    field: FieldPath

    identifier: ClassVar[str] = "core.explode"
    properties: ClassVar[TransformationProperties] = TransformationProperties(
        determinism=Determinism.DETERMINISTIC,
        portability=Portability.PORTABLE,
        purity=Purity.PURE,
        cardinality=CardinalityEffect.EXPAND,
        schema=SchemaEffect.MODIFY,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.field, FieldPath):
            raise TypeError("Explode field must be a FieldPath.")
        if len(self.field.parts) != 1:
            raise InvalidTransformationError(
                "Explode currently requires a top-level List field."
            )


@dataclass(frozen=True, slots=True)
class FlattenTransformation(TransformationSpec):
    """Expand one top-level Struct field into prefixed top-level fields."""

    field: FieldPath
    prefix: str | None = None

    identifier: ClassVar[str] = "core.flatten"
    properties: ClassVar[TransformationProperties] = TransformationProperties(
        determinism=Determinism.DETERMINISTIC,
        portability=Portability.PORTABLE,
        purity=Purity.PURE,
        cardinality=CardinalityEffect.PRESERVE,
        schema=SchemaEffect.MODIFY,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.field, FieldPath):
            raise TypeError("Flatten field must be a FieldPath.")
        if len(self.field.parts) != 1:
            raise InvalidTransformationError(
                "Flatten currently requires a top-level Struct field."
            )
        if self.prefix is not None and not self.prefix:
            raise InvalidTransformationError(
                "Flatten prefix must be non-empty when provided."
            )

    def output_name(self, nested_name: str) -> str:
        prefix = self.prefix if self.prefix is not None else f"{self.field.name}_"
        return f"{prefix}{nested_name}"
