"""Optional Polars engine adapter."""

from pytransformkit.infrastructure.engines.polars.adapter import PolarsAdapter
from pytransformkit.infrastructure.engines.polars.expressions import (
    PolarsExpressionCompiler,
)
from pytransformkit.infrastructure.engines.polars.handle import (
    PolarsDatasetHandle,
)
from pytransformkit.infrastructure.engines.polars.types import (
    PolarsSchemaInspector,
    PolarsTypeMapper,
)

__all__ = [
    "PolarsAdapter",
    "PolarsDatasetHandle",
    "PolarsExpressionCompiler",
    "PolarsSchemaInspector",
    "PolarsTypeMapper",
]
