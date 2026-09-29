"""Canonical PyTransformKit V1 transformation runtime."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.application.execution.bindings import (
    InputBinding,
    InputBindingKind,
    OutputBinding,
)
from pytransformkit.application.execution.compatibility import (
    EngineCompatibilityService,
)
from pytransformkit.application.execution.context import (
    ExecutionContext,
    ExecutionMode,
)
from pytransformkit.application.execution.registry import EngineRegistry
from pytransformkit.application.execution.results import EngineExecutionResult
from pytransformkit.application.planning import TransformationCompiler
from pytransformkit.application.ports.engines import (
    MultiInputEngineAdapter,
    PhysicalHandle,
)
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import EngineCapability, EngineDescriptor
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.plans import TransformationPlan
from pytransformkit.domain.shared.identifiers import TransformationExecutionId
from pytransformkit.errors.engine import (
    AdapterError,
    BindingError,
    ExecutionError,
    ResourceResolutionError,
    UnsupportedEngineCapabilityError,
)


class ExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"


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

    execution_id: TransformationExecutionId
    status: ExecutionStatus
    engine: EngineDescriptor
    logical_plan: LogicalPlan
    outputs: tuple[TransformationOutput, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.execution_id, TransformationExecutionId):
            raise TypeError(
                "TransformationResult execution_id must be "
                "a TransformationExecutionId."
            )
        if not isinstance(self.status, ExecutionStatus):
            raise TypeError("TransformationResult status must be an ExecutionStatus.")
        if not self.outputs:
            raise ValueError("TransformationResult requires at least one output.")

    def output(self, name: str) -> TransformationOutput:
        for output in self.outputs:
            if output.name == name:
                return output
        raise KeyError(name)

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
    ) -> None:
        self._engines = engines
        self._compiler = compiler or TransformationCompiler()
        self._compatibility = compatibility or EngineCompatibilityService()

    def execute(
        self,
        plan: TransformationPlan | LogicalPlan,
        *,
        engine: str,
        inputs: Mapping[str, InputBinding],
        outputs: Mapping[str, OutputBinding] | None = None,
        mode: ExecutionMode = ExecutionMode.AUTO,
    ) -> TransformationResult:
        """Execute one plan using the explicitly selected engine."""
        if not engine or not engine.strip():
            raise ValueError("engine must not be empty.")
        if not isinstance(mode, ExecutionMode):
            raise TypeError("mode must be an ExecutionMode.")

        logical_plan = (
            self._compiler.compile(plan)
            if isinstance(plan, TransformationPlan)
            else plan
        )
        if not isinstance(logical_plan, LogicalPlan):
            raise TypeError(
                "TransformationRuntime.execute requires TransformationPlan "
                "or LogicalPlan."
            )

        adapter = self._engines.get(engine)
        self._compatibility.validate(
            logical_plan,
            adapter.descriptor,
        )

        if (
            mode is ExecutionMode.LAZY
            and EngineCapability.LAZY not in adapter.descriptor.capabilities
        ):
            raise UnsupportedEngineCapabilityError(
                adapter.descriptor.id,
                (EngineCapability.LAZY.value,),
            )

        if outputs:
            raise BindingError(
                "Physical OutputBinding execution is introduced in LOT-20. "
                "LOT-11 supports in-memory/native outputs only."
            )

        handles = self._bind_inputs(
            logical_plan,
            adapter,
            inputs,
            engine,
        )
        context = ExecutionContext(mode=mode)

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

        self._validate_result_contract(
            logical_plan,
            engine_result,
            adapter.descriptor,
        )
        result_outputs = self._public_outputs(
            logical_plan,
            engine_result,
        )

        return TransformationResult(
            execution_id=context.execution_id,
            status=ExecutionStatus.SUCCEEDED,
            engine=adapter.descriptor,
            logical_plan=logical_plan,
            outputs=result_outputs,
        )

    @staticmethod
    def _bind_inputs(
        plan: LogicalPlan,
        adapter: object,
        bindings: Mapping[str, InputBinding],
        engine_id: str,
    ) -> dict[str, PhysicalHandle]:
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
        for name in plan.input_names:
            binding = bindings[name]
            if binding.input_name != name:
                raise BindingError(
                    f"Binding key {name!r} does not match "
                    f"InputBinding name {binding.input_name!r}."
                )

            if binding.kind is InputBindingKind.RESOURCE:
                raise ResourceResolutionError(
                    "ResourceReference input resolution is introduced in LOT-20."
                )

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

        return handles

    @staticmethod
    def _validate_result_contract(
        plan: LogicalPlan,
        result: EngineExecutionResult,
        descriptor: EngineDescriptor,
    ) -> None:
        if result.output_handle.engine_id != descriptor.id:
            raise ExecutionError(
                "EngineAdapter returned an output handle for a different engine."
            )

        if result.named_outputs:
            by_name = {output.name: output for output in result.named_outputs}
            if set(by_name) != set(plan.output_names):
                raise ExecutionError(
                    "EngineAdapter named outputs differ from LogicalPlan outputs."
                )
            for name in plan.output_names:
                output = by_name[name]
                if output.output_handle.engine_id != descriptor.id:
                    raise ExecutionError(
                        "EngineAdapter returned a named output handle for "
                        "a different engine."
                    )
                if output.output_schema != plan.schema_for_output(name):
                    raise ExecutionError(
                        f"EngineAdapter output Schema drift for {name!r}."
                    )
            return

        if len(plan.output_names) != 1:
            raise ExecutionError(
                "EngineAdapter omitted named outputs for a multi-output plan."
            )
        if result.output_schema != plan.output_schema:
            raise ExecutionError(
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
