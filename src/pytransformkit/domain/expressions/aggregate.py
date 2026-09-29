"""Aggregate logical Expressions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.domain.expressions.base import Expression


class AggregateFunction(StrEnum):
    """Portable aggregate functions qualified by LOT-12."""

    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    MEAN = "mean"


@dataclass(frozen=True, slots=True, eq=False)
class AggregateExpression(Expression):
    """One aggregate function applied to an optional row Expression."""

    function: AggregateFunction
    argument: Expression | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.function, AggregateFunction):
            raise TypeError(
                "AggregateExpression function must be an AggregateFunction."
            )
        if self.argument is not None and not isinstance(self.argument, Expression):
            raise TypeError("AggregateExpression argument must be an Expression.")
        if self.function is not AggregateFunction.COUNT and self.argument is None:
            raise ValueError(f"{self.function.value} requires an aggregate argument.")
