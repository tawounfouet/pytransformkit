"""Best-effort telemetry dispatch isolated from business execution."""

from __future__ import annotations

from pytransformkit.domain.runtime import (
    CorrelationContext,
    Diagnostic,
    DiagnosticSeverity,
    RuntimeEvent,
    RuntimeEventType,
    RuntimeMetric,
    RuntimeTraceSpan,
    TelemetryRedactor,
    TelemetrySink,
)
from pytransformkit.domain.shared.identifiers import TransformationExecutionId


class RuntimeTelemetry:
    """Emit sanitized telemetry without letting sink failures replay work."""

    def __init__(
        self,
        sink: TelemetrySink,
        *,
        redactor: TelemetryRedactor | None = None,
    ) -> None:
        self._sink = sink
        self._redactor = redactor or TelemetryRedactor()
        self._diagnostics: list[Diagnostic] = []

    @property
    def diagnostics(self) -> tuple[Diagnostic, ...]:
        return tuple(self._diagnostics)

    def emit_event(
        self,
        event_type: RuntimeEventType,
        *,
        execution_id: TransformationExecutionId,
        correlation: CorrelationContext,
        payload: tuple[tuple[str, str], ...] = (),
    ) -> None:
        event = RuntimeEvent(
            event_type=event_type,
            execution_id=execution_id,
            correlation=correlation,
            payload=self._redactor.redact_pairs(payload),
        )
        try:
            self._sink.emit_event(event)
        except Exception as error:  # noqa: BLE001 - telemetry must remain isolated.
            self._record_failure(
                operation="event",
                error=error,
                execution_id=execution_id,
                correlation=correlation,
            )

    def record_metric(
        self,
        metric: RuntimeMetric,
        *,
        execution_id: TransformationExecutionId,
        correlation: CorrelationContext,
    ) -> None:
        sanitized = RuntimeMetric(
            name=metric.name,
            value=metric.value,
            kind=metric.kind,
            labels=self._redactor.redact_pairs(metric.labels),
        )
        try:
            self._sink.record_metric(sanitized)
        except Exception as error:  # noqa: BLE001 - telemetry must remain isolated.
            self._record_failure(
                operation="metric",
                error=error,
                execution_id=execution_id,
                correlation=correlation,
            )

    def record_span(
        self,
        span: RuntimeTraceSpan,
        *,
        execution_id: TransformationExecutionId,
        correlation: CorrelationContext,
    ) -> None:
        sanitized = RuntimeTraceSpan(
            name=span.name,
            trace_id=span.trace_id,
            span_id=span.span_id,
            parent_span_id=span.parent_span_id,
            started_at=span.started_at,
            ended_at=span.ended_at,
            status=span.status,
            attributes=self._redactor.redact_pairs(span.attributes),
        )
        try:
            self._sink.record_span(sanitized)
        except Exception as error:  # noqa: BLE001 - telemetry must remain isolated.
            self._record_failure(
                operation="trace",
                error=error,
                execution_id=execution_id,
                correlation=correlation,
            )

    def _record_failure(
        self,
        *,
        operation: str,
        error: BaseException,
        execution_id: TransformationExecutionId,
        correlation: CorrelationContext,
    ) -> None:
        self._diagnostics.append(
            Diagnostic(
                code="PTK-OBS-001",
                severity=DiagnosticSeverity.WARNING,
                summary=(
                    "Telemetry delivery failed; transformation execution continued."
                ),
                source_component="runtime.telemetry",
                execution_id=execution_id,
                correlation_id=correlation.correlation_id,
                details=(
                    ("operation", operation),
                    ("sink_type", type(self._sink).__name__),
                    ("exception_type", type(error).__name__),
                ),
            )
        )
