"""PyTransformKit public package."""

from __future__ import annotations

import warnings
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from pytransformkit.application.execution import (
    InputBinding,
    OutputBinding,
    TransformationResult,
    TransformationRuntime,
)
from pytransformkit.domain.data.data_types import DataType
from pytransformkit.domain.data.dataset import Dataset
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.plans import TransformationPlan
from pytransformkit.domain.resources import ResourceReference
from pytransformkit.domain.shared.identifiers import TransformationExecutionId
from pytransformkit.functions import col, lit

try:
    __version__ = version("pytransformkit")
except PackageNotFoundError:
    __version__ = "0.2.0a2"

__all__ = [
    "DataType",
    "Dataset",
    "Expression",
    "Field",
    "InputBinding",
    "LogicalPlan",
    "OutputBinding",
    "ResourceReference",
    "Schema",
    "TransformationExecutionId",
    "TransformationPlan",
    "TransformationResult",
    "TransformationRuntime",
    "__version__",
    "col",
    "lit",
]


def __getattr__(name: str) -> Any:
    """Resolve pre-V1 compatibility names without making them canonical."""
    if name == "Pipeline":
        from pytransformkit.domain.pipelines.pipeline import Pipeline

        _warn_legacy(name, "TransformationPlan")
        return Pipeline

    if name in {
        "EngineRegistry",
        "ExecutionContext",
        "ExecutionMode",
        "PipelineExecutionResult",
        "RunPipelineService",
    }:
        from pytransformkit.application import execution

        replacement = {
            "EngineRegistry": "pytransformkit.engines.EngineRegistry",
            "ExecutionContext": "TransformationRuntime.execute(..., mode=...)",
            "ExecutionMode": "pytransformkit.runtime.ExecutionMode",
            "PipelineExecutionResult": "TransformationResult",
            "RunPipelineService": "TransformationRuntime",
        }[name]
        _warn_legacy(name, replacement)
        return getattr(execution, name)

    raise AttributeError(f"module 'pytransformkit' has no attribute {name!r}")


def _warn_legacy(name: str, replacement: str) -> None:
    warnings.warn(
        f"{name} is a pre-V1 compatibility name; use {replacement} instead.",
        DeprecationWarning,
        stacklevel=3,
    )
