"""Base logical Transformation contract."""

from typing import ClassVar

from pytransformkit.domain.transformations.properties import (
    TransformationProperties,
)


class TransformationSpec:
    """Marker base for immutable logical Transformation specifications."""

    __slots__ = ()

    identifier: ClassVar[str]
    properties: ClassVar[TransformationProperties]
