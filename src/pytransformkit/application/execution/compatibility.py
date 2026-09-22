"""Logical capability analysis and engine compatibility checks."""

from pytransformkit.domain.engines.capabilities import EngineCapability
from pytransformkit.domain.engines.descriptor import EngineDescriptor
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.transformations.base import TransformationSpec
from pytransformkit.domain.transformations.casting import CastTransformation
from pytransformkit.domain.transformations.deduplication import (
    DeduplicateTransformation,
)
from pytransformkit.domain.transformations.derivation import DeriveTransformation
from pytransformkit.domain.transformations.filtering import (
    DistinctTransformation,
    FilterTransformation,
    LimitTransformation,
)
from pytransformkit.domain.transformations.projection import (
    DropTransformation,
    RenameTransformation,
    SelectTransformation,
)
from pytransformkit.domain.transformations.sorting import SortTransformation
from pytransformkit.errors.engine import UnsupportedEngineCapabilityError
from pytransformkit.errors.transformation import UnsupportedTransformationError

_CAPABILITY_BY_TRANSFORMATION: tuple[
    tuple[type[TransformationSpec], EngineCapability],
    ...,
] = (
    (SelectTransformation, EngineCapability.SELECT),
    (DropTransformation, EngineCapability.DROP),
    (RenameTransformation, EngineCapability.RENAME),
    (FilterTransformation, EngineCapability.FILTER),
    (LimitTransformation, EngineCapability.LIMIT),
    (DistinctTransformation, EngineCapability.DISTINCT),
    (CastTransformation, EngineCapability.CAST),
    (DeriveTransformation, EngineCapability.DERIVE),
    (SortTransformation, EngineCapability.SORT),
    (DeduplicateTransformation, EngineCapability.DEDUPLICATE),
)


class EngineCapabilityAnalyzer:
    """Derive physical capabilities required by a LogicalPlan."""

    def required_capabilities(
        self,
        plan: LogicalPlan,
    ) -> frozenset[EngineCapability]:
        required: set[EngineCapability] = set()

        for node in plan.nodes:
            if node.transformation is None:
                continue
            required.add(_capability_for(node.transformation))

        return frozenset(required)


class EngineCompatibilityService:
    """Validate one explicit EngineDescriptor against a LogicalPlan."""

    def __init__(
        self,
        analyzer: EngineCapabilityAnalyzer | None = None,
    ) -> None:
        self._analyzer = analyzer or EngineCapabilityAnalyzer()

    def validate(
        self,
        plan: LogicalPlan,
        descriptor: EngineDescriptor,
    ) -> None:
        required = self._analyzer.required_capabilities(plan)
        missing = tuple(
            sorted(
                capability.value
                for capability in required
                if capability not in descriptor.capabilities
            )
        )

        if missing:
            raise UnsupportedEngineCapabilityError(
                descriptor.id,
                missing,
            )


def _capability_for(
    transformation: TransformationSpec,
) -> EngineCapability:
    for transformation_type, capability in _CAPABILITY_BY_TRANSFORMATION:
        if isinstance(transformation, transformation_type):
            return capability

    raise UnsupportedTransformationError(
        f"No engine capability mapping exists for {type(transformation).__name__!r}."
    )
