"""Polars physical Dataset handles."""

from dataclasses import dataclass
from typing import Any

import polars as pl


@dataclass(frozen=True, slots=True)
class PolarsDatasetHandle:
    """Opaque runtime wrapper around a Polars DataFrame or LazyFrame."""

    frame: Any

    def __post_init__(self) -> None:
        if not isinstance(self.frame, (pl.DataFrame, pl.LazyFrame)):
            raise TypeError(
                "PolarsDatasetHandle frame must be a polars.DataFrame "
                "or polars.LazyFrame."
            )

    @property
    def engine_id(self) -> str:
        return "polars"

    @property
    def is_lazy(self) -> bool:
        return isinstance(self.frame, pl.LazyFrame)

    def to_arrow_table(self) -> Any:
        """Materialize this frame as an Arrow Table for explicit I/O."""
        frame = self.frame.collect() if self.is_lazy else self.frame
        return frame.to_arrow()
