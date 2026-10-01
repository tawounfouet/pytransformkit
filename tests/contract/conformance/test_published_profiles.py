from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")
pl = pytest.importorskip("polars")
pytest.importorskip("pyarrow")
pytest.importorskip("duckdb")

from pytransformkit.adapters.duckdb import DuckDBEngineAdapter
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.adapters.pyarrow import PyArrowEngineAdapter
from pytransformkit.conformance import (
    MANDATORY_V1_CAPABILITIES,
    PUBLISHED_ENGINE_PROFILES,
    ConformanceStatus,
    EngineStability,
    engine_profile,
)


def test_mandatory_v1_engines_are_stable_and_cover_common_capabilities() -> None:
    descriptors = {
        "pandas": PandasEngineAdapter().descriptor,
        "polars": PolarsEngineAdapter().descriptor,
    }

    for engine_id, descriptor in descriptors.items():
        profile = engine_profile(engine_id)
        assert profile.stability is EngineStability.STABLE
        assert profile.mandatory_for_v1 is True
        assert MANDATORY_V1_CAPABILITIES <= descriptor.capabilities
        assert all(
            status is ConformanceStatus.QUALIFIED
            for _, status in profile.dimensions
        )


def test_optional_engines_are_labeled_provisional_honestly() -> None:
    descriptors = {
        "pyarrow": PyArrowEngineAdapter().descriptor,
        "duckdb": DuckDBEngineAdapter().descriptor,
    }

    for engine_id, descriptor in descriptors.items():
        profile = engine_profile(engine_id)
        assert descriptor.id == engine_id
        assert profile.stability is EngineStability.PROVISIONAL
        assert profile.mandatory_for_v1 is False
        assert any(
            status is not ConformanceStatus.QUALIFIED
            for _, status in profile.dimensions
        )


def test_every_official_engine_has_exactly_one_published_profile() -> None:
    ids = tuple(profile.engine_id for profile in PUBLISHED_ENGINE_PROFILES)

    assert ids == ("pandas", "polars", "pyarrow", "duckdb")
    assert len(ids) == len(set(ids))
