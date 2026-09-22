"""Logical deduplication Transformation."""

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


class DeduplicationStrategy(StrEnum):
    FIRST = "first"
    LAST = "last"


@dataclass(frozen=True, slots=True)
class DeduplicateTransformation(TransformationSpec):
    """Remove duplicate rows using explicit logical key fields."""

    keys: tuple[FieldPath, ...]
    keep: DeduplicationStrategy = DeduplicationStrategy.FIRST

    identifier: ClassVar[str] = "core.deduplicate"
    properties: ClassVar[TransformationProperties] = TransformationProperties(
        determinism=Determinism.DETERMINISTIC,
        portability=Portability.PORTABLE,
        purity=Purity.PURE,
        cardinality=CardinalityEffect.REDUCE,
        schema=SchemaEffect.PRESERVE,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.keys, tuple):
            raise TypeError("Deduplication keys must be provided as a tuple.")
        if not self.keys:
            raise InvalidTransformationError(
                "Deduplication requires at least one key."
            )
        if any(not isinstance(key, FieldPath) for key in self.keys):
            raise TypeError(
                "Deduplication keys must contain only FieldPath values."
            )
        if len(set(self.keys)) != len(self.keys):
            raise InvalidTransformationError(
                "Deduplication keys must be unique."
            )
        if not isinstance(self.keep, DeduplicationStrategy):
            raise TypeError(
                "Deduplication keep must be a DeduplicationStrategy."
            )
