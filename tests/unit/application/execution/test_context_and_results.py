from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass

import pytest

from pytransformkit.application.execution import (
    EngineExecutionResult,
    ExecutionContext,
    ExecutionMode,
)
from pytransformkit.domain.data.data_types import StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.shared.identifiers import ExecutionId


@dataclass(frozen=True, slots=True)
class FakeHandle:
    engine_id: str = "fake"


def test_execution_context_generates_unique_identity() -> None:
    first = ExecutionContext()
    second = ExecutionContext()

    assert isinstance(first.execution_id, ExecutionId)
    assert first.execution_id != second.execution_id
    assert first.mode is ExecutionMode.AUTO


def test_execution_context_is_immutable() -> None:
    context = ExecutionContext(mode=ExecutionMode.EAGER)

    with pytest.raises(FrozenInstanceError):
        context.mode = ExecutionMode.LAZY  # type: ignore[misc]


def test_engine_execution_result_preserves_handle_and_schema() -> None:
    schema = Schema(fields=(Field("email", StringType()),))
    handle = FakeHandle()

    result = EngineExecutionResult(
        output_handle=handle,
        output_schema=schema,
    )

    assert result.output_handle is handle
    assert result.output_schema is schema
