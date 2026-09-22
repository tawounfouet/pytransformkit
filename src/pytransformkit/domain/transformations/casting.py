"""Logical type-conversion Transformation."""

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from pytransformkit.domain.data.data_types import DataType
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


class CastPolicy(StrEnum):
    RAISE = "raise"
    NULL = "null"
    COERCE = "coerce"


@dataclass(frozen=True, slots=True)
class CastTransformation(TransformationSpec):
    """Cast one logical field to another logical DataType."""

    field: FieldPath
    target_type: DataType
    policy: CastPolicy = CastPolicy.RAISE

    identifier: ClassVar[str] = "core.cast"
    properties: ClassVar[TransformationProperties] = TransformationProperties(
        determinism=Determinism.DETERMINISTIC,
        portability=Portability.PORTABLE,
        purity=Purity.PURE,
        cardinality=CardinalityEffect.PRESERVE,
        schema=SchemaEffect.MODIFY,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.field, FieldPath):
            raise TypeError("Cast field must be a FieldPath.")
        if not isinstance(self.target_type, DataType):
            raise TypeError("Cast target_type must be a DataType.")
        if not isinstance(self.policy, CastPolicy):
            raise TypeError("Cast policy must be a CastPolicy.")
