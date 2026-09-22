"""Mapping between PyTransformKit DataTypes and Pandas dtypes."""

from typing import Any

import pandas as pd
from pandas.api import types as pdt

from pytransformkit.domain.data.data_types import (
    BinaryType,
    BooleanType,
    DataType,
    DateType,
    DecimalType,
    FloatType,
    IntegerType,
    StringType,
    TimestampType,
    UnknownType,
)
from pytransformkit.errors.engine import AdapterError


class PandasTypeMapper:
    """Conservative logical/native type mapping for Pandas."""

    def to_native(
        self,
        data_type: DataType,
        *,
        nullable: bool = True,
    ) -> str:
        del nullable

        if isinstance(data_type, StringType):
            return "string"
        if isinstance(data_type, BooleanType):
            return "boolean"
        if isinstance(data_type, IntegerType):
            prefix = "Int" if data_type.signed else "UInt"
            return f"{prefix}{data_type.bits}"
        if isinstance(data_type, FloatType):
            return f"Float{data_type.bits}"
        if isinstance(data_type, TimestampType):
            if data_type.timezone is None:
                return "datetime64[ns]"
            return f"datetime64[ns, {data_type.timezone}]"
        if isinstance(data_type, (DateType, BinaryType, UnknownType)):
            return "object"
        if isinstance(data_type, DecimalType):
            raise AdapterError(
                "Pandas Decimal mapping is not supported in the initial adapter."
            )

        raise AdapterError(
            f"Unsupported logical DataType {type(data_type).__name__!r}."
        )

    def from_native(self, dtype: Any) -> DataType:
        """Map a Pandas dtype conservatively to a logical DataType."""
        if str(dtype) == "object":
            return UnknownType()
        if pdt.is_bool_dtype(dtype):
            return BooleanType()
        if pdt.is_integer_dtype(dtype):
            itemsize = getattr(dtype, "itemsize", 8)
            bits = int(itemsize) * 8
            signed = not pdt.is_unsigned_integer_dtype(dtype)
            return IntegerType(bits=bits, signed=signed)
        if pdt.is_float_dtype(dtype):
            itemsize = getattr(dtype, "itemsize", 8)
            return FloatType(bits=int(itemsize) * 8)
        if pdt.is_datetime64_any_dtype(dtype):
            timezone = getattr(dtype, "tz", None)
            return TimestampType(
                timezone=str(timezone) if timezone is not None else None
            )
        if pdt.is_string_dtype(dtype):
            return StringType()

        return UnknownType()


class PandasSchemaInspector:
    """Infer a conservative logical Schema from a pandas.DataFrame."""

    def __init__(self, type_mapper: PandasTypeMapper | None = None) -> None:
        self._type_mapper = type_mapper or PandasTypeMapper()

    def inspect(self, dataframe: Any):
        from pytransformkit.domain.data.field import Field
        from pytransformkit.domain.data.schema import Schema
        from pytransformkit.errors.schema import DuplicateFieldError

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("Pandas schema inspection requires a DataFrame.")

        duplicated = dataframe.columns[dataframe.columns.duplicated()]
        if len(duplicated) > 0:
            raise DuplicateFieldError(str(duplicated[0]))

        fields = []
        for name, dtype in dataframe.dtypes.items():
            if not isinstance(name, str):
                raise AdapterError(
                    "Pandas column names must be strings for logical Schemas."
                )
            fields.append(
                Field(
                    name=name,
                    data_type=self._type_mapper.from_native(dtype),
                    nullable=True,
                )
            )

        return Schema(fields=tuple(fields))
