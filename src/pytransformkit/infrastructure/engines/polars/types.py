"""Mapping between PyTransformKit DataTypes and Polars dtypes."""

from typing import Any

import polars as pl

from pytransformkit.domain.data.data_types import (
    BinaryType,
    BooleanType,
    DataType,
    DateType,
    DecimalType,
    FloatType,
    IntegerType,
    StringType,
    TimeType,
    TimestampType,
    UnknownType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.errors.engine import AdapterError


class PolarsTypeMapper:
    """Logical/native type mapping for Polars."""

    def to_native(self, data_type: DataType) -> Any:
        if isinstance(data_type, StringType):
            return pl.String
        if isinstance(data_type, BooleanType):
            return pl.Boolean
        if isinstance(data_type, IntegerType):
            mapping = {
                (8, True): pl.Int8,
                (16, True): pl.Int16,
                (32, True): pl.Int32,
                (64, True): pl.Int64,
                (8, False): pl.UInt8,
                (16, False): pl.UInt16,
                (32, False): pl.UInt32,
                (64, False): pl.UInt64,
            }
            return mapping[(data_type.bits, data_type.signed)]
        if isinstance(data_type, FloatType):
            return pl.Float32 if data_type.bits == 32 else pl.Float64
        if isinstance(data_type, DecimalType):
            return pl.Decimal(
                precision=data_type.precision,
                scale=data_type.scale,
            )
        if isinstance(data_type, DateType):
            return pl.Date
        if isinstance(data_type, TimeType):
            return pl.Time
        if isinstance(data_type, TimestampType):
            return pl.Datetime(
                time_unit=data_type.unit,
                time_zone=data_type.timezone,
            )
        if isinstance(data_type, BinaryType):
            return pl.Binary
        if isinstance(data_type, UnknownType):
            return pl.Object

        raise AdapterError(
            f"Unsupported logical DataType {type(data_type).__name__!r}."
        )

    def from_native(self, dtype: Any) -> DataType:
        if dtype == pl.String:
            return StringType()
        if dtype == pl.Boolean:
            return BooleanType()
        if dtype == pl.Int8:
            return IntegerType(bits=8)
        if dtype == pl.Int16:
            return IntegerType(bits=16)
        if dtype == pl.Int32:
            return IntegerType(bits=32)
        if dtype == pl.Int64:
            return IntegerType(bits=64)
        if dtype == pl.UInt8:
            return IntegerType(bits=8, signed=False)
        if dtype == pl.UInt16:
            return IntegerType(bits=16, signed=False)
        if dtype == pl.UInt32:
            return IntegerType(bits=32, signed=False)
        if dtype == pl.UInt64:
            return IntegerType(bits=64, signed=False)
        if dtype == pl.Float32:
            return FloatType(bits=32)
        if dtype == pl.Float64:
            return FloatType(bits=64)
        if dtype == pl.Date:
            return DateType()
        if dtype == pl.Time:
            return TimeType()
        if dtype == pl.Binary:
            return BinaryType()

        if isinstance(dtype, pl.Datetime):
            return TimestampType(
                unit=dtype.time_unit,
                timezone=dtype.time_zone,
            )

        if isinstance(dtype, pl.Decimal):
            precision = dtype.precision
            scale = dtype.scale
            if precision is None:
                return UnknownType()
            return DecimalType(
                precision=precision,
                scale=scale,
            )

        return UnknownType()


class PolarsSchemaInspector:
    """Infer a conservative logical Schema without collecting LazyFrames."""

    def __init__(self, type_mapper: PolarsTypeMapper | None = None) -> None:
        self._type_mapper = type_mapper or PolarsTypeMapper()

    def inspect(self, frame: Any) -> Schema:
        if isinstance(frame, pl.LazyFrame):
            native_schema = frame.collect_schema()
        elif isinstance(frame, pl.DataFrame):
            native_schema = frame.schema
        else:
            raise TypeError(
                "Polars schema inspection requires a DataFrame or LazyFrame."
            )

        return Schema(
            fields=tuple(
                Field(
                    name=name,
                    data_type=self._type_mapper.from_native(dtype),
                    nullable=True,
                )
                for name, dtype in native_schema.items()
            )
        )
