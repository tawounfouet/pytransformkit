"""Mapping between PyTransformKit logical types and DuckDB SQL types."""

from __future__ import annotations

from typing import Any

from pytransformkit.domain.data.data_types import (
    BinaryType,
    BooleanType,
    DataType,
    DateType,
    DecimalType,
    DurationType,
    FloatType,
    IntegerType,
    ListType,
    MapType,
    StringType,
    StructType,
    TimestampType,
    TimeType,
    UnknownType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.errors.engine import AdapterError


class DuckDBTypeMapper:
    """Map engine-neutral logical types to DuckDB SQL type declarations."""

    def to_sql(self, data_type: DataType) -> str:
        if isinstance(data_type, StringType):
            return "VARCHAR"
        if isinstance(data_type, BooleanType):
            return "BOOLEAN"
        if isinstance(data_type, IntegerType):
            mapping = {
                (8, True): "TINYINT",
                (16, True): "SMALLINT",
                (32, True): "INTEGER",
                (64, True): "BIGINT",
                (8, False): "UTINYINT",
                (16, False): "USMALLINT",
                (32, False): "UINTEGER",
                (64, False): "UBIGINT",
            }
            return mapping[(data_type.bits, data_type.signed)]
        if isinstance(data_type, FloatType):
            return "FLOAT" if data_type.bits == 32 else "DOUBLE"
        if isinstance(data_type, DecimalType):
            return f"DECIMAL({data_type.precision},{data_type.scale})"
        if isinstance(data_type, DateType):
            return "DATE"
        if isinstance(data_type, TimeType):
            return "TIME"
        if isinstance(data_type, TimestampType):
            return "TIMESTAMPTZ" if data_type.timezone is not None else "TIMESTAMP"
        if isinstance(data_type, DurationType):
            return "INTERVAL"
        if isinstance(data_type, BinaryType):
            return "BLOB"
        if isinstance(data_type, ListType):
            return f"{self.to_sql(data_type.element_type)}[]"
        if isinstance(data_type, StructType):
            fields = ", ".join(
                f"{quote_identifier(field.name)} {self.to_sql(field.data_type)}"
                for field in data_type.fields
            )
            return f"STRUCT({fields})"
        if isinstance(data_type, MapType):
            return (
                "MAP("
                f"{self.to_sql(data_type.key_type)}, "
                f"{self.to_sql(data_type.value_type)}"
                ")"
            )
        if isinstance(data_type, UnknownType):
            raise AdapterError("UnknownType cannot be lowered to a DuckDB SQL type.")

        raise AdapterError(
            f"Unsupported logical DataType {type(data_type).__name__!r}."
        )

    def from_native(self, native_type: Any) -> DataType:
        """Map common DuckDB result types conservatively to logical DataTypes."""
        value = str(native_type).upper()

        simple: dict[str, DataType] = {
            "VARCHAR": StringType(),
            "BOOLEAN": BooleanType(),
            "TINYINT": IntegerType(bits=8),
            "SMALLINT": IntegerType(bits=16),
            "INTEGER": IntegerType(bits=32),
            "BIGINT": IntegerType(bits=64),
            "UTINYINT": IntegerType(bits=8, signed=False),
            "USMALLINT": IntegerType(bits=16, signed=False),
            "UINTEGER": IntegerType(bits=32, signed=False),
            "UBIGINT": IntegerType(bits=64, signed=False),
            "FLOAT": FloatType(bits=32),
            "DOUBLE": FloatType(bits=64),
            "DATE": DateType(),
            "TIME": TimeType(),
            "TIMESTAMP": TimestampType(),
            "TIMESTAMP WITH TIME ZONE": TimestampType(timezone="UTC"),
            "TIMESTAMPTZ": TimestampType(timezone="UTC"),
            "BLOB": BinaryType(),
            "INTERVAL": DurationType(),
        }
        if value in simple:
            return simple[value]

        if value.startswith("DECIMAL(") and value.endswith(")"):
            precision, scale = value[8:-1].split(",", maxsplit=1)
            return DecimalType(
                precision=int(precision.strip()),
                scale=int(scale.strip()),
            )

        return UnknownType()


class DuckDBSchemaInspector:
    """Infer a conservative logical Schema from a DuckDB relation."""

    def __init__(self, type_mapper: DuckDBTypeMapper | None = None) -> None:
        self._type_mapper = type_mapper or DuckDBTypeMapper()

    def inspect(self, relation: Any) -> Schema:
        columns = tuple(relation.columns)
        types = tuple(relation.types)
        if len(columns) != len(types):
            raise AdapterError("DuckDB relation column/type metadata is inconsistent.")

        return Schema(
            fields=tuple(
                Field(
                    name=name,
                    data_type=self._type_mapper.from_native(native_type),
                    nullable=True,
                )
                for name, native_type in zip(columns, types, strict=True)
            )
        )


def quote_identifier(value: str) -> str:
    """Quote one DuckDB identifier without treating it as SQL syntax."""
    if not isinstance(value, str) or not value:
        raise ValueError("DuckDB identifier must be a non-empty string.")
    return '"' + value.replace('"', '""') + '"'
