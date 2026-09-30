from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import pytest

from pytransformkit import InputBinding, TransformationPlan, TransformationRuntime
from pytransformkit.application.execution import (
    CancellationToken,
    EngineExecutionResult,
    ExecutionContext,
    ExecutionMode,
    NamedEngineOutput,
)
from pytransformkit.application.execution.registry import EngineRegistry
from pytransformkit.application.ports import PhysicalHandle
from pytransformkit.diagnostics import (
    RuntimeEvent,
    RuntimeEventType,
    RuntimeMetric,
    RuntimeTraceSpan,
)
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import (
    CancellationSupport,
    EngineCapability,
    EngineDescriptor,
)
from pytransformkit.errors import (
    BindingError,
    EngineContractViolationError,
    ExecutionCancelledError,
    UnknownOutcomeExecutionError,
)
from pytransformkit.runtime import (
    CorrelationContext,
    CorrelationId,
    ExecutionStatus,
    FailureCategory,
    OutcomeUncertainty,
    ProviderRetryEvidence,
    RetryDecision,
    Retryability,
)


@dataclass(frozen=True, slots=True)
class FakeHandle:
    value: object
    engine_id: str = "fake"


class RecordingSink:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.events: list[RuntimeEvent] = []
        self.metrics: list[RuntimeMetric] = []
        self.spans: list[RuntimeTraceSpan] = []

    def emit_event(self, event: RuntimeEvent) -> None:
        if self.fail:
            raise RuntimeError("telemetry event sink unavailable")
        self.events.append(event)

    def record_metric(self, metric: RuntimeMetric) -> None:
        if self.fail:
            raise RuntimeError("telemetry metric sink unavailable")
        self.metrics.append(metric)

    def record_span(self, span: RuntimeTraceSpan) -> None:
        if self.fail:
            raise RuntimeError("telemetry trace sink unavailable")
        self.spans.append(span)


class EvidenceAdapter:
    def __init__(
        self,
        *,
        error: BaseException | None = None,
        provider_retries: tuple[ProviderRetryEvidence, ...] = (),
        capabilities: frozenset[EngineCapability] = frozenset(),
        cancellation_support: CancellationSupport = CancellationSupport.NONE,
        wrong_engine_output: bool = False,
    ) -> None:
        self.error = error
        self.provider_retries = provider_retries
        self.capabilities = capabilities
        self.cancellation_support = cancellation_support
        self.wrong_engine_output = wrong_engine_output
        self.execute_count = 0
        self.last_context: ExecutionContext | None = None

    @property
    def descriptor(self) -> EngineDescriptor:
        return EngineDescriptor(
            id="fake",
            name="Fake",
            adapter_version="0.3.0",
            capabilities=self.capabilities,
            cancellation_support=self.cancellation_support,
        )

    def bind_native(self, value: object) -> PhysicalHandle:
        return FakeHandle(value)

    def execute(
        self,
        plan: object,
        input_handle: PhysicalHandle,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        del plan
        return self.execute_many(
            _compiled_plan(),
            {"customers": input_handle},
            context,
        )

    def execute_many(
        self,
        plan: object,
        input_handles: Mapping[str, PhysicalHandle],
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        self.execute_count += 1
        self.last_context = context
        if self.error is not None:
            raise self.error
        logical_plan = plan
        first = next(iter(input_handles.values()))
        engine_id = "other" if self.wrong_engine_output else "fake"
        output_handle = FakeHandle(
            getattr(first, "value", first),
            engine_id=engine_id,
        )
        named = tuple(
            NamedEngineOutput(
                name=name,
                output_handle=output_handle,
                output_schema=logical_plan.schema_for_output(name),
            )
            for name in logical_plan.output_names
        )
        return EngineExecutionResult(
            output_handle=output_handle,
            output_schema=logical_plan.output_schema,
            named_outputs=named,
            provider_retries=self.provider_retries,
        )


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("status", StringType(), nullable=False),
        )
    )


def _plan() -> TransformationPlan:
    builder = TransformationPlan.builder("customers")
    source = builder.input("customers", schema=_schema())
    return builder.output("customers_out", source).build()


def _compiled_plan():
    from pytransformkit.planning import TransformationCompiler

    return TransformationCompiler().compile(_plan())


def _runtime(
    adapter: EvidenceAdapter,
    sink: RecordingSink | None = None,
) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)
    return TransformationRuntime(
        engines=registry,
        telemetry=sink,
    )


def _inputs() -> dict[str, InputBinding]:
    return {
        "customers": InputBinding.from_native(
            "customers",
            [{"customer_id": 1, "status": "ACTIVE"}],
            engine="fake",
        )
    }


def test_runtime_propagates_correlation_and_builds_execution_evidence() -> None:
    adapter = EvidenceAdapter()
    sink = RecordingSink()
    correlation = CorrelationContext(
        correlation_id=CorrelationId.new(),
        workflow_run_id="workflow-42",
        task_attempt_id="attempt-3",
        trace_id="trace-upstream",
        span_id="parent-span",
    )

    result = _runtime(adapter, sink).execute(
        _plan(),
        engine="fake",
        inputs=_inputs(),
        correlation=correlation,
    )

    assert result.status is ExecutionStatus.SUCCEEDED
    assert result.execution_id != correlation.correlation_id
    assert result.correlation.correlation_id == correlation.correlation_id
    assert result.correlation.workflow_run_id == "workflow-42"
    assert result.correlation.trace_id == "trace-upstream"
    assert result.correlation.span_id != "parent-span"
    assert adapter.last_context is not None
    assert adapter.last_context.execution_id == result.execution_id
    assert adapter.last_context.correlation == result.correlation

    assert result.plan_fingerprint == result.logical_plan.fingerprint()
    assert result.lineage.plan_id == result.logical_plan.plan_id
    assert result.manifest.execution_id == result.execution_id
    assert result.manifest.plan_fingerprint == result.plan_fingerprint
    assert result.manifest.engine_id == "fake"
    assert result.failure is None
    assert result.execution.duration_seconds is not None

    assert sink.spans[0].trace_id == "trace-upstream"
    assert sink.spans[0].parent_span_id == "parent-span"
    assert sink.spans[0].span_id == result.correlation.span_id


def test_runtime_events_cover_success_lifecycle() -> None:
    adapter = EvidenceAdapter()
    sink = RecordingSink()

    _runtime(adapter, sink).execute(
        _plan(),
        engine="fake",
        inputs=_inputs(),
    )

    event_types = [event.event_type for event in sink.events]

    assert RuntimeEventType.EXECUTION_STARTED in event_types
    assert RuntimeEventType.PLAN_COMPILED in event_types
    assert RuntimeEventType.PLAN_VALIDATED in event_types
    assert RuntimeEventType.ENGINE_SELECTED in event_types
    assert RuntimeEventType.INPUT_BOUND in event_types
    assert RuntimeEventType.ENGINE_EXECUTION_STARTED in event_types
    assert RuntimeEventType.OUTPUT_PRODUCED in event_types
    assert RuntimeEventType.EXECUTION_SUCCEEDED in event_types


def test_runtime_metrics_remain_execution_level_and_low_cardinality() -> None:
    adapter = EvidenceAdapter(capabilities=frozenset({EngineCapability.LAZY}))
    sink = RecordingSink()

    _runtime(adapter, sink).execute(
        _plan(),
        engine="fake",
        inputs=_inputs(),
        mode=ExecutionMode.LAZY,
    )

    names = {metric.name for metric in sink.metrics}

    assert "transformation_executions_total" in names
    assert "transformation_duration_seconds" in names
    assert "logical_plan_compile_duration_seconds" in names
    assert all("step" not in metric.name for metric in sink.metrics)
    assert all(
        key not in {"execution_id", "correlation_id"}
        for metric in sink.metrics
        for key, _ in metric.labels
    )


def test_telemetry_failure_never_reexecutes_transformation() -> None:
    adapter = EvidenceAdapter()
    sink = RecordingSink(fail=True)

    result = _runtime(adapter, sink).execute(
        _plan(),
        engine="fake",
        inputs=_inputs(),
    )

    assert result.status is ExecutionStatus.SUCCEEDED
    assert adapter.execute_count == 1
    assert any(
        diagnostic.code == "PTK-OBS-001"
        for diagnostic in result.diagnostics
    )


def test_missing_binding_keeps_typed_error_and_adds_failure_evidence() -> None:
    adapter = EvidenceAdapter()

    with pytest.raises(BindingError) as captured:
        _runtime(adapter).execute(
            _plan(),
            engine="fake",
            inputs={},
        )

    error = captured.value

    assert adapter.execute_count == 0
    assert error.failure_evidence is not None
    assert error.failure_evidence.category is FailureCategory.CONFIGURATION
    assert error.execution is not None
    assert error.execution.status is ExecutionStatus.FAILED
    assert error.execution.execution_id == error.failure_evidence.execution_id
    assert error.execution_manifest is not None
    assert error.execution_manifest.execution_id == error.execution.execution_id


def test_unknown_outcome_remains_first_class_and_requires_reconciliation() -> None:
    adapter = EvidenceAdapter(
        error=UnknownOutcomeExecutionError(
            "Provider confirmation was lost after a side-effecting request."
        )
    )
    sink = RecordingSink()

    with pytest.raises(UnknownOutcomeExecutionError) as captured:
        _runtime(adapter, sink).execute(
            _plan(),
            engine="fake",
            inputs=_inputs(),
        )

    error = captured.value

    assert error.execution is not None
    assert error.execution.status is ExecutionStatus.UNKNOWN_OUTCOME
    assert error.failure_evidence is not None
    assert error.failure_evidence.category is FailureCategory.UNKNOWN_OUTCOME
    assert error.failure_evidence.retryability is (
        Retryability.RETRYABLE_AFTER_RECONCILIATION
    )
    assert error.failure_evidence.uncertainty is (
        OutcomeUncertainty.REQUIRES_RECONCILIATION
    )
    assert RuntimeEventType.EXECUTION_UNKNOWN_OUTCOME in {
        event.event_type for event in sink.events
    }


def test_pre_dispatch_cancellation_is_confirmed_without_engine_execution() -> None:
    adapter = EvidenceAdapter()
    sink = RecordingSink()
    token = CancellationToken()
    token.request()

    with pytest.raises(ExecutionCancelledError) as captured:
        _runtime(adapter, sink).execute(
            _plan(),
            engine="fake",
            inputs=_inputs(),
            cancellation=token,
        )

    error = captured.value

    assert adapter.execute_count == 0
    assert error.execution is not None
    assert error.execution.status is ExecutionStatus.CANCELLED
    assert error.execution.cancellation_requested is True
    assert {
        RuntimeEventType.CANCELLATION_REQUESTED,
        RuntimeEventType.CANCELLATION_CONFIRMED,
    }.issubset({event.event_type for event in sink.events})


def test_provider_retry_evidence_is_visible_without_runtime_retry_stacking() -> None:
    retry = ProviderRetryEvidence(
        failure_domain="engine_query",
        attempt_number=2,
        decision=RetryDecision.RETRY,
        reason_code="provider_transient",
        failure_category=FailureCategory.TRANSIENT,
        retryability=Retryability.RETRYABLE,
        uncertainty=OutcomeUncertainty.KNOWN,
        delay_seconds=0.25,
    )
    adapter = EvidenceAdapter(provider_retries=(retry,))
    sink = RecordingSink()

    result = _runtime(adapter, sink).execute(
        _plan(),
        engine="fake",
        inputs=_inputs(),
    )

    assert adapter.execute_count == 1
    assert result.provider_retries == (retry,)
    assert result.manifest.provider_retries == (retry,)
    assert RuntimeEventType.PROVIDER_RETRY_RECORDED in {
        event.event_type for event in sink.events
    }
    retry_metrics = [
        metric
        for metric in sink.metrics
        if metric.name == "transformation_provider_retries_total"
    ]
    assert len(retry_metrics) == 1
    assert retry_metrics[0].value == 1.0


def test_engine_contract_violation_is_structured_without_message_parsing() -> None:
    adapter = EvidenceAdapter(wrong_engine_output=True)

    with pytest.raises(EngineContractViolationError) as captured:
        _runtime(adapter).execute(
            _plan(),
            engine="fake",
            inputs=_inputs(),
        )

    error = captured.value

    assert error.failure_evidence is not None
    assert error.failure_evidence.category is FailureCategory.CONTRACT_VIOLATION
    assert error.execution is not None
    assert error.execution.status is ExecutionStatus.FAILED
