"""Portable multi-input relational Transformations."""

from __future__ import annotations

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


class JoinType(StrEnum):
    """Portable relational join semantics."""

    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"
    SEMI = "semi"
    ANTI = "anti"
    CROSS = "cross"


class NullJoinPolicy(StrEnum):
    """How NULL join keys participate in equality joins."""

    MATCH = "match"
    NEVER_MATCH = "never_match"


@dataclass(frozen=True, slots=True)
class JoinKey:
    """One explicit equality relation between left and right fields."""

    left: FieldPath
    right: FieldPath

    def __post_init__(self) -> None:
        if not isinstance(self.left, FieldPath):
            raise TypeError("Join left key must be a FieldPath.")
        if not isinstance(self.right, FieldPath):
            raise TypeError("Join right key must be a FieldPath.")

    @classmethod
    def of(cls, left: str, right: str | None = None) -> "JoinKey":
        return cls(
            left=FieldPath.of(left),
            right=FieldPath.of(right if right is not None else left),
        )


_RELATIONAL_PROPERTIES = TransformationProperties(
    determinism=Determinism.DETERMINISTIC,
    portability=Portability.PORTABLE,
    purity=Purity.PURE,
    cardinality=CardinalityEffect.UNKNOWN,
    schema=SchemaEffect.MODIFY,
)

_SET_PROPERTIES = TransformationProperties(
    determinism=Determinism.DETERMINISTIC,
    portability=Portability.PORTABLE,
    purity=Purity.PURE,
    cardinality=CardinalityEffect.UNKNOWN,
    schema=SchemaEffect.PRESERVE,
)


@dataclass(frozen=True, slots=True)
class JoinTransformation(TransformationSpec):
    """Join two logical inputs using explicit portable semantics."""

    keys: tuple[JoinKey, ...] = ()
    how: JoinType = JoinType.INNER
    nulls: NullJoinPolicy = NullJoinPolicy.MATCH
    right_suffix: str = "_right"

    identifier: ClassVar[str] = "core.join"
    properties: ClassVar[TransformationProperties] = _RELATIONAL_PROPERTIES

    def __post_init__(self) -> None:
        if not isinstance(self.keys, tuple):
            raise TypeError("Join keys must be provided as a tuple.")
        if any(not isinstance(key, JoinKey) for key in self.keys):
            raise TypeError("Join keys must contain only JoinKey values.")
        if not isinstance(self.how, JoinType):
            raise TypeError("Join how must be a JoinType.")
        if not isinstance(self.nulls, NullJoinPolicy):
            raise TypeError("Join nulls must be a NullJoinPolicy.")
        if self.how is JoinType.CROSS:
            if self.keys:
                raise InvalidTransformationError(
                    "Cross join must not declare equality keys."
                )
        elif not self.keys:
            raise InvalidTransformationError(
                "Non-cross joins require at least one equality key."
            )
        if len(set(self.keys)) != len(self.keys):
            raise InvalidTransformationError("Join keys must be unique.")
        if not self.right_suffix:
            raise InvalidTransformationError("Join right_suffix must not be empty.")


@dataclass(frozen=True, slots=True)
class UnionTransformation(TransformationSpec):
    """Combine two compatible inputs, optionally preserving duplicates."""

    all: bool = False

    identifier: ClassVar[str] = "core.union"
    properties: ClassVar[TransformationProperties] = _SET_PROPERTIES

    def __post_init__(self) -> None:
        if not isinstance(self.all, bool):
            raise TypeError("Union all must be a bool.")


@dataclass(frozen=True, slots=True)
class IntersectTransformation(TransformationSpec):
    """Return distinct rows present in both compatible inputs."""

    identifier: ClassVar[str] = "core.intersect"
    properties: ClassVar[TransformationProperties] = _SET_PROPERTIES


@dataclass(frozen=True, slots=True)
class ExceptTransformation(TransformationSpec):
    """Return distinct left rows absent from the right compatible input."""

    identifier: ClassVar[str] = "core.except"
    properties: ClassVar[TransformationProperties] = _SET_PROPERTIES


RELATIONAL_TRANSFORMATION_TYPES = (
    JoinTransformation,
    UnionTransformation,
    IntersectTransformation,
    ExceptTransformation,
)


def relational_input_count(transformation: TransformationSpec) -> int:
    """Return the required logical input count for one Transformation."""
    if isinstance(transformation, RELATIONAL_TRANSFORMATION_TYPES):
        return 2
    return 1
