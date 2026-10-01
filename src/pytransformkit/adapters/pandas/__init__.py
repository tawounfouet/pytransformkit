"""Stable public Pandas adapter surface."""

from __future__ import annotations

import warnings
from typing import Any

from pytransformkit.infrastructure.engines.pandas.adapter import (
    PandasAdapter as PandasEngineAdapter,
)

__all__ = ["PandasEngineAdapter"]


def __getattr__(name: str) -> Any:
    """Resolve pre-V1 adapter names without freezing physical wrappers."""
    if name == "PandasAdapter":
        from pytransformkit.infrastructure.engines.pandas import PandasAdapter

        _warn_legacy(name, "PandasEngineAdapter")
        return PandasAdapter
    if name == "PandasDatasetHandle":
        from pytransformkit.infrastructure.engines.pandas import PandasDatasetHandle

        _warn_legacy(
            name,
            "process-local output_handle returned by PandasEngineAdapter",
        )
        return PandasDatasetHandle
    raise AttributeError(
        f"module 'pytransformkit.adapters.pandas' has no attribute {name!r}"
    )


def _warn_legacy(name: str, replacement: str) -> None:
    warnings.warn(
        f"{name} is a pre-V1 adapter compatibility name; use {replacement} instead.",
        DeprecationWarning,
        stacklevel=3,
    )
