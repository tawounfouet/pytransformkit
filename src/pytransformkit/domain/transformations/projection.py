"""Projection-oriented logical Transformations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
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

_PROJECT_PROPERTIES = TransformationProperties(
    determinism=Determinism.DETERMINISTIC,
    portability=Portability.PORTABLE,
    purity=Purity.PURE,
    cardinality=CardinalityEffect.PRESERVE,
    schema=SchemaEffect.PROJECT,
)

_MODIFY_PROPERTIES = TransformationProperties(
    determinism=Determinism.DETERMINISTIC,
    portability=Portability.PORTABLE,
    purity=Purity.PURE,
    cardinality=CardinalityEffect.PRESERVE,
    schema=SchemaEffect.MODIFY,
)


@dataclass(frozen=True, slots=True)
class SelectTransformation(TransformationSpec):
    """Keep only selected logical fields in the requested order."""

    fields: tuple[FieldPath, ...]

    identifier: ClassVar[str] = "core.select"
    properties: ClassVar[TransformationProperties] = _PROJECT_PROPERTIES

    def __post_init__(self) -> None:
        _validate_field_paths(self.fields, "Select")


@dataclass(frozen=True, slots=True)
class DropTransformation(TransformationSpec):
    """Remove selected logical fields."""

    fields: tuple[FieldPath, ...]

    identifier: ClassVar[str] = "core.drop"
    properties: ClassVar[TransformationProperties] = _PROJECT_PROPERTIES

    def __post_init__(self) -> None:
        _validate_field_paths(self.fields, "Drop")


@dataclass(frozen=True, slots=True)
class RenameField:
    """One immutable field rename."""

    source: FieldPath
    target: str

    def __post_init__(self) -> None:
        if not isinstance(self.source, FieldPath):
            raise TypeError("Rename source must be a FieldPath.")
        if not self.target or not self.target.strip():
            raise InvalidTransformationError(
                "Rename target must not be empty."
            )


@dataclass(frozen=True, slots=True)
class RenameTransformation(TransformationSpec):
    """Rename logical fields simultaneously."""

    renames: tuple[RenameField, ...]

    identifier: ClassVar[str] = "core.rename"
    properties: ClassVar[TransformationProperties] = _MODIFY_PROPERTIES

    def __post_init__(self) -> None:
        if not isinstance(self.renames, tuple):
            raise TypeError("Rename entries must be provided as a tuple.")
        if not self.renames:
            raise InvalidTransformationError(
                "Rename requires at least one field."
            )
        if any(not isinstance(item, RenameField) for item in self.renames):
            raise TypeError("Rename entries must contain only RenameField values.")

        sources = tuple(item.source for item in self.renames)
        targets = tuple(item.target for item in self.renames)
        if len(set(sources)) != len(sources):
            raise InvalidTransformationError(
                "Rename sources must be unique."
            )
        if len(set(targets)) != len(targets):
            raise InvalidTransformationError(
                "Rename targets must be unique."
            )

    @classmethod
    def from_mapping(
        cls,
        mapping: Mapping[str, str],
    ) -> RenameTransformation:
        return cls(
            tuple(
                RenameField(
                    source=FieldPath.of(source),
                    target=target,
                )
                for source, target in mapping.items()
            )
        )


def _validate_field_paths(
    fields: tuple[FieldPath, ...],
    operation: str,
) -> None:
    if not isinstance(fields, tuple):
        raise TypeError(f"{operation} fields must be provided as a tuple.")
    if any(not isinstance(field, FieldPath) for field in fields):
        raise TypeError(f"{operation} fields must contain only FieldPath values.")
    if len(set(fields)) != len(fields):
        raise InvalidTransformationError(
            f"{operation} fields must be unique."
        )
