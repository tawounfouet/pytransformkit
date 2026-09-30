"""Structured failure, uncertainty and retry evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from pytransformkit.domain.shared.identifiers import (
    CorrelationId,
    TransformationExecutionId,
)


class FailureCategory(StrEnum):
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    CAPABILITY = "capability"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    TRANSIENT = "transient"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    RATE_LIMITED = "rate_limited"
    INTEGRITY = "integrity"
    CONTRACT_VIOLATION = "contract_violation"
    SIDE_EFFECT_FAILED = "side_effect_failed"
    UNKNOWN_OUTCOME = "unknown_outcome"
    INTERNAL = "internal"
    EXTERNAL_PROVIDER = "external_provider"


class Retryability(StrEnum):
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"
    UNKNOWN = "unknown"
    RETRYABLE_AFTER_RECONCILIATION = "retryable_after_reconciliation"


class OutcomeUncertainty(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    REQUIRES_RECONCILIATION = "requires_reconciliation"


class RetryDecision(StrEnum):
    RETRY = "retry"
    DO_NOT_RETRY = "do_not_retry"
    RECONCILE = "reconcile"
    ABORT = "abort"
    CANCEL = "cancel"
    ESCALATE = "escalate"


@dataclass(frozen=True, slots=True)
class ProviderRetryEvidence:
    """Evidence for one bounded provider/engine retry decision."""

    failure_domain: str
    attempt_number: int
    decision: RetryDecision
    reason_code: str
    failure_category: FailureCategory
    retryability: Retryability
    uncertainty: OutcomeUncertainty
    delay_seconds: float | None = None
    retry_owner: str = "pytransformkit"

    def __post_init__(self) -> None:
        if not self.failure_domain or not self.failure_domain.strip():
            raise ValueError("failure_domain must not be empty.")
        if self.attempt_number < 1:
            raise ValueError("attempt_number must be >= 1.")
        if not isinstance(self.decision, RetryDecision):
            raise TypeError("decision must be a RetryDecision.")
        if not self.reason_code or not self.reason_code.strip():
            raise ValueError("reason_code must not be empty.")
        if not isinstance(self.failure_category, FailureCategory):
            raise TypeError("failure_category must be a FailureCategory.")
        if not isinstance(self.retryability, Retryability):
            raise TypeError("retryability must be a Retryability.")
        if not isinstance(self.uncertainty, OutcomeUncertainty):
            raise TypeError("uncertainty must be an OutcomeUncertainty.")
        if self.delay_seconds is not None and self.delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative.")
        if not self.retry_owner or not self.retry_owner.strip():
            raise ValueError("retry_owner must not be empty.")


@dataclass(frozen=True, slots=True)
class FailureEvidence:
    """Durable machine-readable evidence for one failed/uncertain execution."""

    error_code: str
    category: FailureCategory
    retryability: Retryability
    uncertainty: OutcomeUncertainty
    execution_id: TransformationExecutionId
    correlation_id: CorrelationId
    source_framework: str = "pytransformkit"
    source_component: str | None = None
    provider_code: str | None = None
    message_summary: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    details: tuple[tuple[str, str], ...] = ()
    contract_version: str = "1"

    def __post_init__(self) -> None:
        if not self.error_code or not self.error_code.strip():
            raise ValueError("error_code must not be empty.")
        if not isinstance(self.category, FailureCategory):
            raise TypeError("category must be a FailureCategory.")
        if not isinstance(self.retryability, Retryability):
            raise TypeError("retryability must be a Retryability.")
        if not isinstance(self.uncertainty, OutcomeUncertainty):
            raise TypeError("uncertainty must be an OutcomeUncertainty.")
        if not isinstance(self.execution_id, TransformationExecutionId):
            raise TypeError("execution_id must be a TransformationExecutionId.")
        if not isinstance(self.correlation_id, CorrelationId):
            raise TypeError("correlation_id must be a CorrelationId.")
        if not self.source_framework or not self.source_framework.strip():
            raise ValueError("source_framework must not be empty.")
        if self.source_component is not None and not self.source_component.strip():
            raise ValueError("source_component must not be blank.")
        if self.provider_code is not None and not self.provider_code.strip():
            raise ValueError("provider_code must not be blank.")
        if self.message_summary is not None and not self.message_summary.strip():
            raise ValueError("message_summary must not be blank.")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware.")
        if not isinstance(self.details, tuple):
            raise TypeError("details must be a tuple.")
        for item in self.details:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not all(isinstance(value, str) for value in item)
            ):
                raise TypeError("details must contain string key/value pairs.")
        if not self.contract_version or not self.contract_version.strip():
            raise ValueError("contract_version must not be empty.")
