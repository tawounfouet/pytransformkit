"""Public Pandas adapter surface."""

from pytransformkit.infrastructure.engines.pandas import (
    PandasAdapter,
    PandasDatasetHandle,
)

PandasEngineAdapter = PandasAdapter

__all__ = [
    "PandasAdapter",
    "PandasDatasetHandle",
    "PandasEngineAdapter",
]
