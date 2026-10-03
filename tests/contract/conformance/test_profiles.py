# ruff: noqa: E402

from __future__ import annotations

import pytest

pytest.importorskip("pandas")
pytest.importorskip("polars")
pytest.importorskip("pyarrow")
pytest.importorskip("duckdb")

from pytransformkit.adapters.duckdb import DuckDBEngineAdapter
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.adapters.pyarrow import PyArrowEngineAdapter
from pytransformkit.conformance import (
    DUCKDB_CONFORMANCE,
    MANDATORY_V1_CAPABILITIES,
    PANDAS_CONFORMANCE,
    POLARS_CONFORMANCE,
    PYARROW_CONFORMANCE,
    ConformanceDimension,
    ConformanceStatus,
    EngineStability,
    engine_profile,
)
from pytransformkit.conformance.model import engine_capabilities


def test_pandas_and_polars_are_stable_v1_engines_with_mandatory_capabilities() -> None:
    pandas = PandasEngineAdapter().descriptor
    polars = PolarsEngineAdapter().descriptor

    assert PANDAS_CONFORMANCE.stability is EngineStability.STABLE
    assert POLARS_CONFORMANCE.stability is EngineStability.STABLE
    assert PANDAS_CONFORMANCE.mandatory_for_v1 is True
    assert POLARS_CONFORMANCE.mandatory_for_v1 is True

    assert pandas.capabilities == engine_capabilities("pandas")
    assert polars.capabilities == engine_capabilities("polars")
    assert pandas.capabilities >= MANDATORY_V1_CAPABILITIES
    assert polars.capabilities >= MANDATORY_V1_CAPABILITIES

    assert all(
        status is ConformanceStatus.QUALIFIED
        for _, status in PANDAS_CONFORMANCE.dimensions
    )
    assert all(
        status is ConformanceStatus.QUALIFIED
        for _, status in POLARS_CONFORMANCE.dimensions
    )


def test_optional_engines_are_published_as_provisional_without_overclaiming() -> None:
    pyarrow = PyArrowEngineAdapter().descriptor
    duckdb_adapter = DuckDBEngineAdapter()
    try:
        duckdb = duckdb_adapter.descriptor

        assert PYARROW_CONFORMANCE.stability is EngineStability.PROVISIONAL
        assert DUCKDB_CONFORMANCE.stability is EngineStability.PROVISIONAL
        assert PYARROW_CONFORMANCE.mandatory_for_v1 is False
        assert DUCKDB_CONFORMANCE.mandatory_for_v1 is False

        assert pyarrow.capabilities == engine_capabilities("pyarrow")
        assert duckdb.capabilities == engine_capabilities("duckdb")
        assert not pyarrow.capabilities >= MANDATORY_V1_CAPABILITIES
        assert not duckdb.capabilities >= MANDATORY_V1_CAPABILITIES

        assert (
            PYARROW_CONFORMANCE.status_for(ConformanceDimension.JOINS)
            is ConformanceStatus.UNSUPPORTED
        )
        assert (
            PYARROW_CONFORMANCE.status_for(ConformanceDimension.QUALITY)
            is ConformanceStatus.UNSUPPORTED
        )
        assert (
            DUCKDB_CONFORMANCE.status_for(ConformanceDimension.NESTED)
            is ConformanceStatus.UNSUPPORTED
        )
        assert (
            DUCKDB_CONFORMANCE.status_for(ConformanceDimension.QUALITY)
            is ConformanceStatus.UNSUPPORTED
        )
    finally:
        duckdb_adapter.close()


def test_published_engine_profiles_classify_every_required_dimension() -> None:
    for engine_id in ("pandas", "polars", "pyarrow", "duckdb"):
        profile = engine_profile(engine_id)
        assert {dimension for dimension, _ in profile.dimensions} == set(
            ConformanceDimension
        )
