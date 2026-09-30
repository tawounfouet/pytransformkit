"""PyArrow physical Dataset handle."""

from dataclasses import dataclass
from typing import Any

import pyarrow as pa


@dataclass(frozen=True, slots=True)
class PyArrowDatasetHandle:
    """Opaque runtime wrapper around a PyArrow Table or RecordBatch."""

    value: Any

    def __post_init__(self) -> None:
        if not isinstance(self.value, (pa.Table, pa.RecordBatch)):
            raise TypeError(
                "PyArrowDatasetHandle value must be a pyarrow.Table or RecordBatch."
            )

    @property
    def engine_id(self) -> str:
        return "pyarrow"

    @property
    def table(self) -> pa.Table:
        """Return a Table view without combining chunks."""
        if isinstance(self.value, pa.Table):
            return self.value
        return pa.Table.from_batches([self.value])

    def to_arrow_table(self) -> pa.Table:
        """Expose this handle through the common Arrow I/O boundary."""
        return self.table
