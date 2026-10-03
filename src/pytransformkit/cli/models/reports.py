"""Shared primitives for presentation-neutral CLI reports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias

ReportData: TypeAlias = dict[str, object]


@dataclass(frozen=True, slots=True)
class VersionReport:
    """Installed PyTransformKit and Python version metadata."""

    pytransformkit: str
    python: str

    def to_data(self) -> ReportData:
        """Return the machine-facing version report payload."""
        return {
            "pytransformkit": self.pytransformkit,
            "python": self.python,
        }


class DoctorCheckStatus(StrEnum):
    """Status of one local diagnostic check."""

    AVAILABLE = "available"
    MISSING = "missing"
    INCOMPATIBLE = "incompatible"
    ERROR = "error"
    NOT_APPLICABLE = "not_applicable"


class DoctorStatus(StrEnum):
    """Aggregate doctor status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    """One deterministic local environment diagnostic."""

    name: str
    status: DoctorCheckStatus
    version: str | None = None
    detail: str | None = None

    def to_data(self) -> dict[str, object]:
        """Return the machine-facing check payload."""
        payload: dict[str, object] = {
            "name": self.name,
            "status": self.status.value,
        }
        if self.version is not None:
            payload["version"] = self.version
        if self.detail is not None:
            payload["detail"] = self.detail
        return payload




@dataclass(frozen=True, slots=True)
class ContractSummaryReport:
    """One inspectable PyTransformKit contract summary."""

    id: str
    status: str
    version: str
    description: str

    def to_data(self) -> dict[str, object]:
        """Return the machine-facing contract summary payload."""
        return {
            "id": self.id,
            "status": self.status,
            "version": self.version,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class ContractListReport:
    """Deterministic catalogue of inspectable contracts."""

    contracts: tuple[ContractSummaryReport, ...]

    def to_data(self) -> ReportData:
        """Return the machine-facing contract catalogue payload."""
        return {
            "contracts": [contract.to_data() for contract in self.contracts],
        }


@dataclass(frozen=True, slots=True)
class ContractInspectionReport:
    """Detailed inspection of one packaged/runtime contract."""

    contract: ContractSummaryReport
    document: dict[str, object]

    def to_data(self) -> ReportData:
        """Return the machine-facing contract inspection payload."""
        payload = self.contract.to_data()
        payload["document"] = self.document
        return payload


@dataclass(frozen=True, slots=True)
class EngineSummaryReport:
    """One official engine's installation and qualification summary."""

    id: str
    installed: bool
    qualification: str
    version: str | None = None
    missing_dependencies: tuple[str, ...] = ()
    detail: str | None = None

    def to_data(self) -> dict[str, object]:
        """Return the machine-facing engine summary payload."""
        payload: dict[str, object] = {
            "id": self.id,
            "installed": self.installed,
            "qualification": self.qualification,
        }
        if self.version is not None:
            payload["version"] = self.version
        if self.missing_dependencies:
            payload["missing_dependencies"] = list(self.missing_dependencies)
        if self.detail is not None:
            payload["detail"] = self.detail
        return payload


@dataclass(frozen=True, slots=True)
class EngineListReport:
    """Deterministic list of official engine summaries."""

    engines: tuple[EngineSummaryReport, ...]

    def to_data(self) -> ReportData:
        """Return the machine-facing engine list payload."""
        return {"engines": [engine.to_data() for engine in self.engines]}


@dataclass(frozen=True, slots=True)
class EngineConformanceDimensionReport:
    """One published conformance dimension for an official engine."""

    name: str
    status: str

    def to_data(self) -> dict[str, object]:
        """Return the machine-facing conformance dimension payload."""
        return {"name": self.name, "status": self.status}


@dataclass(frozen=True, slots=True)
class EngineInspectionReport:
    """Detailed static inspection of one official engine."""

    engine: EngineSummaryReport
    mandatory_for_v1: bool
    capabilities: tuple[str, ...]
    conformance: tuple[EngineConformanceDimensionReport, ...]

    def to_data(self) -> ReportData:
        """Return the machine-facing engine inspection payload."""
        payload = self.engine.to_data()
        payload["mandatory_for_v1"] = self.mandatory_for_v1
        payload["capabilities"] = list(self.capabilities)
        payload["conformance"] = [dimension.to_data() for dimension in self.conformance]
        return payload


@dataclass(frozen=True, slots=True)
class SchemaValidationReport:
    """Result of validating one explicit declarative schema file."""

    path: str
    valid: bool

    def to_data(self) -> ReportData:
        """Return the machine-facing schema validation payload."""
        return {
            "path": self.path,
            "valid": self.valid,
        }


@dataclass(frozen=True, slots=True)
class SchemaFieldInspection:
    """Presentation-neutral description of one logical schema field."""

    name: str
    type: str
    nullable: bool
    description: str | None
    type_details: dict[str, object] | None = None

    def to_data(self) -> dict[str, object]:
        """Return the machine-facing field inspection payload."""
        payload: dict[str, object] = {
            "name": self.name,
            "type": self.type,
            "nullable": self.nullable,
            "description": self.description,
        }
        if self.type_details is not None:
            payload["type_details"] = self.type_details
        return payload


@dataclass(frozen=True, slots=True)
class SchemaInspectionReport:
    """Inspection report for one explicit declarative schema."""

    path: str
    schema_name: str
    fields: tuple[SchemaFieldInspection, ...]

    def to_data(self) -> ReportData:
        """Return the machine-facing schema inspection payload."""
        return {
            "path": self.path,
            "schema": {
                "name": self.schema_name,
                "fields": [field.to_data() for field in self.fields],
            },
        }


@dataclass(frozen=True, slots=True)
class DoctorReport:
    """Aggregate local CLI environment diagnostics."""

    status: DoctorStatus
    checks: tuple[DoctorCheck, ...]

    @property
    def is_fatal(self) -> bool:
        """Return whether required local prerequisites are unhealthy."""
        return self.status is DoctorStatus.ERROR

    def to_data(self) -> ReportData:
        """Return the machine-facing doctor report payload."""
        return {
            "status": self.status.value,
            "checks": [check.to_data() for check in self.checks],
        }


__all__ = [
    "DoctorCheck",
    "DoctorCheckStatus",
    "DoctorReport",
    "ContractInspectionReport",
    "ContractListReport",
    "ContractSummaryReport",
    "DoctorStatus",
    "EngineConformanceDimensionReport",
    "EngineInspectionReport",
    "EngineListReport",
    "EngineSummaryReport",
    "ReportData",
    "SchemaFieldInspection",
    "SchemaInspectionReport",
    "SchemaValidationReport",
    "VersionReport",
]
