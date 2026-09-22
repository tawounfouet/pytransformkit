"""Row-selection logical Transformations."""

from dataclasses import dataclass
from typing import ClassVar

from pytransformkit.domain.expressions.base import Expression
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

_FILTER_PROPERTIES = TransformationProperties(
    determinism=Determinism.DETERMINISTIC,
    portability=Portability.PORTABLE,
    purity=Purity.PURE,
    cardinality=CardinalityEffect.REDUCE,
    schema=SchemaEffect.PRESERVE,
)


@dataclass(frozen=True, slots=True)
class FilterTransformation(TransformationSpec):
    """Keep rows for which the logical condition evaluates to TRUE."""

    condition: Expression

    identifier: ClassVar[str] = "core.filter"
    properties: ClassVar[TransformationProperties] = _FILTER_PROPERTIES

    def __post_init__(self) -> None:
        if not isinstance(self.condition, Expression):
            raise TypeError("Filter condition must be an Expression.")


@dataclass(frozen=True, slots=True)
class LimitTransformation(TransformationSpec):
    """Limit output cardinality to at most count rows."""

    count: int

    identifier: ClassVar[str] = "core.limit"
    properties: ClassVar[TransformationProperties] = _FILTER_PROPERTIES

    def __post_init__(self) -> None:
        if isinstance(self.count, bool) or not isinstance(self.count, int):
            raise TypeError("Limit count must be an integer.")
        if self.count < 0:
            raise InvalidTransformationError("Limit count must be non-negative.")


@dataclass(frozen=True, slots=True)
class DistinctTransformation(TransformationSpec):
    """Remove duplicate rows using all logical fields."""

    identifier: ClassVar[str] = "core.distinct"
    properties: ClassVar[TransformationProperties] = _FILTER_PROPERTIES
