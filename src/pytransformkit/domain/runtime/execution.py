"""Transformation execution lifecycle and durable manifest evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from pytransformkit.domain.engines import CancellationSupport, EngineDescriptor
from pytransformkit.domain.runtime.context import CorrelationContext
from pytransformkit.domain.runtime.diagnostics import Diagnostic
from pytransformkit.domain.runtime.failure import (
    FailureEvidence,
    ProviderRetryEvidence,
)
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.domain.shared.identifiers import (
    TransformationExecutionId,
    TransformationPlanId,
)


class ExecutionStatus(StrEnum):
    """Transformation execution lifecycle state."""

    CREATED = "created"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    UNKNOWN_OUTCOME = "unknown_outcome"
    REQUIRES_RECONCILIATION = "requires_reconciliation"

    @property
    def terminal(self) -> bool:
        return self in {
            ExecutionStatus.SUCCEEDED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMED_OUT,
            ExecutionStatus.UNKNOWN_OUTCOME,
            ExecutionStatus.REQUIRES_RECONCILIATION,
        }


@dataclass(frozen=True, slots=True)
class TransformationExecution:
    """Immutable runtime record for one semantic TransformationRuntime execution."""

    execution_id: TransformationExecutionId
    status: ExecutionStatus
    correlation: CorrelationContext
    started_at: datetime
    ended_at: datetime | None = None
    plan_id: TransformationPlanId | None = None
    plan_fingerprint: Fingerprint | None = None
    engine: EngineDescriptor | None = None
    failure: FailureEvidence | None = None
    diagnostics: tuple[Diagnostic, ...] = ()
    provider_retries: tuple[ProviderRetryEvidence, ...] = ()
    cancellation_requested: bool = False
    cancellation_support: CancellationSupport = CancellationSupport.NONE

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, TransformationExecutionId):
            raise TypeError(
                "TransformationExecution execution_id must be "
                "a TransformationExecutionId."
            )
        if not isinstance(self.status, ExecutionStatus):
            raise TypeError(
                "TransformationExecution status must be an ExecutionStatus."
            )
        if not isinstance(self.correlation, CorrelationContext):
            raise TypeError(
                "TransformationExecution correlation must be a CorrelationContext."
            )
        _validate_aware_datetime(self.started_at, "started_at")
        if self.ended_at is not None:
            _validate_aware_datetime(self.ended_at, "ended_at")
            if self.ended_at < self.started_at:
                raise ValueError(
                    "TransformationExecution ended_at precedes started_at."
                )
        if self.plan_id is not None and not isinstance(
            self.plan_id,
            TransformationPlanId,
        ):
            raise TypeError(
                "TransformationExecution plan_id must be a TransformationPlanId."
            )
        if self.plan_fingerprint is not None and not isinstance(
            self.plan_fingerprint,
            Fingerprint,
        ):
            raise TypeError(
                "TransformationExecution plan_fingerprint must be a Fingerprint."
            )
        if self.engine is not None and not isinstance(self.engine, EngineDescriptor):
            raise TypeError(
                "TransformationExecution engine must be an EngineDescriptor."
            )
        if self.failure is not None and not isinstance(self.failure, FailureEvidence):
            raise TypeError("TransformationExecution failure must be FailureEvidence.")
        if not isinstance(self.diagnostics, tuple):
            raise TypeError("TransformationExecution diagnostics must be a tuple.")
        if any(not isinstance(item, Diagnostic) for item in self.diagnostics):
            raise TypeError(
                "TransformationExecution diagnostics must contain Diagnostic."
            )
        if not isinstance(self.provider_retries, tuple):
            raise TypeError("TransformationExecution provider_retries must be a tuple.")
        if any(
            not isinstance(item, ProviderRetryEvidence)
            for item in self.provider_retries
        ):
            raise TypeError(
                "TransformationExecution provider_retries must contain "
                "ProviderRetryEvidence."
            )
        if not isinstance(self.cancellation_requested, bool):
            raise TypeError(
                "TransformationExecution cancellation_requested must be bool."
            )
        if not isinstance(self.cancellation_support, CancellationSupport):
            raise TypeError(
                "TransformationExecution cancellation_support must be "
                "a CancellationSupport."
            )
        if self.status is ExecutionStatus.SUCCEEDED and self.failure is not None:
            raise ValueError("A succeeded TransformationExecution cannot have failure.")
        if self.status.terminal and self.ended_at is None:
            raise ValueError("Terminal TransformationExecution requires ended_at.")

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()


@dataclass(frozen=True, slots=True)
class ExecutionManifest:
    """Portable execution evidence without active handles or raw secrets."""

    framework_version: str
    execution_id: TransformationExecutionId
    correlation: CorrelationContext
    status: ExecutionStatus
    started_at: datetime
    ended_at: datetime
    input_names: tuple[str, ...]
    output_names: tuple[str, ...]
    diagnostic_codes: tuple[str, ...]
    provider_retries: tuple[ProviderRetryEvidence, ...] = ()
    plan_id: TransformationPlanId | None = None
    plan_fingerprint: Fingerprint | None = None
    engine_id: str | None = None
    adapter_version: str | None = None
    contract_version: str = "1"

    def __post_init__(self) -> None:
        if not self.framework_version or not self.framework_version.strip():
            raise ValueError("ExecutionManifest framework_version must not be empty.")
        if not isinstance(self.execution_id, TransformationExecutionId):
            raise TypeError(
                "ExecutionManifest execution_id must be a TransformationExecutionId."
            )
        if not isinstance(self.correlation, CorrelationContext):
            raise TypeError("ExecutionManifest correlation must be CorrelationContext.")
        if not isinstance(self.status, ExecutionStatus) or not self.status.terminal:
            raise ValueError("ExecutionManifest status must be terminal.")
        _validate_aware_datetime(self.started_at, "started_at")
        _validate_aware_datetime(self.ended_at, "ended_at")
        if self.ended_at < self.started_at:
            raise ValueError("ExecutionManifest ended_at precedes started_at.")
        _validate_names(self.input_names, "input_names", allow_empty=True)
        _validate_names(self.output_names, "output_names", allow_empty=True)
        _validate_names(self.diagnostic_codes, "diagnostic_codes", allow_empty=True)
        if not isinstance(self.provider_retries, tuple):
            raise TypeError("ExecutionManifest provider_retries must be a tuple.")
        if any(
            not isinstance(item, ProviderRetryEvidence)
            for item in self.provider_retries
        ):
            raise TypeError(
                "ExecutionManifest provider_retries must contain ProviderRetryEvidence."
            )
        if self.plan_id is not None and not isinstance(
            self.plan_id,
            TransformationPlanId,
        ):
            raise TypeError("ExecutionManifest plan_id must be TransformationPlanId.")
        if self.plan_fingerprint is not None and not isinstance(
            self.plan_fingerprint,
            Fingerprint,
        ):
            raise TypeError("ExecutionManifest plan_fingerprint must be Fingerprint.")
        if self.engine_id is not None and not self.engine_id.strip():
            raise ValueError("ExecutionManifest engine_id must not be blank.")
        if self.adapter_version is not None and not self.adapter_version.strip():
            raise ValueError("ExecutionManifest adapter_version must not be blank.")
        if not self.contract_version or not self.contract_version.strip():
            raise ValueError("ExecutionManifest contract_version must not be empty.")


def _validate_aware_datetime(value: datetime, name: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware.")


def _validate_names(
    values: tuple[str, ...],
    name: str,
    *,
    allow_empty: bool = False,
) -> None:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple.")
    if not allow_empty and not values:
        raise ValueError(f"{name} must not be empty.")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{name} must contain non-empty strings.")
