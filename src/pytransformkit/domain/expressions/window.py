"""Portable analytical window Expression model."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.expressions.base import Expression, ensure_expression
from pytransformkit.errors.expression import ExpressionTypeError


class WindowFunction(StrEnum):
    """Portable analytical functions qualified by LOT-13."""

    ROW_NUMBER = "row_number"
    RANK = "rank"
    DENSE_RANK = "dense_rank"
    LAG = "lag"
    LEAD = "lead"
    COUNT = "count"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    MEAN = "mean"


class WindowSortDirection(StrEnum):
    """Portable window ordering direction."""

    ASC = "asc"
    DESC = "desc"


class WindowNullOrder(StrEnum):
    """Portable NULL positioning for window ordering."""

    FIRST = "first"
    LAST = "last"


class WindowFrameMode(StrEnum):
    """Logical frame coordinate system."""

    ROWS = "rows"
    RANGE = "range"


class WindowBoundaryKind(StrEnum):
    """Portable frame boundary kind."""

    UNBOUNDED_PRECEDING = "unbounded_preceding"
    PRECEDING = "preceding"
    CURRENT_ROW = "current_row"
    FOLLOWING = "following"
    UNBOUNDED_FOLLOWING = "unbounded_following"


class WindowFrameKind(StrEnum):
    """Capability-relevant frame classification."""

    FULL_PARTITION = "full_partition"
    ROWS_CUMULATIVE = "rows_cumulative"
    ROWS_MOVING = "rows_moving"
    ROWS_ARBITRARY = "rows_arbitrary"
    RANGE = "range"


class WindowDeterminism(StrEnum):
    """Static determinism diagnostic for one window expression."""

    ORDER_INDEPENDENT = "order_independent"
    VALUE_ORDERED = "value_ordered"
    ORDER_DEPENDENT = "order_dependent"


@dataclass(frozen=True, slots=True)
class WindowBoundary:
    """One immutable analytical frame boundary."""

    kind: WindowBoundaryKind
    offset: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, WindowBoundaryKind):
            raise TypeError("WindowBoundary kind must be a WindowBoundaryKind.")

        if self.kind in {
            WindowBoundaryKind.PRECEDING,
            WindowBoundaryKind.FOLLOWING,
        }:
            if not isinstance(self.offset, int) or isinstance(self.offset, bool):
                raise TypeError(
                    "PRECEDING/FOLLOWING window boundaries require an integer offset."
                )
            if self.offset < 0:
                raise ValueError("Window boundary offset must be non-negative.")
            return

        if self.offset is not None:
            raise ValueError(
                f"{self.kind.value} window boundary does not accept an offset."
            )

    @property
    def relative_position(self) -> float:
        if self.kind is WindowBoundaryKind.UNBOUNDED_PRECEDING:
            return float("-inf")
        if self.kind is WindowBoundaryKind.PRECEDING:
            assert self.offset is not None
            return float(-self.offset)
        if self.kind is WindowBoundaryKind.CURRENT_ROW:
            return 0.0
        if self.kind is WindowBoundaryKind.FOLLOWING:
            assert self.offset is not None
            return float(self.offset)
        return float("inf")


@dataclass(frozen=True, slots=True)
class WindowFrame:
    """Immutable logical frame boundaries."""

    mode: WindowFrameMode
    start: WindowBoundary
    end: WindowBoundary

    def __post_init__(self) -> None:
        if not isinstance(self.mode, WindowFrameMode):
            raise TypeError("WindowFrame mode must be a WindowFrameMode.")
        if not isinstance(self.start, WindowBoundary):
            raise TypeError("WindowFrame start must be a WindowBoundary.")
        if not isinstance(self.end, WindowBoundary):
            raise TypeError("WindowFrame end must be a WindowBoundary.")
        if self.start.relative_position > self.end.relative_position:
            raise ValueError("WindowFrame start must not be after its end.")

    @property
    def kind(self) -> WindowFrameKind:
        if self.mode is WindowFrameMode.RANGE:
            return WindowFrameKind.RANGE

        if (
            self.start.kind is WindowBoundaryKind.UNBOUNDED_PRECEDING
            and self.end.kind is WindowBoundaryKind.CURRENT_ROW
        ):
            return WindowFrameKind.ROWS_CUMULATIVE

        if (
            self.start.kind is WindowBoundaryKind.PRECEDING
            and self.end.kind is WindowBoundaryKind.CURRENT_ROW
        ):
            return WindowFrameKind.ROWS_MOVING

        return WindowFrameKind.ROWS_ARBITRARY


@dataclass(frozen=True, slots=True)
class WindowOrderKey:
    """One ordered field in a WindowSpec."""

    field: FieldPath
    direction: WindowSortDirection = WindowSortDirection.ASC
    nulls: WindowNullOrder = WindowNullOrder.LAST

    def __post_init__(self) -> None:
        if not isinstance(self.field, FieldPath):
            raise TypeError("Window order field must be a FieldPath.")
        if not isinstance(self.direction, WindowSortDirection):
            raise TypeError("Window order direction must be a WindowSortDirection.")
        if not isinstance(self.nulls, WindowNullOrder):
            raise TypeError("Window null ordering must be a WindowNullOrder.")


@dataclass(frozen=True, slots=True)
class WindowSpec:
    """Immutable partition/order/frame specification."""

    partition_keys: tuple[FieldPath, ...] = ()
    order_keys: tuple[WindowOrderKey, ...] = ()
    frame: WindowFrame | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.partition_keys, tuple):
            raise TypeError("Window partition keys must be provided as a tuple.")
        if any(not isinstance(key, FieldPath) for key in self.partition_keys):
            raise TypeError("Window partition keys must contain FieldPath values.")
        if len(set(self.partition_keys)) != len(self.partition_keys):
            raise ValueError("Window partition keys must be unique.")

        if not isinstance(self.order_keys, tuple):
            raise TypeError("Window order keys must be provided as a tuple.")
        if any(not isinstance(key, WindowOrderKey) for key in self.order_keys):
            raise TypeError("Window order keys must contain WindowOrderKey values.")
        order_fields = tuple(key.field for key in self.order_keys)
        if len(set(order_fields)) != len(order_fields):
            raise ValueError("Window order fields must be unique.")

        if self.frame is not None and not isinstance(self.frame, WindowFrame):
            raise TypeError("Window frame must be a WindowFrame.")

    def partition_by(self, *fields: str) -> WindowSpec:
        """Return a copy with explicit partition fields."""
        return replace(
            self,
            partition_keys=tuple(FieldPath.of(field) for field in fields),
        )

    def order_by(
        self,
        *fields: str | WindowOrderKey,
    ) -> WindowSpec:
        """Return a copy with explicit order keys."""
        keys: list[WindowOrderKey] = []
        for field in fields:
            if isinstance(field, WindowOrderKey):
                keys.append(field)
            elif isinstance(field, str):
                keys.append(WindowOrderKey(FieldPath.of(field)))
            else:
                raise TypeError(
                    "Window order_by accepts field names or WindowOrderKey values."
                )
        if not keys:
            raise ValueError("Window order_by requires at least one field.")
        return replace(self, order_keys=tuple(keys))

    def rows_between(
        self,
        start: WindowBoundary,
        end: WindowBoundary,
    ) -> WindowSpec:
        return replace(
            self,
            frame=WindowFrame(
                mode=WindowFrameMode.ROWS,
                start=start,
                end=end,
            ),
        )

    def range_between(
        self,
        start: WindowBoundary,
        end: WindowBoundary,
    ) -> WindowSpec:
        return replace(
            self,
            frame=WindowFrame(
                mode=WindowFrameMode.RANGE,
                start=start,
                end=end,
            ),
        )


@dataclass(frozen=True, slots=True)
class WindowFunctionCall:
    """Immutable authoring value awaiting an explicit WindowSpec."""

    function: WindowFunction
    argument: Expression | None = None
    offset: int = 1
    default: Expression | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.function, WindowFunction):
            raise TypeError("WindowFunctionCall function must be a WindowFunction.")

        if self.argument is not None and not isinstance(self.argument, Expression):
            raise TypeError("Window function argument must be an Expression.")

        if self.function in {
            WindowFunction.LAG,
            WindowFunction.LEAD,
        }:
            if self.argument is None:
                raise ValueError(f"{self.function.value} requires an argument.")
            if not isinstance(self.offset, int) or isinstance(self.offset, bool):
                raise TypeError("Window offset must be an integer.")
            if self.offset <= 0:
                raise ValueError("Window offset must be greater than zero.")
        elif self.offset != 1:
            raise ValueError(f"{self.function.value} does not accept an offset.")

        if (
            self.function
            in {
                WindowFunction.SUM,
                WindowFunction.MIN,
                WindowFunction.MAX,
                WindowFunction.MEAN,
            }
            and self.argument is None
        ):
            raise ValueError(f"{self.function.value} requires an argument.")

        if self.default is not None and self.function not in {
            WindowFunction.LAG,
            WindowFunction.LEAD,
        }:
            raise ValueError(f"{self.function.value} does not accept a default value.")

    def over(self, spec: WindowSpec) -> WindowExpression:
        """Bind this function call to one immutable WindowSpec."""
        if not isinstance(spec, WindowSpec):
            raise TypeError("Window function over() requires a WindowSpec.")
        return WindowExpression(
            function=self.function,
            spec=spec,
            argument=self.argument,
            offset=self.offset,
            default=self.default,
        )


@dataclass(frozen=True, slots=True, eq=False)
class WindowExpression(Expression):
    """Portable analytical Expression bound to a WindowSpec."""

    function: WindowFunction
    spec: WindowSpec
    argument: Expression | None = None
    offset: int = 1
    default: Expression | None = None

    def __post_init__(self) -> None:
        WindowFunctionCall(
            function=self.function,
            argument=self.argument,
            offset=self.offset,
            default=self.default,
        )
        if not isinstance(self.spec, WindowSpec):
            raise TypeError("WindowExpression spec must be a WindowSpec.")

    @property
    def requires_ordering(self) -> bool:
        if self.function in {
            WindowFunction.ROW_NUMBER,
            WindowFunction.RANK,
            WindowFunction.DENSE_RANK,
            WindowFunction.LAG,
            WindowFunction.LEAD,
        }:
            return True
        return self.spec.frame is not None

    @property
    def determinism(self) -> WindowDeterminism:
        if self.function in {
            WindowFunction.ROW_NUMBER,
            WindowFunction.LAG,
            WindowFunction.LEAD,
        }:
            return WindowDeterminism.ORDER_DEPENDENT
        if self.spec.frame is not None:
            return WindowDeterminism.ORDER_DEPENDENT
        if self.function in {
            WindowFunction.RANK,
            WindowFunction.DENSE_RANK,
        }:
            return WindowDeterminism.VALUE_ORDERED
        return WindowDeterminism.ORDER_INDEPENDENT

    @property
    def frame_kind(self) -> WindowFrameKind:
        if self.spec.frame is None:
            return WindowFrameKind.FULL_PARTITION
        return self.spec.frame.kind


def as_window_argument(value: object) -> Expression:
    """Normalize one public window function argument."""
    return ensure_expression(value)


def validate_window_expression(expression: WindowExpression) -> None:
    """Validate semantic ordering requirements independent from an engine."""
    if expression.requires_ordering and not expression.spec.order_keys:
        raise ExpressionTypeError(
            f"{expression.function.value} requires an explicit window order_by."
        )
