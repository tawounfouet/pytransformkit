from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import pytest

from pytransformkit import (
    InputBinding,
    TransformationExecutionId,
    TransformationPlan,
    TransformationRuntime,
)
from pytransformkit.application.execution import (
    EngineExecutionResult,
    ExecutionContext,
    NamedEngineOutput,
)
from pytransformkit.application.execution.registry import EngineRegistry
from pytransformkit.application.ports import PhysicalHandle
from pytransformkit.domain.data.data_types import IntegerType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import EngineCapability, EngineDescriptor
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.errors import BindingError


@dataclass(frozen=True, slots=True)
class FakeHandle:
    value: object
    engine_id: str = "fake"


class FakeMultiAdapter:
    def __init__(self) -> None:
        self.execute_count = 0

    @property
    def descriptor(self) -> EngineDescriptor:
        return EngineDescriptor(
            id="fake",
            name="Fake",
            adapter_version="0.2.0a1",
            capabilities=frozenset(),
        )

    def bind_native(self, value: object) -> PhysicalHandle:
        return FakeHandle(value)

    def execute(
        self,
        plan: LogicalPlan,
        input_handle: PhysicalHandle,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        return self.execute_many(
            plan,
            {plan.input_names[0]: input_handle},
            context,
        )

    def execute_many(
        self,
        plan: LogicalPlan,
        input_handles: Mapping[str, PhysicalHandle],
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        del context
        self.execute_count += 1
        first = next(iter(input_handles.values()))
        named = tuple(
            NamedEngineOutput(
                name=name,
                output_handle=first,
                output_schema=plan.schema_for_output(name),
            )
            for name in plan.output_names
        )
        return EngineExecutionResult(
            output_handle=first,
            output_schema=plan.output_schema,
            named_outputs=named,
        )


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
        )
    )


def _plan() -> TransformationPlan:
    builder = TransformationPlan.builder("customers")
    source = builder.input("customers", schema=_schema())
    return builder.output("customers_out", source).build()


def _runtime(adapter: FakeMultiAdapter) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)
    return TransformationRuntime(engines=registry)


def test_runtime_executes_explicit_engine_with_native_binding() -> None:
    adapter = FakeMultiAdapter()
    result = _runtime(adapter).execute(
        _plan(),
        engine="fake",
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                [{"customer_id": 1}],
                engine="fake",
            )
        },
    )

    assert isinstance(result.execution_id, TransformationExecutionId)
    assert result.engine.id == "fake"
    assert result.output("customers_out").schema == _schema()
    assert result.output_handle.engine_id == "fake"
    assert adapter.execute_count == 1


def test_runtime_rejects_missing_binding_before_adapter_execution() -> None:
    adapter = FakeMultiAdapter()

    with pytest.raises(BindingError, match="missing"):
        _runtime(adapter).execute(
            _plan(),
            engine="fake",
            inputs={},
        )

    assert adapter.execute_count == 0


def test_runtime_rejects_binding_for_other_engine() -> None:
    adapter = FakeMultiAdapter()

    with pytest.raises(BindingError, match="not 'fake'"):
        _runtime(adapter).execute(
            _plan(),
            engine="fake",
            inputs={
                "customers": InputBinding.from_native(
                    "customers",
                    [{"customer_id": 1}],
                    engine="other",
                )
            },
        )

    assert adapter.execute_count == 0


def test_runtime_does_not_fallback_to_registered_engine() -> None:
    adapter = FakeMultiAdapter()
    runtime = _runtime(adapter)

    with pytest.raises(Exception, match="not registered"):
        runtime.execute(
            _plan(),
            engine="missing",
            inputs={
                "customers": InputBinding.from_native(
                    "customers",
                    [{"customer_id": 1}],
                    engine="missing",
                )
            },
        )
