"""Vendor-neutral runtime observability contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

from pytransformkit.domain.runtime.context import CorrelationContext
from pytransformkit.domain.shared.identifiers import (
    RuntimeEventId,
    TransformationExecutionId,
)

_SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "authorization",
    "credential",
    "api_key",
    "apikey",
    "private_key",
    "signed_url",
    "sas",
    "dsn",
    "sql",
    "payload",
)
_HIGH_CARDINALITY_METRIC_LABELS = frozenset(
    {
        "workflow_run_id",
        "task_run_id",
        "task_attempt_id",
        "ingestion_run_id",
        "transformation_execution_id",
        "execution_id",
        "correlation_id",
        "dataset_version_id",
        "uri",
        "url",
        "locator",
        "error_message",
        "sql",
        "sql_text",
    }
)


class RuntimeEventType(StrEnum):
    EXECUTION_STARTED = "pytransformkit.execution.started"
    PLAN_COMPILED = "pytransformkit.logical_plan.compiled"
    PLAN_VALIDATED = "pytransformkit.logical_plan.validated"
    INPUT_BOUND = "pytransformkit.input.bound"
    ENGINE_SELECTED = "pytransformkit.engine.selected"
    ENGINE_EXECUTION_STARTED = "pytransformkit.engine_execution.started"
    OUTPUT_PRODUCED = "pytransformkit.output.produced"
    EXECUTION_SUCCEEDED = "pytransformkit.execution.succeeded"
    EXECUTION_FAILED = "pytransformkit.execution.failed"
    EXECUTION_UNKNOWN_OUTCOME = "pytransformkit.execution.unknown_outcome"
    CANCELLATION_REQUESTED = "pytransformkit.cancellation.requested"
    CANCELLATION_UNSUPPORTED = "pytransformkit.cancellation.unsupported"
    CANCELLATION_UNCONFIRMED = "pytransformkit.cancellation.unconfirmed"
    CANCELLATION_CONFIRMED = "pytransformkit.cancellation.confirmed"
    PROVIDER_RETRY_RECORDED = "pytransformkit.provider_retry.recorded"


class MetricKind(StrEnum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    """Immutable lifecycle event emitted by TransformationRuntime."""

    event_type: RuntimeEventType
    execution_id: TransformationExecutionId
    correlation: CorrelationContext
    payload: tuple[tuple[str, str], ...] = ()
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    event_id: RuntimeEventId = field(default_factory=RuntimeEventId.new)
    event_version: str = "1"

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, RuntimeEventType):
            raise TypeError("RuntimeEvent event_type must be RuntimeEventType.")
        if not isinstance(self.execution_id, TransformationExecutionId):
            raise TypeError(
                "RuntimeEvent execution_id must be TransformationExecutionId."
            )
        if not isinstance(self.correlation, CorrelationContext):
            raise TypeError("RuntimeEvent correlation must be CorrelationContext.")
        _validate_pairs(self.payload, "RuntimeEvent payload")
        _validate_aware(self.occurred_at, "RuntimeEvent occurred_at")
        if not isinstance(self.event_id, RuntimeEventId):
            raise TypeError("RuntimeEvent event_id must be RuntimeEventId.")
        if not self.event_version or not self.event_version.strip():
            raise ValueError("RuntimeEvent event_version must not be empty.")


@dataclass(frozen=True, slots=True)
class RuntimeMetric:
    """Low-cardinality metric observation."""

    name: str
    value: float
    kind: MetricKind
    labels: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("RuntimeMetric name must not be empty.")
        if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
            raise TypeError("RuntimeMetric value must be numeric.")
        if not isinstance(self.kind, MetricKind):
            raise TypeError("RuntimeMetric kind must be MetricKind.")
        _validate_pairs(self.labels, "RuntimeMetric labels")
        forbidden = {
            key.lower()
            for key, _ in self.labels
            if key.lower() in _HIGH_CARDINALITY_METRIC_LABELS
        }
        if forbidden:
            raise ValueError(
                "RuntimeMetric contains high-cardinality/default-forbidden labels: "
                f"{sorted(forbidden)!r}."
            )


@dataclass(frozen=True, slots=True)
class RuntimeTraceSpan:
    """Completed vendor-neutral trace span."""

    name: str
    trace_id: str
    span_id: str
    started_at: datetime
    ended_at: datetime
    status: str
    attributes: tuple[tuple[str, str], ...] = ()
    parent_span_id: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("name", self.name),
            ("trace_id", self.trace_id),
            ("span_id", self.span_id),
            ("status", self.status),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"RuntimeTraceSpan {name} must not be empty.")
        if self.parent_span_id is not None and not self.parent_span_id.strip():
            raise ValueError("RuntimeTraceSpan parent_span_id must not be blank.")
        _validate_aware(self.started_at, "RuntimeTraceSpan started_at")
        _validate_aware(self.ended_at, "RuntimeTraceSpan ended_at")
        if self.ended_at < self.started_at:
            raise ValueError("RuntimeTraceSpan ended_at precedes started_at.")
        _validate_pairs(self.attributes, "RuntimeTraceSpan attributes")


@runtime_checkable
class TelemetrySink(Protocol):
    """Vendor-neutral best-effort telemetry sink."""

    def emit_event(self, event: RuntimeEvent) -> None: ...

    def record_metric(self, metric: RuntimeMetric) -> None: ...

    def record_span(self, span: RuntimeTraceSpan) -> None: ...


class NullTelemetrySink:
    """Default sink performing no external work."""

    def emit_event(self, event: RuntimeEvent) -> None:
        del event

    def record_metric(self, metric: RuntimeMetric) -> None:
        del metric

    def record_span(self, span: RuntimeTraceSpan) -> None:
        del span


class TelemetryRedactor:
    """Conservative redaction before telemetry crosses the runtime boundary."""

    redacted_value = "[REDACTED]"

    def redact_pairs(
        self,
        values: tuple[tuple[str, str], ...],
    ) -> tuple[tuple[str, str], ...]:
        _validate_pairs(values, "telemetry attributes")
        return tuple(
            (
                key,
                (
                    self.redacted_value
                    if self._sensitive_key(key)
                    else self._safe_value(value)
                ),
            )
            for key, value in values
        )

    @staticmethod
    def _sensitive_key(key: str) -> bool:
        normalized = key.lower()
        return any(fragment in normalized for fragment in _SENSITIVE_KEY_FRAGMENTS)

    def _safe_value(self, value: str) -> str:
        normalized = value.lower()
        if (
            "authorization=" in normalized
            or "access_token=" in normalized
            or "api_key=" in normalized
            or "sig=" in normalized
            or "signature=" in normalized
        ):
            return self.redacted_value
        return value


def _validate_pairs(values: tuple[tuple[str, str], ...], label: str) -> None:
    if not isinstance(values, tuple):
        raise TypeError(f"{label} must be a tuple.")
    for item in values:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not all(isinstance(value, str) for value in item)
        ):
            raise TypeError(f"{label} must contain string key/value pairs.")


def _validate_aware(value: datetime, label: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{label} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware.")
