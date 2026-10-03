from __future__ import annotations

from importlib.metadata import PackageNotFoundError

from pytransformkit.cli.models.reports import DoctorCheckStatus, DoctorStatus
from pytransformkit.cli.services.doctor import DoctorService

ALL_VERSIONS = {
    "pytransformkit": "1.2.0a3",
    "typer": "0.20.0",
    "rich": "14.2.0",
    "PyYAML": "6.0.3",
    "pandas": "2.2.3",
    "polars": "1.35.0",
    "pyarrow": "25.0.0",
    "duckdb": "1.4.1",
}


def _resolver(
    versions: dict[str, str],
    *,
    error_for: str | None = None,
):
    def resolve(name: str) -> str:
        if name == error_for:
            raise RuntimeError("SECRET_DIAGNOSTIC_VALUE")
        try:
            return versions[name]
        except KeyError as exc:
            raise PackageNotFoundError(name) from exc

    return resolve


def test_doctor_is_healthy_when_all_checks_are_available() -> None:
    report = DoctorService(
        version_resolver=_resolver(ALL_VERSIONS),
        python_version="3.14.0",
        python_release=(3, 14),
    ).inspect()

    assert report.status is DoctorStatus.HEALTHY
    assert [check.name for check in report.checks] == [
        "pytransformkit",
        "python",
        "cli",
        "pyyaml",
        "pandas",
        "polars",
        "pyarrow",
        "duckdb",
    ]
    assert all(
        check.status is DoctorCheckStatus.AVAILABLE for check in report.checks
    )


def test_missing_optional_dependency_degrades_without_fatal_error() -> None:
    versions = dict(ALL_VERSIONS)
    versions.pop("pandas")

    report = DoctorService(
        version_resolver=_resolver(versions),
        python_release=(3, 13),
    ).inspect()

    pandas = next(check for check in report.checks if check.name == "pandas")
    assert report.status is DoctorStatus.DEGRADED
    assert report.is_fatal is False
    assert pandas.status is DoctorCheckStatus.MISSING


def test_incompatible_optional_dependency_degrades_report() -> None:
    versions = dict(ALL_VERSIONS)
    versions["pandas"] = "4.0.0"

    report = DoctorService(
        version_resolver=_resolver(versions),
        python_release=(3, 13),
    ).inspect()

    pandas = next(check for check in report.checks if check.name == "pandas")
    assert report.status is DoctorStatus.DEGRADED
    assert pandas.status is DoctorCheckStatus.INCOMPATIBLE


def test_missing_required_cli_dependency_is_fatal() -> None:
    versions = dict(ALL_VERSIONS)
    versions.pop("typer")

    report = DoctorService(
        version_resolver=_resolver(versions),
        python_release=(3, 13),
    ).inspect()

    cli = next(check for check in report.checks if check.name == "cli")
    assert report.status is DoctorStatus.ERROR
    assert report.is_fatal is True
    assert cli.status is DoctorCheckStatus.MISSING


def test_unsupported_python_is_fatal() -> None:
    report = DoctorService(
        version_resolver=_resolver(ALL_VERSIONS),
        python_version="3.15.0",
        python_release=(3, 15),
    ).inspect()

    python = next(check for check in report.checks if check.name == "python")
    assert report.status is DoctorStatus.ERROR
    assert python.status is DoctorCheckStatus.INCOMPATIBLE


def test_metadata_error_is_sanitized_and_does_not_leak_raw_message() -> None:
    report = DoctorService(
        version_resolver=_resolver(ALL_VERSIONS, error_for="pandas"),
        python_release=(3, 13),
    ).inspect()

    pandas = next(check for check in report.checks if check.name == "pandas")
    assert report.status is DoctorStatus.DEGRADED
    assert pandas.status is DoctorCheckStatus.ERROR
    assert pandas.detail == "Metadata lookup failed (RuntimeError)."
    assert "SECRET_DIAGNOSTIC_VALUE" not in (pandas.detail or "")
