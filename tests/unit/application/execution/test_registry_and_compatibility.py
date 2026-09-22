from __future__ import annotations

from dataclasses import dataclass

import pytest

from pytransformkit.application.execution import (
    EngineCapabilityAnalyzer,
    EngineCompatibilityService,
    EngineExecutionResult,
    EngineRegistry,
    ExecutionContext,
)
from pytransformkit.application.ports import DatasetHandle, EngineAdapter
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import EngineCapability, EngineDescriptor
from pytransformkit.domain.pipelines import Pipeline, PipelinePlanner
from pytransformkit.errors import (
    EngineNotFoundError,
    UnsupportedEngineCapabilityError,
)
from pytransformkit.functions import col, lower


@dataclass(frozen=True, slots=True)
class FakeHandle:
    engine_id: str = "fake"


class FakeAdapter:
    def __init__(self, descriptor: EngineDescriptor) -> None:
        self._descriptor = descriptor

    @property
    def descriptor(self) -> EngineDescriptor:
        return self._descriptor

    def execute(
        self,
        plan: object,
        input_handle: DatasetHandle,
        context: ExecutionContext,
    ) -> EngineExecutionResult:
        del plan, context
        return EngineExecutionResult(
            output_handle=input_handle,
            output_schema=_schema(),
        )


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=True),
        )
    )


def _plan():
    pipeline = (
        Pipeline.create("customers", _schema())
        .select("customer_id", "email")
        .filter(col("customer_id") > 0)
        .derive("normalized_email", lower(col("email")))
    )
    return PipelinePlanner().plan(pipeline)


def _descriptor(
    capabilities: frozenset[EngineCapability],
) -> EngineDescriptor:
    return EngineDescriptor(
        id="fake",
        name="Fake Engine",
        adapter_version="0.1.0",
        capabilities=capabilities,
    )


def test_capability_analyzer_derives_plan_requirements() -> None:
    required = EngineCapabilityAnalyzer().required_capabilities(_plan())

    assert required == frozenset(
        {
            EngineCapability.SELECT,
            EngineCapability.FILTER,
            EngineCapability.DERIVE,
        }
    )


def test_compatibility_accepts_complete_engine() -> None:
    descriptor = _descriptor(
        frozenset(
            {
                EngineCapability.SELECT,
                EngineCapability.FILTER,
                EngineCapability.DERIVE,
            }
        )
    )

    EngineCompatibilityService().validate(_plan(), descriptor)


def test_compatibility_rejects_missing_capabilities() -> None:
    descriptor = _descriptor(
        frozenset({EngineCapability.SELECT})
    )

    with pytest.raises(
        UnsupportedEngineCapabilityError
    ) as error:
        EngineCompatibilityService().validate(_plan(), descriptor)

    assert error.value.engine_id == "fake"
    assert error.value.missing_capabilities == ("derive", "filter")


def test_registry_requires_explicit_registered_engine() -> None:
    registry = EngineRegistry()

    with pytest.raises(EngineNotFoundError) as error:
        registry.get("pandas")

    assert error.value.engine_id == "pandas"


def test_registry_registers_adapter_without_fallback() -> None:
    descriptor = _descriptor(frozenset())
    adapter = FakeAdapter(descriptor)
    registry = EngineRegistry()

    registry.register(adapter)

    assert registry.contains("fake")
    assert registry.get("fake") is adapter
    assert registry.engine_ids() == ("fake",)


def test_runtime_protocols_are_structural() -> None:
    adapter = FakeAdapter(_descriptor(frozenset()))
    handle = FakeHandle()

    assert isinstance(adapter, EngineAdapter)
    assert isinstance(handle, DatasetHandle)
