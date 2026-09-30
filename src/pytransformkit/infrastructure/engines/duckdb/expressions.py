"""Safe lowering of portable Expressions to DuckDB SQL fragments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pytransformkit.domain.expressions.aggregate import (
    AggregateExpression,
    AggregateFunction,
)
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.binary import BinaryExpression
from pytransformkit.domain.expressions.functions import FunctionCall
from pytransformkit.domain.expressions.literals import Literal
from pytransformkit.domain.expressions.operators import (
    BinaryOperator,
    UnaryOperator,
)
from pytransformkit.domain.expressions.predicates import (
    IsNotNullExpression,
    IsNullExpression,
)
from pytransformkit.domain.expressions.references import ColumnReference
from pytransformkit.domain.expressions.unary import UnaryExpression
from pytransformkit.domain.expressions.window import (
    WindowBoundaryKind,
    WindowExpression,
    WindowFrameMode,
    WindowFunction,
)
from pytransformkit.errors.engine import AdapterError
from pytransformkit.infrastructure.engines.duckdb.types import quote_identifier


@dataclass(frozen=True, slots=True)
class DuckDBSQLFragment:
    """Parameterized DuckDB SQL fragment."""

    sql: str
    params: tuple[Any, ...] = ()

    def parenthesized(self) -> DuckDBSQLFragment:
        return DuckDBSQLFragment(f"({self.sql})", self.params)


class DuckDBExpressionCompiler:
    """Compile engine-neutral Expressions to parameterized DuckDB SQL."""

    def compile(self, expression: Expression) -> DuckDBSQLFragment:
        if isinstance(expression, ColumnReference):
            return DuckDBSQLFragment(_field_path_sql(expression.path.parts))

        if isinstance(expression, Literal):
            return DuckDBSQLFragment("?", (expression.value,))

        if isinstance(expression, BinaryExpression):
            return self._compile_binary(expression)

        if isinstance(expression, UnaryExpression):
            operand = self.compile(expression.operand)
            if expression.operator is UnaryOperator.NOT:
                return DuckDBSQLFragment(
                    f"(NOT {operand.sql})",
                    operand.params,
                )
            if expression.operator is UnaryOperator.NEGATE:
                return DuckDBSQLFragment(
                    f"(-{operand.sql})",
                    operand.params,
                )
            raise AdapterError(
                f"Unsupported unary operator {expression.operator.value!r}."
            )

        if isinstance(expression, IsNullExpression):
            operand = self.compile(expression.operand)
            return DuckDBSQLFragment(
                f"({operand.sql} IS NULL)",
                operand.params,
            )

        if isinstance(expression, IsNotNullExpression):
            operand = self.compile(expression.operand)
            return DuckDBSQLFragment(
                f"({operand.sql} IS NOT NULL)",
                operand.params,
            )

        if isinstance(expression, FunctionCall):
            return self._compile_function(expression)

        if isinstance(expression, WindowExpression):
            return self.compile_window(expression)

        raise AdapterError(
            f"DuckDB does not compile Expression {type(expression).__name__!r}."
        )

    def compile_aggregate(
        self,
        expression: AggregateExpression,
    ) -> DuckDBSQLFragment:
        argument = (
            None if expression.argument is None else self.compile(expression.argument)
        )

        if expression.function is AggregateFunction.COUNT:
            if argument is None:
                return DuckDBSQLFragment("COUNT(*)")
            return DuckDBSQLFragment(
                f"COUNT({argument.sql})",
                argument.params,
            )

        if argument is None:
            raise AdapterError(
                f"{expression.function.value} requires an aggregate argument."
            )

        if expression.function is AggregateFunction.COUNT_DISTINCT:
            return DuckDBSQLFragment(
                f"COUNT(DISTINCT {argument.sql})",
                argument.params,
            )

        function = {
            AggregateFunction.SUM: "SUM",
            AggregateFunction.MIN: "MIN",
            AggregateFunction.MAX: "MAX",
            AggregateFunction.MEAN: "AVG",
        }.get(expression.function)
        if function is None:
            raise AdapterError(
                f"Unsupported DuckDB aggregate {expression.function.value!r}."
            )
        return DuckDBSQLFragment(
            f"{function}({argument.sql})",
            argument.params,
        )

    def compile_window(
        self,
        expression: WindowExpression,
    ) -> DuckDBSQLFragment:
        argument = (
            None if expression.argument is None else self.compile(expression.argument)
        )
        default = (
            None if expression.default is None else self.compile(expression.default)
        )
        params: list[Any] = []

        function_sql: str
        if expression.function is WindowFunction.ROW_NUMBER:
            function_sql = "ROW_NUMBER()"
        elif expression.function is WindowFunction.RANK:
            function_sql = "RANK()"
        elif expression.function is WindowFunction.DENSE_RANK:
            function_sql = "DENSE_RANK()"
        elif expression.function in {WindowFunction.LAG, WindowFunction.LEAD}:
            if argument is None:
                raise AdapterError(
                    f"{expression.function.value} requires an argument."
                )
            params.extend(argument.params)
            args = [argument.sql, str(expression.offset)]
            if default is not None:
                args.append(default.sql)
                params.extend(default.params)
            function_sql = (
                f"{expression.function.value.upper()}({', '.join(args)})"
            )
        elif expression.function in {
            WindowFunction.COUNT,
            WindowFunction.SUM,
            WindowFunction.MIN,
            WindowFunction.MAX,
            WindowFunction.MEAN,
        }:
            if expression.function is WindowFunction.COUNT and argument is None:
                function_sql = "COUNT(*)"
            else:
                if argument is None:
                    raise AdapterError(
                        f"{expression.function.value} requires an argument."
                    )
                params.extend(argument.params)
                function = {
                    WindowFunction.COUNT: "COUNT",
                    WindowFunction.SUM: "SUM",
                    WindowFunction.MIN: "MIN",
                    WindowFunction.MAX: "MAX",
                    WindowFunction.MEAN: "AVG",
                }[expression.function]
                function_sql = f"{function}({argument.sql})"
        else:
            raise AdapterError(
                f"Unsupported DuckDB window function {expression.function.value!r}."
            )

        over_parts: list[str] = []
        if expression.spec.partition_keys:
            over_parts.append(
                "PARTITION BY "
                + ", ".join(
                    _field_path_sql(field.parts)
                    for field in expression.spec.partition_keys
                )
            )

        if expression.spec.order_keys:
            order_sql = ", ".join(
                (
                    f"{_field_path_sql(key.field.parts)} "
                    f"{key.direction.value.upper()} "
                    f"NULLS {key.nulls.value.upper()}"
                )
                for key in expression.spec.order_keys
            )
            over_parts.append(f"ORDER BY {order_sql}")

        if expression.spec.frame is not None:
            frame = expression.spec.frame
            over_parts.append(
                f"{frame.mode.value.upper()} BETWEEN "
                f"{_boundary_sql(frame.start.kind, frame.start.offset)} AND "
                f"{_boundary_sql(frame.end.kind, frame.end.offset)}"
            )

        return DuckDBSQLFragment(
            f"{function_sql} OVER ({' '.join(over_parts)})",
            tuple(params),
        )

    def _compile_binary(
        self,
        expression: BinaryExpression,
    ) -> DuckDBSQLFragment:
        left = self.compile(expression.left)
        right = self.compile(expression.right)
        operator = {
            BinaryOperator.EQ: "=",
            BinaryOperator.NE: "<>",
            BinaryOperator.LT: "<",
            BinaryOperator.LE: "<=",
            BinaryOperator.GT: ">",
            BinaryOperator.GE: ">=",
            BinaryOperator.ADD: "+",
            BinaryOperator.SUB: "-",
            BinaryOperator.MUL: "*",
            BinaryOperator.DIV: "/",
            BinaryOperator.AND: "AND",
            BinaryOperator.OR: "OR",
        }.get(expression.operator)
        if operator is None:
            raise AdapterError(
                f"Unsupported binary operator {expression.operator.value!r}."
            )
        return DuckDBSQLFragment(
            f"({left.sql} {operator} {right.sql})",
            left.params + right.params,
        )

    def _compile_function(
        self,
        expression: FunctionCall,
    ) -> DuckDBSQLFragment:
        name = expression.function.value
        arguments = tuple(self.compile(item) for item in expression.arguments)
        params = tuple(
            value for argument in arguments for value in argument.params
        )

        if name == "core.lower":
            return DuckDBSQLFragment(f"LOWER({arguments[0].sql})", params)
        if name == "core.upper":
            return DuckDBSQLFragment(f"UPPER({arguments[0].sql})", params)
        if name == "core.trim":
            return DuckDBSQLFragment(f"TRIM({arguments[0].sql})", params)
        if name == "core.concat":
            return DuckDBSQLFragment(
                "(" + " || ".join(argument.sql for argument in arguments) + ")",
                params,
            )

        raise AdapterError(f"DuckDB does not compile logical function {name!r}.")


def _field_path_sql(parts: tuple[str, ...]) -> str:
    if not parts:
        raise AdapterError("Field path must contain at least one part.")
    root = quote_identifier(parts[0])
    if len(parts) == 1:
        return root
    nested = root
    for part in parts[1:]:
        nested += f".{quote_identifier(part)}"
    return nested


def _boundary_sql(
    kind: WindowBoundaryKind,
    offset: int | None,
) -> str:
    if kind is WindowBoundaryKind.UNBOUNDED_PRECEDING:
        return "UNBOUNDED PRECEDING"
    if kind is WindowBoundaryKind.CURRENT_ROW:
        return "CURRENT ROW"
    if kind is WindowBoundaryKind.UNBOUNDED_FOLLOWING:
        return "UNBOUNDED FOLLOWING"
    if kind is WindowBoundaryKind.PRECEDING:
        if offset is None:
            raise AdapterError("PRECEDING boundary requires an offset.")
        return f"{offset} PRECEDING"
    if kind is WindowBoundaryKind.FOLLOWING:
        if offset is None:
            raise AdapterError("FOLLOWING boundary requires an offset.")
        return f"{offset} FOLLOWING"
    raise AdapterError(f"Unsupported window boundary {kind!r}.")
