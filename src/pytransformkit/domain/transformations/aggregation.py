"""Portable aggregation Transformation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from pytransformkit.domain.expressions.aggregate import AggregateExpression
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


@dataclass(frozen=True, slots=True)
class AggregateMetric:
    """One named aggregate output."""

    name: str
    expression: AggregateExpression

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidTransformationError(
                "Aggregate metric name must not be empty."
            )
        if not isinstance(self.expression, AggregateExpression):
            raise TypeError(
                "Aggregate metric expression must be an AggregateExpression."
            )


@dataclass(frozen=True, slots=True)
class AggregateTransformation(TransformationSpec):
    """Group rows and compute named aggregate metrics."""

    group_by: tuple[Expression, ...]
    metrics: tuple[AggregateMetric, ...]

    identifier: ClassVar[str] = "core.aggregate"
    properties: ClassVar[TransformationProperties] = TransformationProperties(
        determinism=Determinism.DETERMINISTIC,
        portability=Portability.PORTABLE,
        purity=Purity.PURE,
        cardinality=CardinalityEffect.REDUCE,
        schema=SchemaEffect.MODIFY,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.group_by, tuple):
            raise TypeError("Aggregate group_by must be provided as a tuple.")
        if any(not isinstance(item, Expression) for item in self.group_by):
            raise TypeError(
                "Aggregate group_by must contain only Expression values."
            )
        if not isinstance(self.metrics, tuple):
            raise TypeError("Aggregate metrics must be provided as a tuple.")
        if not self.metrics:
            raise InvalidTransformationError(
                "AggregateTransformation requires at least one metric."
            )
        if any(not isinstance(item, AggregateMetric) for item in self.metrics):
            raise TypeError(
                "Aggregate metrics must contain only AggregateMetric values."
            )

        metric_names = tuple(metric.name for metric in self.metrics)
        if len(metric_names) != len(set(metric_names)):
            raise InvalidTransformationError(
                "Aggregate metric names must be unique."
            )

    @classmethod
    def from_mapping(
        cls,
        *,
        group_by: tuple[Expression, ...],
        metrics: Mapping[str, AggregateExpression],
    ) -> AggregateTransformation:
        return cls(
            group_by=group_by,
            metrics=tuple(
                AggregateMetric(name, expression)
                for name, expression in metrics.items()
            ),
        )
