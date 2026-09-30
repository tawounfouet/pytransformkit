"""DuckDB physical Dataset handle."""

from dataclasses import dataclass
from typing import Any

import duckdb


@dataclass(frozen=True, slots=True)
class DuckDBDatasetHandle:
    """Opaque runtime wrapper around a DuckDB relation."""

    relation: Any

    def __post_init__(self) -> None:
        if not isinstance(self.relation, duckdb.DuckDBPyRelation):
            raise TypeError(
                "DuckDBDatasetHandle relation must be a DuckDBPyRelation."
            )

    @property
    def engine_id(self) -> str:
        return "duckdb"

    def to_arrow_table(self) -> Any:
        """Materialize this relation as a PyArrow Table."""
        return self.relation.to_arrow_table()
