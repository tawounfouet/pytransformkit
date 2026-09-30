"""Portable execution-correlation context."""

from __future__ import annotations

from dataclasses import dataclass, field

from pytransformkit.domain.shared.identifiers import CorrelationId


@dataclass(frozen=True, slots=True)
class CorrelationContext:
    """Portable cross-boundary correlation metadata.

    Correlation identity groups related work while native execution identities
    remain owned by their bounded contexts.
    """

    correlation_id: CorrelationId = field(default_factory=CorrelationId.new)
    causation_id: str | None = None
    parent_execution_id: str | None = None
    workflow_run_id: str | None = None
    task_run_id: str | None = None
    task_attempt_id: str | None = None
    ingestion_run_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.correlation_id, CorrelationId):
            raise TypeError("correlation_id must be a CorrelationId.")
        for name, value in (
            ("causation_id", self.causation_id),
            ("parent_execution_id", self.parent_execution_id),
            ("workflow_run_id", self.workflow_run_id),
            ("task_run_id", self.task_run_id),
            ("task_attempt_id", self.task_attempt_id),
            ("ingestion_run_id", self.ingestion_run_id),
            ("trace_id", self.trace_id),
            ("span_id", self.span_id),
        ):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be a non-empty string when provided.")

    def with_trace(
        self,
        *,
        trace_id: str,
        span_id: str | None = None,
    ) -> "CorrelationContext":
        """Return a copy carrying explicit trace context."""
        return CorrelationContext(
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
            parent_execution_id=self.parent_execution_id,
            workflow_run_id=self.workflow_run_id,
            task_run_id=self.task_run_id,
            task_attempt_id=self.task_attempt_id,
            ingestion_run_id=self.ingestion_run_id,
            trace_id=trace_id,
            span_id=span_id,
        )
