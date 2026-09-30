"""Lower LogicalPlan values to parameterized DuckDB SQL using CTEs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.transformations.aggregation import (
    AggregateTransformation,
    group_output_name,
)
from pytransformkit.domain.transformations.base import TransformationSpec
from pytransformkit.domain.transformations.casting import (
    CastPolicy,
    CastTransformation,
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
from pytransformkit.domain.transformations.relational import (
    ExceptTransformation,
    IntersectTransformation,
    JoinTransformation,
    JoinType,
    NullJoinPolicy,
    UnionTransformation,
)
from pytransformkit.domain.transformations.sorting import SortTransformation
from pytransformkit.errors.engine import AdapterError
from pytransformkit.infrastructure.engines.duckdb.expressions import (
    DuckDBExpressionCompiler,
    DuckDBSQLFragment,
)
from pytransformkit.infrastructure.engines.duckdb.types import (
    DuckDBTypeMapper,
    quote_identifier,
)


@dataclass(frozen=True, slots=True)
class DuckDBCompiledQuery:
    """One named output query with values kept separate from SQL text."""

    name: str
    sql: str
    params: tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class DuckDBCompiledPlan:
    """Parameterized SQL lowering for every named plan output."""

    outputs: tuple[DuckDBCompiledQuery, ...]

    def output(self, name: str) -> DuckDBCompiledQuery:
        for output in self.outputs:
            if output.name == name:
                return output
        raise KeyError(name)


class DuckDBPlanCompiler:
    """Compile a LogicalPlan into CTE-backed DuckDB SELECT statements."""

    def __init__(
        self,
        expression_compiler: DuckDBExpressionCompiler | None = None,
        type_mapper: DuckDBTypeMapper | None = None,
    ) -> None:
        self._expressions = expression_compiler or DuckDBExpressionCompiler()
        self._types = type_mapper or DuckDBTypeMapper()

    def compile(
        self,
        plan: LogicalPlan,
        input_views: dict[str, str],
    ) -> DuckDBCompiledPlan:
        aliases: dict[object, str] = {}
        ctes: list[tuple[str, DuckDBSQLFragment]] = []
        output_aliases: list[tuple[str, str]] = []

        for index, node in enumerate(plan.nodes):
            alias = f"ptk_node_{index}"
            aliases[node.node_id] = alias

            if node.kind is PipelineNodeKind.INPUT:
                if node.name is None or node.name not in input_views:
                    raise AdapterError(f"Missing DuckDB input view for {node.name!r}.")
                source = quote_identifier(input_views[node.name])
                ctes.append(
                    (
                        alias,
                        DuckDBSQLFragment(f"SELECT * FROM {source}"),
                    )
                )
                continue

            if node.kind is PipelineNodeKind.TRANSFORMATION:
                if node.transformation is None:
                    raise AdapterError(
                        "Transformation LogicalPlan node is missing its specification."
                    )
                inputs = tuple(aliases[item] for item in node.input_node_ids)
                fragment = self._compile_transformation(
                    node.transformation,
                    inputs=inputs,
                    input_schemas=node.input_schemas,
                    output_schema=node.output_schema,
                )
                ctes.append((alias, fragment))
                continue

            if node.kind is PipelineNodeKind.OUTPUT:
                if node.name is None:
                    raise AdapterError("Output LogicalPlan node is missing its name.")
                if len(node.input_node_ids) != 1:
                    raise AdapterError(
                        "DuckDB output node requires exactly one predecessor."
                    )
                source = quote_identifier(aliases[node.input_node_ids[0]])
                ctes.append(
                    (
                        alias,
                        DuckDBSQLFragment(f"SELECT * FROM {source}"),
                    )
                )
                output_aliases.append((node.name, alias))
                continue

            raise AdapterError(f"Unsupported LogicalPlan node kind {node.kind!r}.")

        if not output_aliases:
            raise AdapterError("LogicalPlan did not produce any outputs.")

        cte_sql = ",\n".join(
            f"{quote_identifier(alias)} AS ({fragment.sql})" for alias, fragment in ctes
        )
        params = tuple(value for _, fragment in ctes for value in fragment.params)

        return DuckDBCompiledPlan(
            outputs=tuple(
                DuckDBCompiledQuery(
                    name=name,
                    sql=("WITH " + cte_sql + "\nSELECT * FROM " + quote_identifier(alias)),
                    params=params,
                )
                for name, alias in output_aliases
            )
        )

    def _compile_transformation(
        self,
        transformation: TransformationSpec,
        *,
        inputs: tuple[str, ...],
        input_schemas: tuple[Schema, ...],
        output_schema: Schema,
    ) -> DuckDBSQLFragment:
        if len(inputs) == 1:
            return self._compile_unary(
                transformation,
                source=inputs[0],
                input_schema=input_schemas[0],
                output_schema=output_schema,
            )
        if len(inputs) == 2:
            return self._compile_relational(
                transformation,
                left=inputs[0],
                right=inputs[1],
                input_schemas=input_schemas,
                output_schema=output_schema,
            )
        raise AdapterError(
            "DuckDB lowering supports unary or binary transformations only."
        )

    def _compile_unary(
        self,
        transformation: TransformationSpec,
        *,
        source: str,
        input_schema: Schema,
        output_schema: Schema,
    ) -> DuckDBSQLFragment:
        source_sql = quote_identifier(source)

        if isinstance(transformation, SelectTransformation):
            columns = ", ".join(
                quote_identifier(str(field)) for field in transformation.fields
            )
            return DuckDBSQLFragment(f"SELECT {columns} FROM {source_sql}")

        if isinstance(transformation, DropTransformation):
            columns = _schema_projection(output_schema)
            return DuckDBSQLFragment(
                f"SELECT {columns} FROM {source_sql}"
            )

        if isinstance(transformation, RenameTransformation):
            mapping = {
                str(item.source): item.target for item in transformation.renames
            }
            columns = ", ".join(
                (
                    f"{quote_identifier(field.name)} AS "
                    f"{quote_identifier(mapping[field.name])}"
                    if field.name in mapping
                    else quote_identifier(field.name)
                )
                for field in input_schema.fields
            )
            return DuckDBSQLFragment(
                f"SELECT {columns} FROM {source_sql}"
            )

        if isinstance(transformation, FilterTransformation):
            condition = self._expressions.compile(transformation.condition)
            return DuckDBSQLFragment(
                f"SELECT * FROM {source_sql} WHERE {condition.sql}",
                condition.params,
            )

        if isinstance(transformation, LimitTransformation):
            return DuckDBSQLFragment(
                f"SELECT * FROM {source_sql} LIMIT ?",
                (transformation.count,),
            )

        if isinstance(transformation, DistinctTransformation):
            return DuckDBSQLFragment(
                f"SELECT DISTINCT * FROM {source_sql}"
            )

        if isinstance(transformation, CastTransformation):
            if transformation.policy is CastPolicy.COERCE:
                raise AdapterError(
                    "DuckDB CastPolicy.COERCE is not qualified in LOT-19."
                )
            field_name = str(transformation.field)
            cast_function = (
                "TRY_CAST"
                if transformation.policy is CastPolicy.NULL
                else "CAST"
            )
            target = self._types.to_sql(transformation.target_type)
            columns = ", ".join(
                (
                    f"{cast_function}({quote_identifier(field.name)} AS {target}) "
                    f"AS {quote_identifier(field.name)}"
                    if field.name == field_name
                    else quote_identifier(field.name)
                )
                for field in input_schema.fields
            )
            return DuckDBSQLFragment(
                f"SELECT {columns} FROM {source_sql}"
            )

        if isinstance(transformation, DeriveTransformation):
            expression = self._expressions.compile(transformation.expression)
            columns = [
                quote_identifier(field.name)
                for field in input_schema.fields
                if field.name != transformation.field_name
            ]
            columns.append(
                f"{expression.sql} AS {quote_identifier(transformation.field_name)}"
            )
            return DuckDBSQLFragment(
                f"SELECT {', '.join(columns)} FROM {source_sql}",
                expression.params,
            )

        if isinstance(transformation, SortTransformation):
            order_by = ", ".join(
                (
                    f"{quote_identifier(str(key.field))} "
                    f"{key.direction.value.upper()} "
                    f"NULLS {key.nulls.value.upper()}"
                )
                for key in transformation.keys
            )
            return DuckDBSQLFragment(f"SELECT * FROM {source_sql} ORDER BY {order_by}")

        if isinstance(transformation, AggregateTransformation):
            return self._compile_aggregate(transformation, source_sql)

        raise AdapterError(
            "DuckDB SQL lowering is not implemented for "
            f"{type(transformation).__name__!r}."
        )

    def _compile_aggregate(
        self,
        transformation: AggregateTransformation,
        source_sql: str,
    ) -> DuckDBSQLFragment:
        selections: list[str] = []
        params: list[Any] = []

        for index, expression in enumerate(transformation.group_by):
            compiled = self._expressions.compile(expression)
            params.extend(compiled.params)
            selections.append(
                f"{compiled.sql} AS "
                f"{quote_identifier(group_output_name(expression, index))}"
            )

        for metric in transformation.metrics:
            compiled = self._expressions.compile_aggregate(metric.expression)
            params.extend(compiled.params)
            selections.append(f"{compiled.sql} AS {quote_identifier(metric.name)}")

        sql = f"SELECT {', '.join(selections)} FROM {source_sql}"
        if transformation.group_by:
            positions = ", ".join(
                str(index) for index in range(1, len(transformation.group_by) + 1)
            )
            sql += f" GROUP BY {positions}"

        return DuckDBSQLFragment(sql, tuple(params))

    def _compile_relational(
        self,
        transformation: TransformationSpec,
        *,
        left: str,
        right: str,
        input_schemas: tuple[Schema, ...],
        output_schema: Schema,
    ) -> DuckDBSQLFragment:
        left_sql = quote_identifier(left)
        right_sql = quote_identifier(right)

        if isinstance(transformation, JoinTransformation):
            return DuckDBSQLFragment(
                _join_sql(
                    transformation,
                    left_sql=left_sql,
                    right_sql=right_sql,
                    left_schema=input_schemas[0],
                    right_schema=input_schemas[1],
                )
            )

        if isinstance(transformation, UnionTransformation):
            operator = "UNION ALL" if transformation.all else "UNION"
            projection = _schema_projection(output_schema)
            return DuckDBSQLFragment(
                f"SELECT {projection} FROM {left_sql} "
                f"{operator} SELECT {projection} FROM {right_sql}"
            )

        if isinstance(transformation, IntersectTransformation):
            projection = _schema_projection(output_schema)
            return DuckDBSQLFragment(
                f"SELECT {projection} FROM {left_sql} "
                f"INTERSECT SELECT {projection} FROM {right_sql}"
            )

        if isinstance(transformation, ExceptTransformation):
            projection = _schema_projection(output_schema)
            return DuckDBSQLFragment(
                f"SELECT {projection} FROM {left_sql} "
                f"EXCEPT SELECT {projection} FROM {right_sql}"
            )

        raise AdapterError(
            "DuckDB relational lowering is not implemented for "
            f"{type(transformation).__name__!r}."
        )


def _schema_projection(schema: Schema) -> str:
    return ", ".join(quote_identifier(field.name) for field in schema.fields)


def _join_sql(
    transformation: JoinTransformation,
    *,
    left_sql: str,
    right_sql: str,
    left_schema: Schema,
    right_schema: Schema,
) -> str:
    left_alias = "l"
    right_alias = "r"

    if transformation.how in {JoinType.SEMI, JoinType.ANTI}:
        projection = ", ".join(
            f"{left_alias}.{quote_identifier(field.name)}"
            for field in left_schema.fields
        )
    else:
        projection = _join_projection(
            transformation,
            left_schema=left_schema,
            right_schema=right_schema,
            left_alias=left_alias,
            right_alias=right_alias,
        )

    join_keyword = {
        JoinType.INNER: "INNER JOIN",
        JoinType.LEFT: "LEFT JOIN",
        JoinType.RIGHT: "RIGHT JOIN",
        JoinType.FULL: "FULL OUTER JOIN",
        JoinType.SEMI: "SEMI JOIN",
        JoinType.ANTI: "ANTI JOIN",
        JoinType.CROSS: "CROSS JOIN",
    }[transformation.how]

    sql = (
        f"SELECT {projection} FROM {left_sql} AS {left_alias} "
        f"{join_keyword} {right_sql} AS {right_alias}"
    )
    if transformation.how is JoinType.CROSS:
        return sql

    operator = (
        "IS NOT DISTINCT FROM" if transformation.nulls is NullJoinPolicy.MATCH else "="
    )
    predicates = " AND ".join(
        (
            f"{left_alias}.{quote_identifier(str(key.left))} "
            f"{operator} "
            f"{right_alias}.{quote_identifier(str(key.right))}"
        )
        for key in transformation.keys
    )
    return f"{sql} ON {predicates}"


def _join_projection(
    transformation: JoinTransformation,
    *,
    left_schema: Schema,
    right_schema: Schema,
    left_alias: str,
    right_alias: str,
) -> str:
    expressions: list[str] = []
    used_names: set[str] = set()
    right_key_names = {str(key.right) for key in transformation.keys}
    key_by_left = {str(key.left): str(key.right) for key in transformation.keys}

    for field in left_schema.fields:
        source = f"{left_alias}.{quote_identifier(field.name)}"
        if (
            transformation.how in {JoinType.RIGHT, JoinType.FULL}
            and field.name in key_by_left
        ):
            right_key = key_by_left[field.name]
            source = f"COALESCE({source}, {right_alias}.{quote_identifier(right_key)})"
        expressions.append(f"{source} AS {quote_identifier(field.name)}")
        used_names.add(field.name)

    for field in right_schema.fields:
        if field.name in right_key_names:
            continue
        output_name = field.name
        if output_name in used_names:
            output_name = f"{output_name}{transformation.right_suffix}"
        expressions.append(
            f"{right_alias}.{quote_identifier(field.name)} "
            f"AS {quote_identifier(output_name)}"
        )
        used_names.add(output_name)

    return ", ".join(expressions)
