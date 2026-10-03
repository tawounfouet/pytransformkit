from __future__ import annotations

from importlib.metadata import PackageNotFoundError

import pytest

from pytransformkit.cli.exceptions import CLIUsageError
from pytransformkit.cli.services.engines import EngineService
from pytransformkit.conformance.model import (
    PUBLISHED_ENGINE_PROFILES,
    engine_capabilities,
)


def _resolver(values: dict[str, str]):
    def resolve(name: str) -> str:
        try:
            return values[name]
        except KeyError as exc:
            raise PackageNotFoundError(name) from exc

    return resolve


def test_engine_list_follows_canonical_conformance_order() -> None:
    service = EngineService(
        version_resolver=_resolver(
            {
                "pandas": "2.3.0",
                "polars": "1.35.0",
                "pyarrow": "22.0.0",
                "duckdb": "1.4.1",
            }
        )
    )

    report = service.list()

    assert tuple(engine.id for engine in report.engines) == tuple(
        profile.engine_id for profile in PUBLISHED_ENGINE_PROFILES
    )
    assert all(engine.installed for engine in report.engines)
    assert [engine.qualification for engine in report.engines] == [
        "stable",
        "stable",
        "provisional",
        "provisional",
    ]


def test_engine_list_reports_known_absent_engine_without_importing_it() -> None:
    service = EngineService(
        version_resolver=_resolver(
            {
                "pandas": "2.3.0",
                "pyarrow": "22.0.0",
                "duckdb": "1.4.1",
            }
        )
    )

    report = service.list()
    polars = next(engine for engine in report.engines if engine.id == "polars")

    assert polars.installed is False
    assert polars.version is None
    assert polars.missing_dependencies == ("polars",)


def test_duckdb_requires_pyarrow_to_be_locally_available() -> None:
    service = EngineService(
        version_resolver=_resolver(
            {
                "duckdb": "1.4.1",
            }
        )
    )

    report = service.inspect("duckdb")

    assert report.engine.installed is False
    assert report.engine.version == "1.4.1"
    assert report.engine.missing_dependencies == ("pyarrow",)


def test_engine_inspect_normalizes_identifier_and_uses_conformance_capabilities() -> None:
    service = EngineService(
        version_resolver=_resolver(
            {
                "polars": "1.35.0",
            }
        )
    )

    report = service.inspect("  POLARS  ")

    assert report.engine.id == "polars"
    assert report.engine.qualification == "stable"
    assert report.mandatory_for_v1 is True
    assert set(report.capabilities) == {
        capability.value for capability in engine_capabilities("polars")
    }
    assert report.capabilities[-1] == "lazy"
    assert all(item.status == "qualified" for item in report.conformance)


def test_engine_inspect_unknown_id_is_usage_error() -> None:
    service = EngineService(version_resolver=_resolver({}))

    with pytest.raises(CLIUsageError, match="Unknown engine id"):
        service.inspect("spark")


def test_engine_metadata_failure_is_reported_without_raising() -> None:
    def broken(name: str) -> str:
        if name == "pandas":
            raise RuntimeError("metadata backend unavailable")
        raise PackageNotFoundError(name)

    report = EngineService(version_resolver=broken).inspect("pandas")

    assert report.engine.installed is False
    assert report.engine.detail == "pandas metadata lookup failed (RuntimeError)."
