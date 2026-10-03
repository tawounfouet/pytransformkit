"""Static official-engine inspection for the PyTransformKit CLI."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

from pytransformkit.cli.exceptions import CLIUsageError
from pytransformkit.cli.models.reports import (
    EngineConformanceDimensionReport,
    EngineInspectionReport,
    EngineListReport,
    EngineSummaryReport,
)
from pytransformkit.conformance.model import (
    PUBLISHED_ENGINE_PROFILES,
    engine_capabilities,
)
from pytransformkit.domain.engines import EngineCapability

VersionResolver = Callable[[str], str]


@dataclass(frozen=True, slots=True)
class _EngineRuntimeSpec:
    engine_id: str
    distribution: str
    required_distributions: tuple[str, ...]


_ENGINE_RUNTIME_SPECS: tuple[_EngineRuntimeSpec, ...] = (
    _EngineRuntimeSpec("pandas", "pandas", ("pandas",)),
    _EngineRuntimeSpec("polars", "polars", ("polars",)),
    _EngineRuntimeSpec("pyarrow", "pyarrow", ("pyarrow",)),
    _EngineRuntimeSpec("duckdb", "duckdb", ("duckdb", "pyarrow")),
)


def _runtime_spec(engine_id: str) -> _EngineRuntimeSpec:
    for spec in _ENGINE_RUNTIME_SPECS:
        if spec.engine_id == engine_id:
            return spec
    raise RuntimeError(f"Missing runtime metadata for official engine {engine_id!r}.")


class EngineService:
    """Inspect official engine metadata without importing optional engines."""

    def __init__(self, *, version_resolver: VersionResolver = version) -> None:
        self._version_resolver = version_resolver

    def list(self) -> EngineListReport:
        """Return all official engines in canonical conformance order."""
        return EngineListReport(
            engines=tuple(
                self._summary(profile.engine_id, profile.stability.value)
                for profile in PUBLISHED_ENGINE_PROFILES
            )
        )

    def inspect(self, engine_id: str) -> EngineInspectionReport:
        """Return static qualification and capability metadata for one engine."""
        normalized = engine_id.strip().lower()
        profile = next(
            (
                candidate
                for candidate in PUBLISHED_ENGINE_PROFILES
                if candidate.engine_id == normalized
            ),
            None,
        )
        if profile is None:
            known = ", ".join(
                candidate.engine_id for candidate in PUBLISHED_ENGINE_PROFILES
            )
            raise CLIUsageError(
                f"Unknown engine id {engine_id!r}. Known engines: {known}."
            )

        capabilities = engine_capabilities(profile.engine_id)
        ordered_capabilities = tuple(
            capability.value
            for capability in EngineCapability
            if capability in capabilities
        )
        dimensions = tuple(
            EngineConformanceDimensionReport(
                name=dimension.value,
                status=status.value,
            )
            for dimension, status in profile.dimensions
        )

        return EngineInspectionReport(
            engine=self._summary(profile.engine_id, profile.stability.value),
            mandatory_for_v1=profile.mandatory_for_v1,
            capabilities=ordered_capabilities,
            conformance=dimensions,
        )

    def _summary(self, engine_id: str, qualification: str) -> EngineSummaryReport:
        spec = _runtime_spec(engine_id)
        versions: dict[str, str] = {}
        missing: list[str] = []
        errors: list[str] = []

        for distribution in spec.required_distributions:
            try:
                versions[distribution] = self._version_resolver(distribution)
            except PackageNotFoundError:
                missing.append(distribution)
            except Exception as exc:
                errors.append(
                    f"{distribution} metadata lookup failed ({type(exc).__name__})."
                )

        installed = not missing and not errors
        return EngineSummaryReport(
            id=engine_id,
            installed=installed,
            qualification=qualification,
            version=versions.get(spec.distribution),
            missing_dependencies=tuple(missing),
            detail="; ".join(errors) or None,
        )


__all__ = ["EngineService"]
