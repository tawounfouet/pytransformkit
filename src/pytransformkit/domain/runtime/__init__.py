"""Portable runtime evidence contracts."""

from pytransformkit.domain.runtime.context import CorrelationContext
from pytransformkit.domain.runtime.diagnostics import (
    Diagnostic,
    DiagnosticSeverity,
)
from pytransformkit.domain.runtime.execution import (
    ExecutionManifest,
    ExecutionStatus,
    TransformationExecution,
)
from pytransformkit.domain.runtime.failure import (
    FailureCategory,
    FailureEvidence,
    OutcomeUncertainty,
    ProviderRetryEvidence,
    Retryability,
    RetryDecision,
)
from pytransformkit.domain.runtime.references import TransformationExecutionReference
from pytransformkit.domain.runtime.observability import (
    MetricKind,
    NullTelemetrySink,
    RuntimeEvent,
    RuntimeEventType,
    RuntimeMetric,
    RuntimeTraceSpan,
    TelemetryRedactor,
    TelemetrySink,
)

__all__ = [
    "CorrelationContext",
    "Diagnostic",
    "DiagnosticSeverity",
    "ExecutionManifest",
    "ExecutionStatus",
    "FailureCategory",
    "FailureEvidence",
    "MetricKind",
    "NullTelemetrySink",
    "OutcomeUncertainty",
    "ProviderRetryEvidence",
    "RetryDecision",
    "Retryability",
    "RuntimeEvent",
    "RuntimeEventType",
    "RuntimeMetric",
    "RuntimeTraceSpan",
    "TelemetryRedactor",
    "TelemetrySink",
    "TransformationExecution",
    "TransformationExecutionReference",
]
