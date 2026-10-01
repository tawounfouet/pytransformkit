"""Public Polars adapter surface."""

from pytransformkit.infrastructure.engines.polars import (
    PolarsAdapter,
    PolarsDatasetHandle,
)

PolarsEngineAdapter = PolarsAdapter

__all__ = ["PolarsEngineAdapter"]
