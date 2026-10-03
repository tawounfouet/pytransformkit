"""Local, side-effect-free environment diagnostics for the PyTransformKit CLI."""

from __future__ import annotations

import platform
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

from pytransformkit.cli.models.reports import (
    DoctorCheck,
    DoctorCheckStatus,
    DoctorReport,
    DoctorStatus,
)

VersionResolver = Callable[[str], str]


@dataclass(frozen=True, slots=True)
class _DependencySpec:
    check_name: str
    distribution: str
    minimum: tuple[int, int, int]
    maximum_exclusive: tuple[int, int, int]
    required: bool


_OPTIONAL_DEPENDENCIES: tuple[_DependencySpec, ...] = (
    _DependencySpec("pyyaml", "PyYAML", (6, 0, 0), (7, 0, 0), False),
    _DependencySpec("pandas", "pandas", (2, 2, 0), (4, 0, 0), False),
    _DependencySpec("polars", "polars", (1, 0, 0), (2, 0, 0), False),
    _DependencySpec("pyarrow", "pyarrow", (20, 0, 0), (26, 0, 0), False),
    _DependencySpec("duckdb", "duckdb", (1, 4, 0), (2, 0, 0), False),
)

_CLI_DEPENDENCIES: tuple[_DependencySpec, ...] = (
    _DependencySpec("typer", "typer", (0, 12, 0), (1, 0, 0), True),
    _DependencySpec("rich", "rich", (13, 0, 0), (15, 0, 0), True),
)

_RELEASE_PREFIX = re.compile(r"^\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?")


def _release_tuple(value: str) -> tuple[int, int, int] | None:
    match = _RELEASE_PREFIX.match(value)
    if match is None:
        return None
    major, minor, patch = match.groups()
    return (
        int(major),
        int(minor or "0"),
        int(patch or "0"),
    )


def _is_supported(
    installed: str,
    *,
    minimum: tuple[int, int, int],
    maximum_exclusive: tuple[int, int, int],
) -> bool:
    parsed = _release_tuple(installed)
    if parsed is None:
        return False
    return minimum <= parsed < maximum_exclusive


class DoctorService:
    """Inspect the local environment without importing optional engines."""

    def __init__(
        self,
        *,
        version_resolver: VersionResolver = version,
        python_version: str | None = None,
        python_release: tuple[int, int] | None = None,
    ) -> None:
        self._version_resolver = version_resolver
        self._python_version = python_version or platform.python_version()
        self._python_release = python_release or (
            sys.version_info.major,
            sys.version_info.minor,
        )

    def inspect(self) -> DoctorReport:
        """Return deterministic local diagnostics."""
        checks = (
            self._check_pytransformkit(),
            self._check_python(),
            self._check_cli_dependencies(),
            *(self._check_dependency(spec) for spec in _OPTIONAL_DEPENDENCIES),
        )

        required_names = {"pytransformkit", "python", "cli"}
        required_failure = any(
            check.name in required_names
            and check.status is not DoctorCheckStatus.AVAILABLE
            for check in checks
        )
        optional_degraded = any(
            check.name not in required_names
            and check.status is not DoctorCheckStatus.AVAILABLE
            for check in checks
        )

        if required_failure:
            status = DoctorStatus.ERROR
        elif optional_degraded:
            status = DoctorStatus.DEGRADED
        else:
            status = DoctorStatus.HEALTHY

        return DoctorReport(status=status, checks=checks)

    def _check_pytransformkit(self) -> DoctorCheck:
        try:
            installed = self._version_resolver("pytransformkit")
        except PackageNotFoundError:
            return DoctorCheck(
                name="pytransformkit",
                status=DoctorCheckStatus.MISSING,
                detail="PyTransformKit distribution metadata is unavailable.",
            )
        except Exception as exc:
            return DoctorCheck(
                name="pytransformkit",
                status=DoctorCheckStatus.ERROR,
                detail=f"Metadata lookup failed ({type(exc).__name__}).",
            )

        return DoctorCheck(
            name="pytransformkit",
            status=DoctorCheckStatus.AVAILABLE,
            version=installed,
        )

    def _check_python(self) -> DoctorCheck:
        supported = (3, 11) <= self._python_release < (3, 15)
        return DoctorCheck(
            name="python",
            status=(
                DoctorCheckStatus.AVAILABLE
                if supported
                else DoctorCheckStatus.INCOMPATIBLE
            ),
            version=self._python_version,
            detail=None if supported else "Supported Python range is 3.11 through 3.14.",
        )

    def _check_cli_dependencies(self) -> DoctorCheck:
        versions: list[str] = []
        statuses: list[DoctorCheckStatus] = []
        details: list[str] = []

        for spec in _CLI_DEPENDENCIES:
            check = self._check_dependency(spec)
            statuses.append(check.status)
            if check.version is not None:
                versions.append(f"{spec.check_name}={check.version}")
            if check.status is DoctorCheckStatus.MISSING:
                details.append(f"{spec.check_name} is missing")
            elif check.status is DoctorCheckStatus.INCOMPATIBLE:
                details.append(f"{spec.check_name} is incompatible")
            elif check.status is DoctorCheckStatus.ERROR:
                details.append(f"{spec.check_name} metadata lookup failed")

        if DoctorCheckStatus.ERROR in statuses:
            status = DoctorCheckStatus.ERROR
        elif DoctorCheckStatus.MISSING in statuses:
            status = DoctorCheckStatus.MISSING
        elif DoctorCheckStatus.INCOMPATIBLE in statuses:
            status = DoctorCheckStatus.INCOMPATIBLE
        else:
            status = DoctorCheckStatus.AVAILABLE

        return DoctorCheck(
            name="cli",
            status=status,
            version="; ".join(versions) or None,
            detail="; ".join(details) or None,
        )

    def _check_dependency(self, spec: _DependencySpec) -> DoctorCheck:
        try:
            installed = self._version_resolver(spec.distribution)
        except PackageNotFoundError:
            return DoctorCheck(
                name=spec.check_name,
                status=DoctorCheckStatus.MISSING,
                detail=(
                    "Required CLI dependency is not installed."
                    if spec.required
                    else "Optional dependency is not installed."
                ),
            )
        except Exception as exc:
            return DoctorCheck(
                name=spec.check_name,
                status=DoctorCheckStatus.ERROR,
                detail=f"Metadata lookup failed ({type(exc).__name__}).",
            )

        if not _is_supported(
            installed,
            minimum=spec.minimum,
            maximum_exclusive=spec.maximum_exclusive,
        ):
            minimum = ".".join(str(value) for value in spec.minimum[:2])
            maximum = ".".join(str(value) for value in spec.maximum_exclusive[:2])
            return DoctorCheck(
                name=spec.check_name,
                status=DoctorCheckStatus.INCOMPATIBLE,
                version=installed,
                detail=f"Expected >= {minimum} and < {maximum}.",
            )

        return DoctorCheck(
            name=spec.check_name,
            status=DoctorCheckStatus.AVAILABLE,
            version=installed,
        )


__all__ = ["DoctorService"]
