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
    "DoctorStatus",
    "ReportData",
    "SchemaFieldInspection",
    "SchemaInspectionReport",
    "SchemaValidationReport",
    "VersionReport",
]
