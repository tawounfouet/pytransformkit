"""Structured runtime diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.domain.shared.identifiers import (
    CorrelationId,
    TransformationExecutionId,
)


class DiagnosticSeverity(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """Structured evidence explaining one runtime decision or anomaly."""

    code: str
    severity: DiagnosticSeverity
    summary: str
    source_component: str | None = None
    details: tuple[tuple[str, str], ...] = ()
    location: str | None = None
    related_node: str | None = None
    related_field: str | None = None
    execution_id: TransformationExecutionId | None = None
    correlation_id: CorrelationId | None = None
    source_framework: str = "pytransformkit"

    def __post_init__(self) -> None:
        if not self.code or not self.code.strip():
            raise ValueError("Diagnostic code must not be empty.")
        if not isinstance(self.severity, DiagnosticSeverity):
            raise TypeError("Diagnostic severity must be a DiagnosticSeverity.")
        if not self.summary or not self.summary.strip():
            raise ValueError("Diagnostic summary must not be empty.")
        if self.source_component is not None and not self.source_component.strip():
            raise ValueError("Diagnostic source_component must not be blank.")
        if not isinstance(self.details, tuple):
            raise TypeError("Diagnostic details must be a tuple.")
        for item in self.details:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not all(isinstance(value, str) for value in item)
            ):
                raise TypeError(
                    "Diagnostic details must contain string key/value pairs."
                )
        for name, value in (
            ("location", self.location),
            ("related_node", self.related_node),
            ("related_field", self.related_field),
        ):
            if value is not None and not value.strip():
                raise ValueError(f"Diagnostic {name} must not be blank.")
        if self.execution_id is not None and not isinstance(
            self.execution_id,
            TransformationExecutionId,
        ):
            raise TypeError(
                "Diagnostic execution_id must be a TransformationExecutionId."
            )
        if self.correlation_id is not None and not isinstance(
            self.correlation_id,
            CorrelationId,
        ):
            raise TypeError("Diagnostic correlation_id must be a CorrelationId.")
