"""Runtime ports implemented by physical engine adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pytransformkit.application.execution.context import ExecutionContext
from pytransformkit.domain.engines.descriptor import EngineDescriptor
from pytransformkit.domain.pipelines.plan import LogicalPlan

if TYPE_CHECKING:
    from pytransformkit.application.execution.results import EngineExecutionResult


@runtime_checkable
class PhysicalHandle(Protocol):
    """Opaque engine-owned handle to physical tabular data."""

    @property
    def engine_id(self) -> str:
        """Identifier of the engine owning this handle."""
        ...


# Pre-1.0 compatibility name.
DatasetHandle = PhysicalHandle


@runtime_checkable
class ArrowExportablePhysicalHandle(PhysicalHandle, Protocol):
    """Physical handle that can expose an Arrow Table at an explicit I/O boundary."""

    def to_arrow_table(self) -> object:
        """Materialize this handle as an Arrow-compatible table object."""
        ...


@runtime_checkable
class ArrowBindableEngineAdapter(Protocol):
    """Engine adapter capable of binding an Arrow interchange value."""

    def bind_arrow(self, value: object) -> PhysicalHandle:
        """Bind an Arrow Table/RecordBatch into an engine-owned handle."""
        ...


@runtime_checkable
class EngineAdapter(Protocol):
    """Legacy-compatible physical execution adapter contract."""

    @property
    def descriptor(self) -> EngineDescriptor:
        """Describe this adapter and its supported capabilities."""
        ...

    def execute(
        self,
        plan: LogicalPlan,
        input_handle: PhysicalHandle,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        """Execute a single-input LogicalPlan compatibility path."""
        ...


@runtime_checkable
class MultiInputEngineAdapter(Protocol):
    """V1 adapter extension for named multi-input plan execution."""

    @property
    def descriptor(self) -> EngineDescriptor: ...

    def bind_native(self, value: object) -> PhysicalHandle:
        """Wrap one engine-native value in an opaque PhysicalHandle."""
        ...

    def execute_many(
        self,
        plan: LogicalPlan,
        input_handles: Mapping[str, PhysicalHandle],
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        """Execute a LogicalPlan with explicit named physical inputs."""
        ...
