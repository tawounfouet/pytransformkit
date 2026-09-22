# ruff: noqa: E402

from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")

from pytransformkit.domain.data.data_types import (
    BooleanType,
    FloatType,
    IntegerType,
    StringType,
    TimestampType,
    UnknownType,
)
from pytransformkit.errors.schema import DuplicateFieldError
from pytransformkit.infrastructure.engines.pandas import (
    PandasSchemaInspector,
    PandasTypeMapper,
)


def test_type_mapper_maps_logical_types_to_nullable_pandas_dtypes() -> None:
    mapper = PandasTypeMapper()

    assert mapper.to_native(StringType()) == "string"
    assert mapper.to_native(BooleanType()) == "boolean"
    assert mapper.to_native(IntegerType(bits=32)) == "Int32"
    assert mapper.to_native(FloatType(bits=64)) == "Float64"
    assert mapper.to_native(TimestampType()) == "datetime64[ns]"


def test_type_mapper_keeps_object_dtype_unknown() -> None:
    mapper = PandasTypeMapper()
    dataframe = pd.DataFrame({"value": [{"x": 1}]})

    assert mapper.from_native(dataframe["value"].dtype) == UnknownType()


def test_schema_inspector_is_conservative_about_nullability() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_id": pd.Series([1, 2], dtype="int64"),
            "email": pd.Series(["a", "b"], dtype="string"),
        }
    )

    schema = PandasSchemaInspector().inspect(dataframe)

    assert schema.names() == ("customer_id", "email")
    assert schema.field("customer_id").data_type == IntegerType()
    assert schema.field("customer_id").nullable is True
    assert schema.field("email").data_type == StringType()
    assert schema.field("email").nullable is True


def test_schema_inspector_rejects_duplicate_columns() -> None:
    dataframe = pd.DataFrame([[1, 2]], columns=["email", "email"])

    with pytest.raises(DuplicateFieldError):
        PandasSchemaInspector().inspect(dataframe)
