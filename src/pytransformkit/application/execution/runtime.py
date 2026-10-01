"""Canonical PyTransformKit V1 transformation runtime."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from time import perf_counter
from uuid import uuid4

from pytransformkit.application.execution.bindings import (
    InputBinding,
    InputBindingKind,
    OutputBinding,
)
from pytransformkit.application.execution.compatibility import (
    EngineCompatibilityService,
)
from pytransformkit.application.execution.context import (
    CancellationToken,
    ExecutionContext,
    ExecutionMode,
)
from pytransformkit.application.execution.failures import (
    failure_evidence_from_exception,
)
from pytransformkit.application.execution.registry import EngineRegistry
from pytransformkit.application.execution.results import EngineExecutionResult
from pytransformkit.application.execution.telemetry import RuntimeTelemetry
from pytransformkit.application.io import (
    ReadRepresentation,
    ReadRequest,
    ResourceIORegistry,
    WriteRequest,
    WriteResult,
)
from pytransformkit.application.planning import (
    TransformationCompiler,
    logical_plan_fingerprint,
)
from pytransformkit.application.ports.engines import (
    ArrowBindableEngineAdapter,
    MultiInputEngineAdapter,
    PhysicalHandle,
)
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import (
    CancellationSupport,
    EngineCapability,
    EngineDescriptor,
)
from pytransformkit.domain.lineage import LineageAnalyzer, TransformationLineage
from pytransformkit.domain.pipelines.nodes import PipelineNodeKind
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.plans import TransformationPlan
from pytransformkit.domain.quality.results import ValidationResult
from pytransformkit.domain.resources import ResourceReference, WriteStatus
from pytransformkit.domain.runtime import (
    CorrelationContext,
    Diagnostic,
    DiagnosticSeverity,
    ExecutionManifest,
    ExecutionStatus,
    FailureCategory,
    FailureEvidence,
    MetricKind,
    NullTelemetrySink,
    ProviderRetryEvidence,
    RuntimeEventType,
    RuntimeMetric,
    RuntimeTraceSpan,
    TelemetrySink,
    TransformationExecution,
)
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.domain.shared.identifiers import (
    TransformationExecutionId,
    TransformationPlanId,
)
from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.engine import (
    AdapterError,
    BindingError,
    EngineContractViolationError,
    ExecutionCancelledError,
    ExecutionTimeoutError,
    ResourceResolutionError,
    TransformationExecutionError,
    UnknownOutcomeExecutionError,
    UnsupportedEngineCapabilityError,
)
from pytransformkit.errors.io import ResourceIOError, ResourceWriteError


@dataclass(frozen=True, slots=True)
class TransformationOutput:
    """One named output from a TransformationRuntime execution."""

    name: str
    handle: PhysicalHandle
    schema: Schema

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("TransformationOutput name must not be empty.")
        if not isinstance(self.schema, Schema):
            raise TypeError("TransformationOutput schema must be a Schema.")


@dataclass(frozen=True, slots=True)
class TransformationResult:
    """Immutable caller-facing outcome of one successful execution."""

    execution: TransformationExecution
    engine: EngineDescriptor
    logical_plan: LogicalPlan
    outputs: tuple[TransformationOutput, ...]
    lineage: TransformationLineage
    manifest: ExecutionManifest
    validations: tuple[ValidationResult, ...] = ()
    writes: tuple[WriteResult, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.execution, TransformationExecution):
            raise TypeError(
                "TransformationResult execution must be a TransformationExecution."
            )
        if self.execution.status is not ExecutionStatus.SUCCEEDED:
            raise ValueError(
                "TransformationResult currently represents successful executions."
            )
        if not isinstance(self.engine, EngineDescriptor):
            raise TypeError("TransformationResult engine must be an EngineDescriptor.")
        if self.execution.engine != self.engine:
            raise ValueError(
                "TransformationResult engine must match TransformationExecution."
            )
        if not isinstance(self.logical_plan, LogicalPlan):
            raise TypeError("TransformationResult logical_plan must be a LogicalPlan.")
        if not self.outputs:
            raise ValueError("TransformationResult requires at least one output.")
        if not isinstance(self.lineage, TransformationLineage):
            raise TypeError(
                "TransformationResult lineage must be a TransformationLineage."
            )
        if not isinstance(self.manifest, ExecutionManifest):
            raise TypeError(
                "TransformationResult manifest must be an ExecutionManifest."
            )
        if self.manifest.execution_id != self.execution.execution_id:
            raise ValueError(
                "TransformationResult manifest execution identity does not match."
            )
        if not isinstance(self.validations, tuple):
            raise TypeError("TransformationResult validations must be a tuple.")
        if any(not isinstance(result, ValidationResult) for result in self.validations):
            raise TypeError(
                "TransformationResult validations must contain ValidationResult."
            )
        if not isinstance(self.writes, tuple):
            raise TypeError("TransformationResult writes must be a tuple.")
        if any(not isinstance(result, WriteResult) for result in self.writes):
            raise TypeError("TransformationResult writes must contain WriteResult.")

    @property
    def execution_id(self) -> TransformationExecutionId:
        return self.execution.execution_id

    @property
    def status(self) -> ExecutionStatus:
        return self.execution.status

    @property
    def correlation(self) -> CorrelationContext:
        return self.execution.correlation

    @property
    def plan_fingerprint(self) -> Fingerprint:
        fingerprint = self.execution.plan_fingerprint
        if fingerprint is None:
            raise RuntimeError(
                "Successful TransformationExecution requires a plan fingerprint."
            )
        return fingerprint

    @property
    def diagnostics(self) -> tuple[Diagnostic, ...]:
        return self.execution.diagnostics

    @property
    def failure(self) -> FailureEvidence | None:
        return self.execution.failure

    @property
    def provider_retries(self) -> tuple[ProviderRetryEvidence, ...]:
        return self.execution.provider_retries

    def output(self, name: str) -> TransformationOutput:
        for output in self.outputs:
            if output.name == name:
                return output
        raise KeyError(name)

    def validation(self, gate_name: str) -> ValidationResult:
        """Return one QualityGate result by name."""
        for result in self.validations:
            if result.gate_name == gate_name:
                return result
        raise KeyError(gate_name)

    @property
    def output_handle(self) -> PhysicalHandle:
        """Compatibility convenience for single-output plans."""
        return self.outputs[0].handle

    @property
    def output_schema(self) -> Schema:
        """Compatibility convenience for single-output plans."""
        return self.outputs[0].schema


class TransformationRuntime:
    """Compile, validate and execute one plan on one explicit engine."""

    def __init__(
        self,
        *,
        engines: EngineRegistry,
        compiler: TransformationCompiler | None = None,
        compatibility: EngineCompatibilityService | None = None,
        telemetry: TelemetrySink | None = None,
        resources: ResourceIORegistry | None = None,
    ) -> None:
        self._engines = engines
        self._compiler = compiler or TransformationCompiler()
        self._compatibility = compatibility or EngineCompatibilityService()
        self._telemetry = telemetry or NullTelemetrySink()
        self._resources = resources

    def execute(
        self,
        plan: TransformationPlan | LogicalPlan,
        *,
        engine: str,
        inputs: Mapping[str, InputBinding],
        outputs: Mapping[str, OutputBinding] | None = None,
        mode: ExecutionMode = ExecutionMode.AUTO,
        correlation: CorrelationContext | None = None,
        cancellation: CancellationToken | None = None,
    ) -> TransformationResult:
        """Execute one plan using the explicitly selected engine."""
        execution_id = TransformationExecutionId.new()
        started_at = _utc_now()
        started_monotonic = perf_counter()
        invalid_correlation = correlation is not None and not isinstance(
            correlation, CorrelationContext
        )
        upstream_correlation = (
            correlation
            if isinstance(correlation, CorrelationContext)
            else CorrelationContext()
        )
        parent_span_id = upstream_correlation.span_id
        trace_id = upstream_correlation.trace_id or uuid4().hex
        span_id = uuid4().hex[:16]
        execution_correlation = upstream_correlation.with_trace(
            trace_id=trace_id,
            span_id=span_id,
        )
        telemetry = RuntimeTelemetry(self._telemetry)

        requested_plan_id = _plan_id(plan)
        logical_plan: LogicalPlan | None = None
        plan_fingerprint: Fingerprint | None = None
        descriptor: EngineDescriptor | None = None
        lineage: TransformationLineage | None = None
        provider_retries: tuple[ProviderRetryEvidence, ...] = ()
        write_results: tuple[WriteResult, ...] = ()
        input_resources: dict[str, ResourceReference] = {}
        output_resources: dict[str, ResourceReference] = {}
        runtime_diagnostics: list[Diagnostic] = []
        compile_duration = 0.0
        engine_started = False

        telemetry.emit_event(
            RuntimeEventType.EXECUTION_STARTED,
            execution_id=execution_id,
            correlation=execution_correlation,
            payload=(("mode", _safe_mode_value(mode)),),
        )

        try:
            if not engine or not engine.strip():
                raise ValueError("engine must not be empty.")
            if not isinstance(mode, ExecutionMode):
                raise TypeError("mode must be an ExecutionMode.")
            if invalid_correlation:
                raise TypeError("correlation must be a CorrelationContext.")
            if cancellation is not None and not isinstance(
                cancellation,
                CancellationToken,
            ):
                raise TypeError("cancellation must be a CancellationToken.")

            compile_started = perf_counter()
            logical_plan = (
                self._compiler.compile(plan)
                if isinstance(plan, TransformationPlan)
                else plan
            )
            compile_duration = perf_counter() - compile_started
            if not isinstance(logical_plan, LogicalPlan):
                raise TypeError(
                    "TransformationRuntime.execute requires TransformationPlan "
                    "or LogicalPlan."
                )

            requested_plan_id = logical_plan.plan_id
            plan_fingerprint = logical_plan_fingerprint(logical_plan)
            lineage = LineageAnalyzer().analyze(logical_plan)
            runtime_diagnostics.append(
                Diagnostic(
                    code="PTK-RUNTIME-001",
                    severity=DiagnosticSeverity.INFO,
                    summary="LogicalPlan compiled and fingerprinted.",
                    source_component="runtime.planning",
                    execution_id=execution_id,
                    correlation_id=execution_correlation.correlation_id,
                    details=(
                        ("fingerprint_algorithm", plan_fingerprint.algorithm),
                        ("fingerprint", plan_fingerprint.value),
                    ),
                )
            )
            telemetry.emit_event(
                RuntimeEventType.PLAN_COMPILED,
                execution_id=execution_id,
                correlation=execution_correlation,
                payload=(
                    ("fingerprint_algorithm", plan_fingerprint.algorithm),
                    ("fingerprint", plan_fingerprint.value),
                ),
            )

            adapter = self._engines.get(engine)
            descriptor = adapter.descriptor
            self._compatibility.validate(
                logical_plan,
                descriptor,
            )
            telemetry.emit_event(
                RuntimeEventType.PLAN_VALIDATED,
                execution_id=execution_id,
                correlation=execution_correlation,
                payload=(("engine", descriptor.id),),
            )

            if (
                mode is ExecutionMode.LAZY
                and EngineCapability.LAZY not in descriptor.capabilities
            ):
                raise UnsupportedEngineCapabilityError(
                    descriptor.id,
                    (EngineCapability.LAZY.value,),
                )

            runtime_diagnostics.append(
                Diagnostic(
                    code="PTK-RUNTIME-002",
                    severity=DiagnosticSeverity.INFO,
                    summary="Execution engine selected explicitly.",
                    source_component="runtime.engine_selection",
                    execution_id=execution_id,
                    correlation_id=execution_correlation.correlation_id,
                    details=(
                        ("engine", descriptor.id),
                        ("adapter_version", descriptor.adapter_version),
                    ),
                )
            )
            telemetry.emit_event(
                RuntimeEventType.ENGINE_SELECTED,
                execution_id=execution_id,
                correlation=execution_correlation,
                payload=(
                    ("engine", descriptor.id),
                    ("adapter_version", descriptor.adapter_version),
                ),
            )

            if cancellation is not None and cancellation.requested:
                telemetry.emit_event(
                    RuntimeEventType.CANCELLATION_REQUESTED,
                    execution_id=execution_id,
                    correlation=execution_correlation,
                    payload=(("phase", "before_engine_execution"),),
                )
                raise ExecutionCancelledError(
                    "Cancellation was requested before engine execution."
                )

            handles, input_resources, read_diagnostics = self._bind_inputs(
                logical_plan,
                adapter,
                inputs,
                engine,
            )
            runtime_diagnostics.extend(read_diagnostics)
            telemetry.emit_event(
                RuntimeEventType.INPUT_BOUND,
                execution_id=execution_id,
                correlation=execution_correlation,
                payload=(("input_count", str(len(handles))),),
            )

            context = ExecutionContext(
                execution_id=execution_id,
                mode=mode,
                correlation=execution_correlation,
                cancellation=cancellation,
            )
            telemetry.emit_event(
                RuntimeEventType.ENGINE_EXECUTION_STARTED,
                execution_id=execution_id,
                correlation=execution_correlation,
                payload=(("engine", descriptor.id),),
            )
            engine_started = True

            try:
                if isinstance(adapter, MultiInputEngineAdapter):
                    engine_result = adapter.execute_many(
                        logical_plan,
                        handles,
                        context,
                    )
                elif len(handles) == 1:
                    engine_result = adapter.execute(
                        logical_plan,
                        next(iter(handles.values())),
                        context,
                    )
                else:
                    raise AdapterError(
                        f"Engine {engine!r} does not implement multi-input execution."
                    )
            except TimeoutError as error:
                raise ExecutionTimeoutError("Engine execution timed out.") from error
            except PyTransformKitError:
                raise
            except Exception as error:
                raise AdapterError(
                    "Engine provider raised an unexpected execution error."
                ) from error

            provider_retries = engine_result.provider_retries
            runtime_diagnostics.extend(engine_result.diagnostics)

            self._validate_result_contract(
                logical_plan,
                engine_result,
                descriptor,
            )
            result_outputs = self._public_outputs(
                logical_plan,
                engine_result,
            )
            write_results, output_resources, write_diagnostics = self._write_outputs(
                logical_plan,
                result_outputs,
                outputs or {},
            )
            runtime_diagnostics.extend(write_diagnostics)
            lineage = LineageAnalyzer().analyze(
                logical_plan,
                input_resources=input_resources,
                output_resources=output_resources,
            )

            if cancellation is not None and cancellation.requested:
                telemetry.emit_event(
                    RuntimeEventType.CANCELLATION_REQUESTED,
                    execution_id=execution_id,
                    correlation=execution_correlation,
                    payload=(("phase", "after_engine_execution"),),
                )
                if descriptor.cancellation_support is CancellationSupport.NONE:
                    runtime_diagnostics.append(
                        Diagnostic(
                            code="PTK-RUNTIME-003",
                            severity=DiagnosticSeverity.WARNING,
                            summary=(
                                "Cancellation was requested while the selected "
                                "engine does not advertise in-flight cancellation."
                            ),
                            source_component="runtime.cancellation",
                            execution_id=execution_id,
                            correlation_id=execution_correlation.correlation_id,
                            details=(("engine", descriptor.id),),
                        )
                    )
                    telemetry.emit_event(
                        RuntimeEventType.CANCELLATION_UNSUPPORTED,
                        execution_id=execution_id,
                        correlation=execution_correlation,
                        payload=(("engine", descriptor.id),),
                    )
                else:
                    telemetry.emit_event(
                        RuntimeEventType.CANCELLATION_UNCONFIRMED,
                        execution_id=execution_id,
                        correlation=execution_correlation,
                        payload=(("engine", descriptor.id),),
                    )

            for retry in provider_retries:
                telemetry.emit_event(
                    RuntimeEventType.PROVIDER_RETRY_RECORDED,
                    execution_id=execution_id,
                    correlation=execution_correlation,
                    payload=(
                        ("retry_owner", retry.retry_owner),
                        ("failure_domain", retry.failure_domain),
                        ("attempt_number", str(retry.attempt_number)),
                        ("decision", retry.decision.value),
                    ),
                )

            ended_at = _utc_now()
            telemetry.emit_event(
                RuntimeEventType.OUTPUT_PRODUCED,
                execution_id=execution_id,
                correlation=execution_correlation,
                payload=(("output_count", str(len(result_outputs))),),
            )
            telemetry.emit_event(
                RuntimeEventType.EXECUTION_SUCCEEDED,
                execution_id=execution_id,
                correlation=execution_correlation,
                payload=(("engine", descriptor.id),),
            )
            self._record_terminal_telemetry(
                telemetry,
                execution_id=execution_id,
                correlation=execution_correlation,
                status=ExecutionStatus.SUCCEEDED,
                engine_id=descriptor.id,
                started_at=started_at,
                ended_at=ended_at,
                started_monotonic=started_monotonic,
                compile_duration=compile_duration,
                provider_retry_count=len(provider_retries),
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
            )
            runtime_diagnostics.extend(telemetry.diagnostics)

            assert lineage is not None
            execution = TransformationExecution(
                execution_id=execution_id,
                status=ExecutionStatus.SUCCEEDED,
                correlation=execution_correlation,
                started_at=started_at,
                ended_at=ended_at,
                plan_id=logical_plan.plan_id,
                plan_fingerprint=plan_fingerprint,
                engine=descriptor,
                diagnostics=tuple(runtime_diagnostics),
                provider_retries=provider_retries,
                cancellation_requested=(
                    cancellation.requested if cancellation is not None else False
                ),
                cancellation_support=descriptor.cancellation_support,
            )
            manifest = _manifest(
                execution,
                logical_plan=logical_plan,
                requested_engine=engine,
            )
            return TransformationResult(
                execution=execution,
                engine=descriptor,
                logical_plan=logical_plan,
                outputs=result_outputs,
                lineage=lineage,
                manifest=manifest,
                validations=engine_result.validations,
                writes=write_results,
            )

        except Exception as raw_error:
            normalized_error = _normalize_runtime_error(raw_error)
            ended_at = _utc_now()
            failure = failure_evidence_from_exception(
                normalized_error,
                execution_id=execution_id,
                correlation=execution_correlation,
                source_component=(
                    "runtime.engine_execution"
                    if engine_started
                    else "runtime.coordination"
                ),
            )
            status = _status_for_failure(failure)
            runtime_diagnostics.append(
                Diagnostic(
                    code=failure.error_code,
                    severity=DiagnosticSeverity.ERROR,
                    summary="Transformation execution did not complete successfully.",
                    source_component=failure.source_component,
                    execution_id=execution_id,
                    correlation_id=execution_correlation.correlation_id,
                    details=(
                        ("failure_category", failure.category.value),
                        ("retryability", failure.retryability.value),
                        ("uncertainty", failure.uncertainty.value),
                    ),
                )
            )

            event_type = RuntimeEventType.EXECUTION_FAILED
            if status is ExecutionStatus.UNKNOWN_OUTCOME:
                event_type = RuntimeEventType.EXECUTION_UNKNOWN_OUTCOME
            elif status is ExecutionStatus.CANCELLED:
                event_type = RuntimeEventType.CANCELLATION_CONFIRMED

            telemetry.emit_event(
                event_type,
                execution_id=execution_id,
                correlation=execution_correlation,
                payload=(
                    ("status", status.value),
                    ("failure_category", failure.category.value),
                ),
            )
            self._record_terminal_telemetry(
                telemetry,
                execution_id=execution_id,
                correlation=execution_correlation,
                status=status,
                engine_id=descriptor.id if descriptor is not None else engine,
                started_at=started_at,
                ended_at=ended_at,
                started_monotonic=started_monotonic,
                compile_duration=compile_duration,
                provider_retry_count=len(provider_retries),
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                failure_category=failure.category,
            )
            runtime_diagnostics.extend(telemetry.diagnostics)

            execution = TransformationExecution(
                execution_id=execution_id,
                status=status,
                correlation=execution_correlation,
                started_at=started_at,
                ended_at=ended_at,
                plan_id=requested_plan_id,
                plan_fingerprint=plan_fingerprint,
                engine=descriptor,
                failure=failure,
                diagnostics=tuple(runtime_diagnostics),
                provider_retries=provider_retries,
                cancellation_requested=(
                    cancellation.requested
                    if isinstance(cancellation, CancellationToken)
                    else False
                ),
                cancellation_support=(
                    descriptor.cancellation_support
                    if descriptor is not None
                    else CancellationSupport.NONE
                ),
            )
            manifest = _manifest(
                execution,
                logical_plan=logical_plan,
                requested_engine=engine,
            )
            normalized_error.attach_runtime_evidence(
                execution=execution,
                failure_evidence=failure,
                manifest=manifest,
                diagnostics=tuple(runtime_diagnostics),
            )
            if normalized_error is raw_error:
                raise
            raise normalized_error from raw_error

    def _bind_inputs(
        self,
        plan: LogicalPlan,
        adapter: object,
        bindings: Mapping[str, InputBinding],
        engine_id: str,
    ) -> tuple[
        dict[str, PhysicalHandle],
        dict[str, ResourceReference],
        tuple[Diagnostic, ...],
    ]:
        expected = set(plan.input_names)
        supplied = set(bindings)

        missing = sorted(expected - supplied)
        extra = sorted(supplied - expected)
        if missing or extra:
            raise BindingError(
                "Input bindings do not match LogicalPlan inputs. "
                f"missing={missing!r}, extra={extra!r}."
            )

        handles: dict[str, PhysicalHandle] = {}
        resources: dict[str, ResourceReference] = {}
        diagnostics: list[Diagnostic] = []

        for name in plan.input_names:
            binding = bindings[name]
            if binding.input_name != name:
                raise BindingError(
                    f"Binding key {name!r} does not match "
                    f"InputBinding name {binding.input_name!r}."
                )

            if binding.kind is InputBindingKind.RESOURCE:
                if binding.resource is None:
                    raise ResourceResolutionError(
                        f"Resource input {name!r} has no ResourceReference."
                    )
                if self._resources is None:
                    raise ResourceResolutionError(
                        "Resource input resolution requires ResourceIORegistry."
                    )
                if not isinstance(adapter, ArrowBindableEngineAdapter):
                    raise ResourceResolutionError(
                        f"Engine {engine_id!r} cannot bind Arrow resource reads."
                    )

                try:
                    reader = self._resources.reader_for(binding.resource.scheme)
                    read_result = reader.read(
                        ReadRequest(
                            resource=binding.resource,
                            expected_schema=_input_schema(plan, name),
                            credential=binding.credential,
                        )
                    )
                except ResourceIOError as error:
                    raise ResourceResolutionError(
                        f"Failed to resolve resource input {name!r}: {error}"
                    ) from error

                if read_result.representation is not ReadRepresentation.ARROW:
                    raise ResourceResolutionError(
                        "LOT-20 runtime only binds Arrow Reader representations."
                    )
                handle = adapter.bind_arrow(read_result.value)
                resources[name] = binding.resource
                diagnostics.extend(read_result.diagnostics)
            else:
                if binding.engine_id != engine_id:
                    raise BindingError(
                        f"Input {name!r} is bound for engine "
                        f"{binding.engine_id!r}, not {engine_id!r}."
                    )

                value = binding.native_value
                if isinstance(value, PhysicalHandle):
                    handle = value
                elif isinstance(adapter, MultiInputEngineAdapter):
                    handle = adapter.bind_native(value)
                else:
                    raise BindingError(
                        f"Engine {engine_id!r} cannot bind native input values."
                    )

            if handle.engine_id != engine_id:
                raise BindingError(
                    f"Input {name!r} resolved to engine "
                    f"{handle.engine_id!r}, not {engine_id!r}."
                )
            handles[name] = handle

        return handles, resources, tuple(diagnostics)

    def _write_outputs(
        self,
        plan: LogicalPlan,
        outputs: tuple[TransformationOutput, ...],
        bindings: Mapping[str, OutputBinding],
    ) -> tuple[
        tuple[WriteResult, ...],
        dict[str, ResourceReference],
        tuple[Diagnostic, ...],
    ]:
        if not bindings:
            return (), {}, ()

        if self._resources is None:
            raise BindingError(
                "Physical output materialization requires ResourceIORegistry."
            )

        known_outputs = set(plan.output_names)
        unknown = sorted(set(bindings) - known_outputs)
        if unknown:
            raise BindingError(
                f"Output bindings contain unknown LogicalPlan outputs: {unknown!r}."
            )

        by_name = {output.name: output for output in outputs}
        write_results: list[WriteResult] = []
        resources: dict[str, ResourceReference] = {}
        diagnostics: list[Diagnostic] = []

        for name in plan.output_names:
            if name not in bindings:
                continue

            binding = bindings[name]
            if binding.output_name != name:
                raise BindingError(
                    f"Output binding key {name!r} does not match "
                    f"OutputBinding name {binding.output_name!r}."
                )
            output = by_name[name]
            writer = self._resources.writer_for(binding.resource.scheme)
            result = writer.write(
                WriteRequest(
                    resource=binding.resource,
                    handle=output.handle,
                    schema=output.schema,
                    mode=binding.mode,
                    credential=binding.credential,
                    retry_safety=binding.retry_safety,
                )
            )
            diagnostics.extend(result.diagnostics)
            write_results.append(result)

            if result.status is WriteStatus.UNKNOWN_OUTCOME:
                raise UnknownOutcomeExecutionError(
                    "Physical output write has UNKNOWN_OUTCOME for "
                    f"{binding.resource.scheme}:{binding.resource.locator}."
                )
            if result.status is WriteStatus.FAILED:
                raise ResourceWriteError(f"Physical output write failed for {name!r}.")

            resources[name] = result.resource

        return tuple(write_results), resources, tuple(diagnostics)

    @staticmethod
    def _validate_result_contract(
        plan: LogicalPlan,
        result: EngineExecutionResult,
        descriptor: EngineDescriptor,
    ) -> None:
        if result.output_handle.engine_id != descriptor.id:
            raise EngineContractViolationError(
                "EngineAdapter returned an output handle for a different engine."
            )

        if result.named_outputs:
            by_name = {output.name: output for output in result.named_outputs}
            if set(by_name) != set(plan.output_names):
                raise EngineContractViolationError(
                    "EngineAdapter named outputs differ from LogicalPlan outputs."
                )
            for name in plan.output_names:
                output = by_name[name]
                if output.output_handle.engine_id != descriptor.id:
                    raise EngineContractViolationError(
                        "EngineAdapter returned a named output handle for "
                        "a different engine."
                    )
                if output.output_schema != plan.schema_for_output(name):
                    raise EngineContractViolationError(
                        f"EngineAdapter output Schema drift for {name!r}."
                    )
            return

        if len(plan.output_names) != 1:
            raise EngineContractViolationError(
                "EngineAdapter omitted named outputs for a multi-output plan."
            )
        if result.output_schema != plan.output_schema:
            raise EngineContractViolationError(
                "EngineAdapter returned an output Schema that differs "
                "from the validated LogicalPlan."
            )

    @staticmethod
    def _public_outputs(
        plan: LogicalPlan,
        result: EngineExecutionResult,
    ) -> tuple[TransformationOutput, ...]:
        if result.named_outputs:
            return tuple(
                TransformationOutput(
                    name=output.name,
                    handle=output.output_handle,
                    schema=output.output_schema,
                )
                for output in result.named_outputs
            )

        return (
            TransformationOutput(
                name=plan.output_names[0],
                handle=result.output_handle,
                schema=result.output_schema,
            ),
        )

    @staticmethod
    def _record_terminal_telemetry(
        telemetry: RuntimeTelemetry,
        *,
        execution_id: TransformationExecutionId,
        correlation: CorrelationContext,
        status: ExecutionStatus,
        engine_id: str,
        started_at: datetime,
        ended_at: datetime,
        started_monotonic: float,
        compile_duration: float,
        provider_retry_count: int,
        trace_id: str,
        span_id: str,
        parent_span_id: str | None,
        failure_category: FailureCategory | None = None,
    ) -> None:
        labels = (
            ("framework", "pytransformkit"),
            ("status", status.value),
            ("engine", engine_id or "unknown"),
        )
        telemetry.record_metric(
            RuntimeMetric(
                name="transformation_executions_total",
                value=1.0,
                kind=MetricKind.COUNTER,
                labels=labels,
            ),
            execution_id=execution_id,
            correlation=correlation,
        )
        telemetry.record_metric(
            RuntimeMetric(
                name="transformation_duration_seconds",
                value=max(0.0, perf_counter() - started_monotonic),
                kind=MetricKind.HISTOGRAM,
                labels=labels,
            ),
            execution_id=execution_id,
            correlation=correlation,
        )
        if compile_duration > 0:
            telemetry.record_metric(
                RuntimeMetric(
                    name="logical_plan_compile_duration_seconds",
                    value=compile_duration,
                    kind=MetricKind.HISTOGRAM,
                    labels=(("framework", "pytransformkit"),),
                ),
                execution_id=execution_id,
                correlation=correlation,
            )
        if provider_retry_count:
            telemetry.record_metric(
                RuntimeMetric(
                    name="transformation_provider_retries_total",
                    value=float(provider_retry_count),
                    kind=MetricKind.COUNTER,
                    labels=(("engine", engine_id or "unknown"),),
                ),
                execution_id=execution_id,
                correlation=correlation,
            )

        span_attributes: tuple[tuple[str, str], ...] = (
            ("framework", "pytransformkit"),
            ("engine", engine_id or "unknown"),
            ("status", status.value),
        )
        if failure_category is not None:
            span_attributes += (("failure_category", failure_category.value),)
        telemetry.record_span(
            RuntimeTraceSpan(
                name="pytransformkit.transformation.execute",
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                started_at=started_at,
                ended_at=ended_at,
                status=status.value,
                attributes=span_attributes,
            ),
            execution_id=execution_id,
            correlation=correlation,
        )


def _normalize_runtime_error(error: Exception) -> PyTransformKitError:
    if isinstance(error, PyTransformKitError):
        return error
    return TransformationExecutionError(
        f"Transformation runtime failed with {type(error).__name__}."
    )


def _status_for_failure(failure: FailureEvidence) -> ExecutionStatus:
    if failure.category is FailureCategory.CANCELLED:
        return ExecutionStatus.CANCELLED
    if failure.category is FailureCategory.TIMEOUT:
        return ExecutionStatus.TIMED_OUT
    if failure.category is FailureCategory.UNKNOWN_OUTCOME:
        return ExecutionStatus.UNKNOWN_OUTCOME
    return ExecutionStatus.FAILED


def _plan_id(
    plan: TransformationPlan | LogicalPlan,
) -> TransformationPlanId | None:
    if isinstance(plan, TransformationPlan):
        return plan.id
    if isinstance(plan, LogicalPlan):
        return plan.plan_id
    return None


def _manifest(
    execution: TransformationExecution,
    *,
    logical_plan: LogicalPlan | None,
    requested_engine: str,
) -> ExecutionManifest:
    ended_at = execution.ended_at
    if ended_at is None:
        raise ValueError("ExecutionManifest requires a terminal execution.")
    return ExecutionManifest(
        framework_version=_package_version(),
        execution_id=execution.execution_id,
        correlation=execution.correlation,
        status=execution.status,
        started_at=execution.started_at,
        ended_at=ended_at,
        input_names=logical_plan.input_names if logical_plan is not None else (),
        output_names=logical_plan.output_names if logical_plan is not None else (),
        diagnostic_codes=tuple(item.code for item in execution.diagnostics),
        provider_retries=execution.provider_retries,
        plan_id=execution.plan_id,
        plan_fingerprint=execution.plan_fingerprint,
        engine_id=(
            execution.engine.id
            if execution.engine is not None
            else (requested_engine if requested_engine.strip() else None)
        ),
        adapter_version=(
            execution.engine.adapter_version if execution.engine is not None else None
        ),
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _safe_mode_value(mode: object) -> str:
    return mode.value if isinstance(mode, ExecutionMode) else type(mode).__name__


def _package_version() -> str:
    try:
        return version("pytransformkit")
    except PackageNotFoundError:
        return "0.6.0"


def _input_schema(plan: LogicalPlan, name: str) -> Schema:
    for node in plan.nodes:
        if node.kind is PipelineNodeKind.INPUT and node.name == name:
            return node.output_schema
    raise KeyError(name)
