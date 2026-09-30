"""Public DuckDB adapter surface."""

from pytransformkit.infrastructure.engines.duckdb import (
    DuckDBAdapter,
    DuckDBCompiledPlan,
    DuckDBCompiledQuery,
    DuckDBDatasetHandle,
    DuckDBExpressionCompiler,
    DuckDBPlanCompiler,
    DuckDBSQLFragment,
    DuckDBSchemaInspector,
    DuckDBTypeMapper,
    quote_identifier,
)

DuckDBEngineAdapter = DuckDBAdapter

__all__ = [
    "DuckDBAdapter",
    "DuckDBCompiledPlan",
    "DuckDBCompiledQuery",
    "DuckDBDatasetHandle",
    "DuckDBEngineAdapter",
    "DuckDBExpressionCompiler",
    "DuckDBPlanCompiler",
    "DuckDBSQLFragment",
    "DuckDBSchemaInspector",
    "DuckDBTypeMapper",
    "quote_identifier",
]
