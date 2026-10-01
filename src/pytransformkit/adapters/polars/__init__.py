"""Stable public Polars adapter surface."""

from __future__ import annotations

import warnings
from typing import Any

from pytransformkit.infrastructure.engines.polars.adapter import (
    PolarsAdapter as PolarsEngineAdapter,
)

__all__ = ["PolarsEngineAdapter"]


def __getattr__(name: str) -> Any:
    """Resolve pre-V1 adapter names without freezing physical wrappers."""
    if name == "PolarsAdapter":
        from pytransformkit.infrastructure.engines.polars import PolarsAdapter

        _warn_legacy(name, "PolarsEngineAdapter")
        return PolarsAdapter
    if name == "PolarsDatasetHandle":
        from pytransformkit.infrastructure.engines.polars import PolarsDatasetHandle

        _warn_legacy(
            name,
            "process-local output_handle returned by PolarsEngineAdapter",
        )
        return PolarsDatasetHandle
    raise AttributeError(
        f"module 'pytransformkit.adapters.polars' has no attribute {name!r}"
    )


def _warn_legacy(name: str, replacement: str) -> None:
    warnings.warn(
        f"{name} is a pre-V1 adapter compatibility name; use {replacement} instead.",
        DeprecationWarning,
        stacklevel=3,
    )
