# ruff: noqa: E402

from __future__ import annotations

import pytest

pa = pytest.importorskip("pyarrow")

from pytransformkit.errors import AdapterError
from pytransformkit.infrastructure.engines.pyarrow import (
    ConversionLossiness,
    ConversionPolicy,
    PyArrowDatasetHandle,
    PyArrowInterchange,
)


def test_pandas_arrow_bridge_is_lossless_for_qualified_primitive_types() -> None:
    pd = pytest.importorskip("pandas")
    dataframe = pd.DataFrame(
        {
            "customer_id": pd.Series([1, 2], dtype="int64"),
            "email": pd.Series(["a", "b"], dtype="string"),
        }
    )

    converted = PyArrowInterchange.from_pandas(dataframe)

    assert converted.lossiness is ConversionLossiness.LOSSLESS
    assert isinstance(converted.value, PyArrowDatasetHandle)
    round_trip = PyArrowInterchange.to_pandas(converted.value)
    assert round_trip.lossiness is ConversionLossiness.LOSSLESS
    assert round_trip.value["customer_id"].tolist() == [1, 2]
    assert round_trip.value["email"].tolist() == ["a", "b"]


def test_strict_pandas_bridge_rejects_object_dtype_inference() -> None:
    pd = pytest.importorskip("pandas")
    dataframe = pd.DataFrame({"payload": [{"x": 1}, {"x": 2}]})

    with pytest.raises(AdapterError, match="potentially lossy"):
        PyArrowInterchange.from_pandas(dataframe)


def test_permissive_conversion_returns_structured_diagnostics() -> None:
    pd = pytest.importorskip("pandas")
    dataframe = pd.DataFrame({"payload": [{"x": 1}, {"x": 2}]})

    converted = PyArrowInterchange.from_pandas(
        dataframe,
        policy=ConversionPolicy.ALLOW_POTENTIALLY_LOSSY,
    )

    assert converted.lossiness is ConversionLossiness.POTENTIALLY_LOSSY
    assert converted.diagnostics
    assert converted.diagnostics[0].code == "PTK-ARROW-CONV-001"
    assert converted.diagnostics[0].related_field == "payload"


def test_polars_arrow_bridge_round_trips_materialized_frame() -> None:
    pl = pytest.importorskip("polars")
    frame = pl.DataFrame({"customer_id": [1, 2], "email": ["a", "b"]})

    converted = PyArrowInterchange.from_polars(frame)
    round_trip = PyArrowInterchange.to_polars(converted.value)

    assert converted.lossiness is ConversionLossiness.LOSSLESS
    assert round_trip.lossiness is ConversionLossiness.LOSSLESS
    assert round_trip.value.to_dict(as_series=False) == {
        "customer_id": [1, 2],
        "email": ["a", "b"],
    }
