"""Engine-independent logical Transformation model."""

from pytransformkit.domain.transformations.base import TransformationSpec
from pytransformkit.domain.transformations.casting import (
    CastPolicy,
    CastTransformation,
)
from pytransformkit.domain.transformations.deduplication import (
    DeduplicateTransformation,
    DeduplicationStrategy,
)
from pytransformkit.domain.transformations.derivation import (
    DeriveTransformation,
)
from pytransformkit.domain.transformations.filtering import (
    DistinctTransformation,
    FilterTransformation,
    LimitTransformation,
)
from pytransformkit.domain.transformations.projection import (
    DropTransformation,
    RenameField,
    RenameTransformation,
    SelectTransformation,
)
from pytransformkit.domain.transformations.properties import (
    CardinalityEffect,
    Determinism,
    Portability,
    Purity,
    SchemaEffect,
    TransformationProperties,
)
from pytransformkit.domain.transformations.schema_resolution import (
    OutputSchemaResolver,
)
from pytransformkit.domain.transformations.sorting import (
    NullOrder,
    SortDirection,
    SortKey,
    SortTransformation,
)

__all__ = [
    "CardinalityEffect",
    "CastPolicy",
    "CastTransformation",
    "DeduplicateTransformation",
    "DeduplicationStrategy",
    "DeriveTransformation",
    "Determinism",
    "DistinctTransformation",
    "DropTransformation",
    "FilterTransformation",
    "LimitTransformation",
    "NullOrder",
    "OutputSchemaResolver",
    "Portability",
    "Purity",
    "RenameField",
    "RenameTransformation",
    "SchemaEffect",
    "SelectTransformation",
    "SortDirection",
    "SortKey",
    "SortTransformation",
    "TransformationProperties",
    "TransformationSpec",
]
