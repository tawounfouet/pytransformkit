"""Logical sorting Transformation."""

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


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class NullOrder(StrEnum):
    FIRST = "first"
    LAST = "last"


@dataclass(frozen=True, slots=True)
class SortKey:
    field: FieldPath
    direction: SortDirection = SortDirection.ASC
    nulls: NullOrder = NullOrder.LAST

    def __post_init__(self) -> None:
        if not isinstance(self.field, FieldPath):
            raise TypeError("Sort field must be a FieldPath.")
        if not isinstance(self.direction, SortDirection):
            raise TypeError("Sort direction must be a SortDirection.")
        if not isinstance(self.nulls, NullOrder):
            raise TypeError("Sort null ordering must be a NullOrder.")


@dataclass(frozen=True, slots=True)
class SortTransformation(TransformationSpec):
    """Sort rows by one or more explicit logical keys."""

    keys: tuple[SortKey, ...]

    identifier: ClassVar[str] = "core.sort"
    properties: ClassVar[TransformationProperties] = TransformationProperties(
        determinism=Determinism.DETERMINISTIC,
        portability=Portability.PORTABLE,
        purity=Purity.PURE,
        cardinality=CardinalityEffect.PRESERVE,
        schema=SchemaEffect.PRESERVE,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.keys, tuple):
            raise TypeError("Sort keys must be provided as a tuple.")
        if not self.keys:
            raise InvalidTransformationError("Sort requires at least one key.")
        if any(not isinstance(key, SortKey) for key in self.keys):
            raise TypeError("Sort keys must contain only SortKey values.")

        fields = tuple(key.field for key in self.keys)
        if len(set(fields)) != len(fields):
            raise InvalidTransformationError("Sort fields must be unique.")
