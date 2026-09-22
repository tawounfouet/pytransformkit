"""PyTransformKit public package."""

from importlib.metadata import PackageNotFoundError, version

from pytransformkit.application.execution import (
    EngineRegistry,
    ExecutionContext,
    ExecutionMode,
    PipelineExecutionResult,
    RunPipelineService,
)
from pytransformkit.domain.pipelines.pipeline import Pipeline

try:
    __version__ = version("pytransformkit")
except PackageNotFoundError:
    __version__ = "0.1.0a1"

__all__ = [
    "EngineRegistry",
    "ExecutionContext",
    "ExecutionMode",
    "Pipeline",
    "PipelineExecutionResult",
    "RunPipelineService",
    "__version__",
]
