"""Mapping between PyTransformKit logical types and PyArrow types."""

from typing import Any

import pyarrow as pa

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
    StructField,
    StructType,
    TimestampType,
    TimeType,
    UnknownType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.errors.engine import AdapterError


class PyArrowTypeMapper:
    """Loss-aware logical/native type mapping for Arrow."""

    def to_native(self, data_type: DataType) -> pa.DataType:
        if isinstance(data_type, StringType):
            return pa.string()
        if isinstance(data_type, BooleanType):
            return pa.bool_()
        if isinstance(data_type, IntegerType):
            mapping = {
                (8, True): pa.int8(),
                (16, True): pa.int16(),
                (32, True): pa.int32(),
                (64, True): pa.int64(),
                (8, False): pa.uint8(),
                (16, False): pa.uint16(),
                (32, False): pa.uint32(),
                (64, False): pa.uint64(),
            }
            return mapping[(data_type.bits, data_type.signed)]
        if isinstance(data_type, FloatType):
            return pa.float32() if data_type.bits == 32 else pa.float64()
        if isinstance(data_type, DecimalType):
            if data_type.precision <= 38:
                return pa.decimal128(data_type.precision, data_type.scale)
            return pa.decimal256(data_type.precision, data_type.scale)
        if isinstance(data_type, DateType):
            return pa.date32()
        if isinstance(data_type, TimeType):
            if data_type.unit in {"s", "ms"}:
                return pa.time32(data_type.unit)
            return pa.time64(data_type.unit)
        if isinstance(data_type, TimestampType):
            return pa.timestamp(data_type.unit, tz=data_type.timezone)
        if isinstance(data_type, DurationType):
            return pa.duration(data_type.unit)
        if isinstance(data_type, BinaryType):
            return pa.binary()
        if isinstance(data_type, ListType):
            return pa.list_(
                pa.field(
                    "item",
                    self.to_native(data_type.element_type),
                    nullable=data_type.element_nullable,
                )
            )
        if isinstance(data_type, StructType):
            return pa.struct(
                [
                    pa.field(
                        field.name,
                        self.to_native(field.data_type),
                        nullable=field.nullable,
                    )
                    for field in data_type.fields
                ]
            )
        if isinstance(data_type, MapType):
            return pa.map_(
                self.to_native(data_type.key_type),
                self.to_native(data_type.value_type),
            )
        if isinstance(data_type, UnknownType):
            return pa.null()

        raise AdapterError(
            f"Unsupported logical DataType {type(data_type).__name__!r}."
        )

    def from_native(self, dtype: Any) -> DataType:
        if pa.types.is_string(dtype) or pa.types.is_large_string(dtype):
            return StringType()
        if pa.types.is_boolean(dtype):
            return BooleanType()
        if pa.types.is_int8(dtype):
            return IntegerType(bits=8)
        if pa.types.is_int16(dtype):
            return IntegerType(bits=16)
        if pa.types.is_int32(dtype):
            return IntegerType(bits=32)
        if pa.types.is_int64(dtype):
            return IntegerType(bits=64)
        if pa.types.is_uint8(dtype):
            return IntegerType(bits=8, signed=False)
        if pa.types.is_uint16(dtype):
            return IntegerType(bits=16, signed=False)
        if pa.types.is_uint32(dtype):
            return IntegerType(bits=32, signed=False)
        if pa.types.is_uint64(dtype):
            return IntegerType(bits=64, signed=False)
        if pa.types.is_float32(dtype):
            return FloatType(bits=32)
        if pa.types.is_float64(dtype):
            return FloatType(bits=64)
        if pa.types.is_decimal(dtype):
            return DecimalType(precision=dtype.precision, scale=dtype.scale)
        if pa.types.is_date(dtype):
            return DateType()
        if pa.types.is_time(dtype):
            return TimeType(unit=dtype.unit)
        if pa.types.is_timestamp(dtype):
            return TimestampType(unit=dtype.unit, timezone=dtype.tz)
        if pa.types.is_duration(dtype):
            return DurationType(unit=dtype.unit)
        if pa.types.is_binary(dtype) or pa.types.is_large_binary(dtype):
            return BinaryType()
        if pa.types.is_list(dtype) or pa.types.is_large_list(dtype):
            return ListType(
                element_type=self.from_native(dtype.value_type),
                element_nullable=dtype.value_field.nullable,
            )
        if pa.types.is_struct(dtype):
            return StructType(
                fields=tuple(
                    StructField(
                        name=field.name,
                        data_type=self.from_native(field.type),
                        nullable=field.nullable,
                    )
                    for field in dtype
                )
            )
        if pa.types.is_map(dtype):
            return MapType(
                key_type=self.from_native(dtype.key_type),
                value_type=self.from_native(dtype.item_type),
                value_nullable=dtype.item_field.nullable,
            )
        if pa.types.is_null(dtype):
            return UnknownType()

        return UnknownType()


class PyArrowSchemaInspector:
    """Infer the engine-neutral Schema from Arrow schema metadata."""

    def __init__(self, type_mapper: PyArrowTypeMapper | None = None) -> None:
        self._type_mapper = type_mapper or PyArrowTypeMapper()

    def inspect(self, value: Any) -> Schema:
        if isinstance(value, (pa.Table, pa.RecordBatch)):
            native_schema = value.schema
        elif isinstance(value, pa.Schema):
            native_schema = value
        else:
            raise TypeError(
                "Arrow schema inspection requires a Table, RecordBatch, or Schema."
            )

        return Schema(
            fields=tuple(
                Field(
                    name=field.name,
                    data_type=self._type_mapper.from_native(field.type),
                    nullable=field.nullable,
                )
                for field in native_schema
            )
        )
