"""Optional Pandas reference adapter."""

from pytransformkit.infrastructure.engines.pandas.adapter import PandasAdapter
from pytransformkit.infrastructure.engines.pandas.expressions import (
    PandasExpressionCompiler,
)
from pytransformkit.infrastructure.engines.pandas.handle import (
    PandasDatasetHandle,
)
from pytransformkit.infrastructure.engines.pandas.types import (
    PandasSchemaInspector,
    PandasTypeMapper,
)

__all__ = [
    "PandasAdapter",
    "PandasDatasetHandle",
    "PandasExpressionCompiler",
    "PandasSchemaInspector",
    "PandasTypeMapper",
]
