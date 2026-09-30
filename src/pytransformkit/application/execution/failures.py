"""Mapping native exceptions into stable runtime failure evidence."""

from __future__ import annotations

from pytransformkit.domain.runtime.context import CorrelationContext
from pytransformkit.domain.runtime.failure import (
    FailureCategory,
    FailureEvidence,
    OutcomeUncertainty,
    Retryability,
)
from pytransformkit.domain.shared.identifiers import TransformationExecutionId
from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.engine import (
    AdapterError,
    BindingError,
    EngineContractViolationError,
    EngineNotFoundError,
    ExecutionCancelledError,
    ExecutionError,
    ExecutionTimeoutError,
    ResourceResolutionError,
    UnknownOutcomeExecutionError,
    UnsupportedEngineCapabilityError,
)
from pytransformkit.errors.quality import QualityGateError


def failure_evidence_from_exception(
    error: BaseException,
    *,
    execution_id: TransformationExecutionId,
    correlation: CorrelationContext,
    source_component: str,
) -> FailureEvidence:
    """Map one exception to stable PyTransformKit failure semantics."""
    category, retryability, uncertainty = _classification(error)
    error_code = (
        str(error.code) if isinstance(error, PyTransformKitError) else "PTK-EXEC-500"
    )
    provider_code = getattr(error, "provider_code", None)
    if provider_code is not None and not isinstance(provider_code, str):
        provider_code = str(provider_code)

    message = str(error).strip() or type(error).__name__
    return FailureEvidence(
        error_code=error_code,
        category=category,
        retryability=retryability,
        uncertainty=uncertainty,
        execution_id=execution_id,
        correlation_id=correlation.correlation_id,
        source_component=source_component,
        provider_code=provider_code,
        message_summary=message,
        details=(("exception_type", type(error).__name__),),
    )


def _classification(
    error: BaseException,
) -> tuple[FailureCategory, Retryability, OutcomeUncertainty]:
    if isinstance(error, UnknownOutcomeExecutionError):
        return (
            FailureCategory.UNKNOWN_OUTCOME,
            Retryability.RETRYABLE_AFTER_RECONCILIATION,
            OutcomeUncertainty.REQUIRES_RECONCILIATION,
        )
    if isinstance(error, ExecutionCancelledError):
        return (
            FailureCategory.CANCELLED,
            Retryability.NON_RETRYABLE,
            OutcomeUncertainty.KNOWN,
        )
    if isinstance(error, (ExecutionTimeoutError, TimeoutError)):
        return (
            FailureCategory.TIMEOUT,
            Retryability.UNKNOWN,
            OutcomeUncertainty.UNKNOWN,
        )
    if isinstance(error, QualityGateError):
        return (
            FailureCategory.VALIDATION,
            Retryability.NON_RETRYABLE,
            OutcomeUncertainty.KNOWN,
        )
    if isinstance(error, UnsupportedEngineCapabilityError):
        return (
            FailureCategory.CAPABILITY,
            Retryability.NON_RETRYABLE,
            OutcomeUncertainty.KNOWN,
        )
    if isinstance(error, ResourceResolutionError):
        return (
            FailureCategory.NOT_FOUND,
            Retryability.UNKNOWN,
            OutcomeUncertainty.KNOWN,
        )
    if isinstance(error, (EngineNotFoundError, BindingError)):
        return (
            FailureCategory.CONFIGURATION,
            Retryability.NON_RETRYABLE,
            OutcomeUncertainty.KNOWN,
        )
    if isinstance(error, EngineContractViolationError):
        return (
            FailureCategory.CONTRACT_VIOLATION,
            Retryability.NON_RETRYABLE,
            OutcomeUncertainty.KNOWN,
        )
    if isinstance(error, AdapterError):
        return (
            FailureCategory.EXTERNAL_PROVIDER,
            Retryability.UNKNOWN,
            OutcomeUncertainty.KNOWN,
        )
    if isinstance(error, ExecutionError):
        return (
            FailureCategory.INTERNAL,
            Retryability.UNKNOWN,
            OutcomeUncertainty.KNOWN,
        )
    if isinstance(error, PyTransformKitError):
        return (
            FailureCategory.VALIDATION,
            Retryability.NON_RETRYABLE,
            OutcomeUncertainty.KNOWN,
        )
    return (
        FailureCategory.EXTERNAL_PROVIDER,
        Retryability.UNKNOWN,
        OutcomeUncertainty.KNOWN,
    )
