"""Logical capability analysis and engine compatibility checks."""

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.engines.capabilities import EngineCapability
from pytransformkit.domain.engines.descriptor import EngineDescriptor
from pytransformkit.domain.expressions.aggregate import AggregateExpression
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.binary import BinaryExpression
from pytransformkit.domain.expressions.dependencies import ExpressionDependencyExtractor
from pytransformkit.domain.expressions.functions import FunctionCall
from pytransformkit.domain.expressions.predicates import (
    IsNotNullExpression,
    IsNullExpression,
)
from pytransformkit.domain.expressions.unary import UnaryExpression
from pytransformkit.domain.expressions.window import (
    WindowExpression,
    WindowFrameKind,
)
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.quality.rules import (
    AllowedValues,
    ExpressionValidation,
    NotNull,
    Range,
    Regex,
    Unique,
    ValidationRule,
)
from pytransformkit.domain.transformations.aggregation import AggregateTransformation
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
from pytransformkit.domain.transformations.quality import QualityGate
from pytransformkit.domain.transformations.relational import (
    ExceptTransformation,
    IntersectTransformation,
    JoinTransformation,
    JoinType,
    UnionTransformation,
)
from pytransformkit.domain.transformations.reshaping import (
    ExplodeTransformation,
    FlattenTransformation,
    PivotTransformation,
    UnpivotTransformation,
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
    (AggregateTransformation, EngineCapability.AGGREGATE),
    (PivotTransformation, EngineCapability.PIVOT),
    (UnpivotTransformation, EngineCapability.UNPIVOT),
    (ExplodeTransformation, EngineCapability.EXPLODE),
    (FlattenTransformation, EngineCapability.FLATTEN),
    (QualityGate, EngineCapability.QUALITY),
    (UnionTransformation, EngineCapability.UNION),
    (IntersectTransformation, EngineCapability.INTERSECT),
    (ExceptTransformation, EngineCapability.EXCEPT),
)

_JOIN_CAPABILITY: dict[JoinType, EngineCapability] = {
    JoinType.INNER: EngineCapability.JOIN_INNER,
    JoinType.LEFT: EngineCapability.JOIN_LEFT,
    JoinType.RIGHT: EngineCapability.JOIN_RIGHT,
    JoinType.FULL: EngineCapability.JOIN_FULL,
    JoinType.SEMI: EngineCapability.JOIN_SEMI,
    JoinType.ANTI: EngineCapability.JOIN_ANTI,
    JoinType.CROSS: EngineCapability.JOIN_CROSS,
}


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
            transformation = node.transformation
            required.add(_capability_for(transformation))

            for expression in _transformation_expressions(transformation):
                dependencies = ExpressionDependencyExtractor().extract(expression)
                if any(len(path.parts) > 1 for path in dependencies):
                    required.add(EngineCapability.NESTED)
                for current in _walk_expression(expression):
                    if isinstance(current, FunctionCall):
                        function_name = current.function.value
                        if function_name.startswith("core.temporal."):
                            required.add(EngineCapability.TEMPORAL)
                        if function_name == "core.temporal.duration_between":
                            required.add(EngineCapability.DURATION)

            if isinstance(transformation, QualityGate):
                for rule in transformation.spec.rules:
                    if any(
                        len(path.parts) > 1
                        for path in _quality_rule_paths(rule)
                    ):
                        required.add(EngineCapability.NESTED)

            if isinstance(transformation, DeriveTransformation) and isinstance(
                transformation.expression, WindowExpression
            ):
                required.add(EngineCapability.WINDOW)
                frame_capability = _window_frame_capability(
                    transformation.expression.frame_kind
                )
                if frame_capability is not None:
                    required.add(frame_capability)

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
    if isinstance(transformation, JoinTransformation):
        return _JOIN_CAPABILITY[transformation.how]

    for transformation_type, capability in _CAPABILITY_BY_TRANSFORMATION:
        if isinstance(transformation, transformation_type):
            return capability

    raise UnsupportedTransformationError(
        f"No engine capability mapping exists for {type(transformation).__name__!r}."
    )


def _transformation_expressions(
    transformation: TransformationSpec,
) -> tuple[Expression, ...]:
    if isinstance(transformation, DeriveTransformation):
        return (transformation.expression,)
    if isinstance(transformation, FilterTransformation):
        return (transformation.condition,)
    if isinstance(transformation, AggregateTransformation):
        return transformation.group_by + tuple(
            metric.expression for metric in transformation.metrics
        )
    if isinstance(transformation, QualityGate):
        return tuple(
            rule.expression
            for rule in transformation.spec.rules
            if isinstance(rule, ExpressionValidation)
        )
    return ()


def _walk_expression(expression: Expression) -> tuple[Expression, ...]:
    values: list[Expression] = [expression]

    if isinstance(expression, BinaryExpression):
        values.extend(_walk_expression(expression.left))
        values.extend(_walk_expression(expression.right))
    elif isinstance(
        expression,
        (UnaryExpression, IsNullExpression, IsNotNullExpression),
    ):
        values.extend(_walk_expression(expression.operand))
    elif isinstance(expression, FunctionCall):
        for argument in expression.arguments:
            values.extend(_walk_expression(argument))
    elif isinstance(expression, AggregateExpression):
        if expression.argument is not None:
            values.extend(_walk_expression(expression.argument))
    elif isinstance(expression, WindowExpression):
        if expression.argument is not None:
            values.extend(_walk_expression(expression.argument))
        if expression.default is not None:
            values.extend(_walk_expression(expression.default))

    return tuple(values)


def _quality_rule_paths(
    rule: ValidationRule,
) -> tuple[FieldPath, ...]:
    if isinstance(rule, (NotNull, Range, AllowedValues, Regex)):
        return (rule.field,)
    if isinstance(rule, Unique):
        return rule.fields
    return ()


def _window_frame_capability(
    frame_kind: WindowFrameKind,
) -> EngineCapability | None:
    if frame_kind is WindowFrameKind.FULL_PARTITION:
        return None
    if frame_kind is WindowFrameKind.ROWS_CUMULATIVE:
        return EngineCapability.WINDOW_ROWS_CUMULATIVE
    if frame_kind is WindowFrameKind.ROWS_MOVING:
        return EngineCapability.WINDOW_ROWS_MOVING
    if frame_kind is WindowFrameKind.ROWS_ARBITRARY:
        return EngineCapability.WINDOW_ROWS_ARBITRARY
    if frame_kind is WindowFrameKind.RANGE:
        return EngineCapability.WINDOW_RANGE
    raise UnsupportedTransformationError(f"Unknown window frame kind {frame_kind!r}.")
