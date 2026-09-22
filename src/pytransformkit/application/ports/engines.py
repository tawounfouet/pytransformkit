"""Runtime ports implemented by physical engine adapters."""

from typing import Protocol, runtime_checkable

from pytransformkit.application.execution.context import ExecutionContext
from pytransformkit.domain.engines.descriptor import EngineDescriptor
from pytransformkit.domain.pipelines.plan import LogicalPlan


@runtime_checkable
class DatasetHandle(Protocol):
    """Opaque engine-owned handle to physical tabular data."""

    @property
    def engine_id(self) -> str:
        """Identifier of the engine owning this handle."""
        ...


@runtime_checkable
class EngineAdapter(Protocol):
    """Physical execution adapter contract."""

    @property
    def descriptor(self) -> EngineDescriptor:
        """Describe this adapter and its supported capabilities."""
        ...

    def execute(
        self,
        plan: LogicalPlan,
        input_handle: DatasetHandle,
        context: ExecutionContext,
    ) -> "EngineExecutionResult":
        """Execute a validated LogicalPlan using one physical engine."""
        ...


from pytransformkit.application.execution.results import EngineExecutionResult
