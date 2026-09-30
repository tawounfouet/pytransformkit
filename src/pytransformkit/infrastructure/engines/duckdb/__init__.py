"""Optional DuckDB relational SQL adapter."""

from pytransformkit.infrastructure.engines.duckdb.adapter import DuckDBAdapter
from pytransformkit.infrastructure.engines.duckdb.expressions import (
    DuckDBExpressionCompiler,
    DuckDBSQLFragment,
)
from pytransformkit.infrastructure.engines.duckdb.handle import (
    DuckDBDatasetHandle,
)
from pytransformkit.infrastructure.engines.duckdb.planner import (
    DuckDBCompiledPlan,
    DuckDBCompiledQuery,
    DuckDBPlanCompiler,
)
from pytransformkit.infrastructure.engines.duckdb.types import (
    DuckDBSchemaInspector,
    DuckDBTypeMapper,
    quote_identifier,
)

__all__ = [
    "DuckDBAdapter",
    "DuckDBCompiledPlan",
    "DuckDBCompiledQuery",
    "DuckDBDatasetHandle",
    "DuckDBExpressionCompiler",
    "DuckDBPlanCompiler",
    "DuckDBSQLFragment",
    "DuckDBSchemaInspector",
    "DuckDBTypeMapper",
    "quote_identifier",
]
