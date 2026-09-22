"""Application service orchestrating logical and physical execution."""

from dataclasses import dataclass

from pytransformkit.application.execution.compatibility import (
    EngineCompatibilityService,
)
from pytransformkit.application.execution.context import (
    ExecutionContext,
    ExecutionMode,
)
from pytransformkit.application.execution.registry import EngineRegistry
from pytransformkit.application.execution.results import EngineExecutionResult
from pytransformkit.application.ports.engines import DatasetHandle
from pytransformkit.domain.engines import EngineCapability, EngineDescriptor
from pytransformkit.domain.pipelines import LogicalPlan, Pipeline, PipelinePlanner
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.shared.identifiers import ExecutionId
from pytransformkit.errors.engine import (
    AdapterError,
    ExecutionError,
    UnsupportedEngineCapabilityError,
)


@dataclass(frozen=True, slots=True)
class PipelineExecutionResult:
    """Public application result of one Pipeline execution."""

    execution_id: ExecutionId
    engine: EngineDescriptor
    logical_plan: LogicalPlan
    engine_result: EngineExecutionResult

    @property
    def output_handle(self) -> DatasetHandle:
        return self.engine_result.output_handle

    @property
    def output_schema(self) -> Schema:
        return self.engine_result.output_schema


class RunPipelineService:
    """Plan, validate and execute a Pipeline on one explicit engine."""

    def __init__(
        self,
        registry: EngineRegistry,
        planner: PipelinePlanner | None = None,
        compatibility: EngineCompatibilityService | None = None,
    ) -> None:
        self._registry = registry
        self._planner = planner or PipelinePlanner()
        self._compatibility = compatibility or EngineCompatibilityService()

    def run(
        self,
        pipeline: Pipeline,
        input_handle: DatasetHandle,
        *,
        engine_id: str,
        context: ExecutionContext | None = None,
    ) -> PipelineExecutionResult:
        """Execute using exactly the engine named by engine_id."""
        if not engine_id or not engine_id.strip():
            raise ValueError("engine_id must not be empty.")

        adapter = self._registry.get(engine_id)

        if input_handle.engine_id != engine_id:
            raise AdapterError(
                f"Input handle belongs to engine {input_handle.engine_id!r}, "
                f"not requested engine {engine_id!r}."
            )

        execution_context = context or ExecutionContext()
        plan = self._planner.plan(pipeline)

        self._compatibility.validate(plan, adapter.descriptor)
        self._validate_execution_mode(
            execution_context,
            adapter.descriptor,
        )

        result = adapter.execute(
            plan,
            input_handle,
            execution_context,
        )
        self._validate_result_contract(plan, result)

        return PipelineExecutionResult(
            execution_id=execution_context.execution_id,
            engine=adapter.descriptor,
            logical_plan=plan,
            engine_result=result,
        )

    @staticmethod
    def _validate_execution_mode(
        context: ExecutionContext,
        descriptor: EngineDescriptor,
    ) -> None:
        if (
            context.mode is ExecutionMode.LAZY
            and EngineCapability.LAZY not in descriptor.capabilities
        ):
            raise UnsupportedEngineCapabilityError(
                descriptor.id,
                (EngineCapability.LAZY.value,),
            )

    @staticmethod
    def _validate_result_contract(
        plan: LogicalPlan,
        result: EngineExecutionResult,
    ) -> None:
        if result.output_handle.engine_id == "":
            raise ExecutionError(
                "EngineAdapter returned an output handle without engine_id."
            )

        if result.output_schema != plan.output_schema:
            raise ExecutionError(
                "EngineAdapter returned an output Schema that differs "
                "from the validated LogicalPlan."
            )
