"""Transformation-owned quality-gate semantics."""

from dataclasses import dataclass
from typing import ClassVar

from pytransformkit.domain.quality.rules import ValidationSpec
from pytransformkit.domain.transformations.base import TransformationSpec
from pytransformkit.domain.transformations.properties import (
    CardinalityEffect,
    Determinism,
    Portability,
    Purity,
    SchemaEffect,
    TransformationProperties,
)


@dataclass(frozen=True, slots=True)
class QualityGate(TransformationSpec):
    """Validate physical data while preserving its logical rows and Schema."""

    spec: ValidationSpec

    identifier: ClassVar[str] = "core.quality_gate"
    properties: ClassVar[TransformationProperties] = TransformationProperties(
        determinism=Determinism.DETERMINISTIC,
        portability=Portability.PORTABLE,
        purity=Purity.PURE,
        cardinality=CardinalityEffect.PRESERVE,
        schema=SchemaEffect.PRESERVE,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.spec, ValidationSpec):
            raise TypeError("QualityGate spec must be a ValidationSpec.")
