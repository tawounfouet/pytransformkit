"""Logical field derivation Transformation."""

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


@dataclass(frozen=True, slots=True)
class DeriveTransformation(TransformationSpec):
    """Create or explicitly replace a logical field from an Expression."""

    field_name: str
    expression: Expression
    replace_existing: bool = False

    identifier: ClassVar[str] = "core.derive"
    properties: ClassVar[TransformationProperties] = TransformationProperties(
        determinism=Determinism.DETERMINISTIC,
        portability=Portability.PORTABLE,
        purity=Purity.PURE,
        cardinality=CardinalityEffect.PRESERVE,
        schema=SchemaEffect.EXTEND,
    )

    def __post_init__(self) -> None:
        if not self.field_name or not self.field_name.strip():
            raise InvalidTransformationError("Derived field name must not be empty.")
        if not isinstance(self.expression, Expression):
            raise TypeError("Derived field expression must be an Expression.")
