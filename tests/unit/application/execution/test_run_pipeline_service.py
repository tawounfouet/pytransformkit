from __future__ import annotations

from dataclasses import dataclass

import pytest

from pytransformkit.application.execution import (
    EngineExecutionResult,
    EngineRegistry,
    ExecutionContext,
    ExecutionMode,
    RunPipelineService,
)
from pytransformkit.application.ports import DatasetHandle
from pytransformkit.domain.data.data_types import IntegerType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import EngineCapability, EngineDescriptor
from pytransformkit.domain.pipelines import LogicalPlan, Pipeline
from pytransformkit.errors import (
    AdapterError,
    ExecutionError,
    UnsupportedEngineCapabilityError,
)
from pytransformkit.functions import col


@dataclass(frozen=True, slots=True)
class FakeHandle:
    engine_id: str = "fake"


class FakeAdapter:
    def __init__(
        self,
        descriptor: EngineDescriptor,
        *,
        output_handle: DatasetHandle | None = None,
        output_schema: Schema | None = None,
    ) -> None:
        self._descriptor = descriptor
        self.output_handle = output_handle
        self.output_schema = output_schema
        self.execute_count = 0

    @property
    def descriptor(self) -> EngineDescriptor:
        return self._descriptor

    def execute(
        self,
        plan: LogicalPlan,
        input_handle: DatasetHandle,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        del context
        self.execute_count += 1
        return EngineExecutionResult(
            output_handle=self.output_handle or input_handle,
            output_schema=self.output_schema or plan.output_schema,
        )


def _schema() -> Schema:
    return Schema(
        fields=(Field("customer_id", IntegerType(), nullable=False),)
    )


def _pipeline() -> Pipeline:
    return Pipeline.create("customers", _schema()).filter(
        col("customer_id") > 0
    )


def _descriptor(
    *,
    engine_id: str = "fake",
    capabilities: frozenset[EngineCapability] | None = None,
) -> EngineDescriptor:
    if capabilities is None:
        capabilities = frozenset({EngineCapability.FILTER})

    return EngineDescriptor(
        id=engine_id,
        name="Fake Engine",
        adapter_version="0.1.0",
        capabilities=capabilities,
    )


def _service(adapter: FakeAdapter) -> RunPipelineService:
    registry = EngineRegistry()
    registry.register(adapter)
    return RunPipelineService(registry)


def test_service_executes_explicit_engine_and_returns_plan_context() -> None:
    adapter = FakeAdapter(_descriptor())
    service = _service(adapter)
    context = ExecutionContext(mode=ExecutionMode.EAGER)

    result = service.run(
        _pipeline(),
        FakeHandle(),
        engine_id="fake",
        context=context,
    )

    assert result.execution_id == context.execution_id
    assert result.engine == adapter.descriptor
    assert result.logical_plan.pipeline_name == "customers"
    assert result.output_schema == result.logical_plan.output_schema
    assert result.output_handle.engine_id == "fake"
    assert adapter.execute_count == 1


def test_service_rejects_input_handle_from_other_engine() -> None:
    adapter = FakeAdapter(_descriptor())
    service = _service(adapter)

    with pytest.raises(AdapterError, match="belongs to engine"):
        service.run(
            _pipeline(),
            FakeHandle(engine_id="other"),
            engine_id="fake",
        )

    assert adapter.execute_count == 0


def test_service_rejects_missing_plan_capability_before_execution() -> None:
    adapter = FakeAdapter(_descriptor(capabilities=frozenset()))
    service = _service(adapter)

    with pytest.raises(UnsupportedEngineCapabilityError):
        service.run(
            _pipeline(),
            FakeHandle(),
            engine_id="fake",
        )

    assert adapter.execute_count == 0


def test_service_rejects_lazy_mode_before_adapter_execution() -> None:
    adapter = FakeAdapter(_descriptor())
    service = _service(adapter)

    with pytest.raises(UnsupportedEngineCapabilityError, match="lazy"):
        service.run(
            _pipeline(),
            FakeHandle(),
            engine_id="fake",
            context=ExecutionContext(mode=ExecutionMode.LAZY),
        )

    assert adapter.execute_count == 0


def test_service_allows_lazy_when_engine_advertises_capability() -> None:
    adapter = FakeAdapter(
        _descriptor(
            capabilities=frozenset(
                {
                    EngineCapability.FILTER,
                    EngineCapability.LAZY,
                }
            )
        )
    )
    service = _service(adapter)

    result = service.run(
        _pipeline(),
        FakeHandle(),
        engine_id="fake",
        context=ExecutionContext(mode=ExecutionMode.LAZY),
    )

    assert result.output_handle.engine_id == "fake"
    assert adapter.execute_count == 1


def test_service_rejects_output_handle_for_different_engine() -> None:
    adapter = FakeAdapter(
        _descriptor(),
        output_handle=FakeHandle(engine_id="other"),
    )
    service = _service(adapter)

    with pytest.raises(ExecutionError, match="different engine"):
        service.run(
            _pipeline(),
            FakeHandle(),
            engine_id="fake",
        )


def test_service_rejects_adapter_schema_drift() -> None:
    adapter = FakeAdapter(
        _descriptor(),
        output_schema=Schema(fields=()),
    )
    service = _service(adapter)

    with pytest.raises(ExecutionError, match="output Schema"):
        service.run(
            _pipeline(),
            FakeHandle(),
            engine_id="fake",
        )


def test_service_requires_non_empty_engine_id() -> None:
    adapter = FakeAdapter(_descriptor())
    service = _service(adapter)

    with pytest.raises(ValueError, match="engine_id"):
        service.run(
            _pipeline(),
            FakeHandle(),
            engine_id=" ",
        )
