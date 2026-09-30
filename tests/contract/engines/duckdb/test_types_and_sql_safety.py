# ruff: noqa: E402

from __future__ import annotations

import pytest

duckdb = pytest.importorskip("duckdb")

from pytransformkit.domain.data.data_types import (
    DecimalType,
    FloatType,
    IntegerType,
    StringType,
    TimestampType,
)
from pytransformkit.infrastructure.engines.duckdb import (
    DuckDBExpressionCompiler,
    DuckDBSchemaInspector,
    DuckDBTypeMapper,
    quote_identifier,
)
from pytransformkit.functions import col, lit


def test_type_mapper_covers_core_relational_types() -> None:
    mapper = DuckDBTypeMapper()

    assert mapper.to_sql(StringType()) == "VARCHAR"
    assert mapper.to_sql(IntegerType(bits=32)) == "INTEGER"
    assert mapper.to_sql(IntegerType(bits=64, signed=False)) == "UBIGINT"
    assert mapper.to_sql(FloatType(bits=64)) == "DOUBLE"
    assert mapper.to_sql(DecimalType(18, 4)) == "DECIMAL(18,4)"
    assert mapper.to_sql(TimestampType(timezone="UTC")) == "TIMESTAMPTZ"


def test_schema_inspector_reads_relation_metadata_without_domain_duckdb_types() -> None:
    connection = duckdb.connect()
    relation = connection.sql(
        "SELECT 1::BIGINT AS customer_id, 'a'::VARCHAR AS email"
    )

    schema = DuckDBSchemaInspector().inspect(relation)

    assert schema.names() == ("customer_id", "email")
    assert schema.field("customer_id").data_type == IntegerType()
    assert schema.field("email").data_type == StringType()
    connection.close()


def test_identifier_quoting_escapes_embedded_double_quotes() -> None:
    assert quote_identifier('a"b') == '"a""b"'


def test_expression_values_are_parameters_not_sql_interpolation() -> None:
    payload = "x'); DROP TABLE customers; --"
    expression = (col("status") == lit(payload)) & (col("amount") > 10)

    compiled = DuckDBExpressionCompiler().compile(expression)

    assert payload not in compiled.sql
    assert compiled.sql.count("?") == 2
    assert compiled.params == (payload, 10)
