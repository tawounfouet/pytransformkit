"""DuckDB physical Dataset handle."""

from dataclasses import dataclass
from typing import Any

import duckdb


@dataclass(frozen=True, slots=True)
class DuckDBDatasetHandle:
    """Opaque runtime wrapper around a DuckDB relation."""

    relation: Any
    connection: Any | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.relation, duckdb.DuckDBPyRelation):
            raise TypeError(
                "DuckDBDatasetHandle relation must be a DuckDBPyRelation."
            )
        if self.connection is not None and not isinstance(
            self.connection,
            duckdb.DuckDBPyConnection,
        ):
            raise TypeError(
                "DuckDBDatasetHandle connection must be a DuckDBPyConnection."
            )

    @property
    def engine_id(self) -> str:
        return "duckdb"

    def to_arrow_table(self) -> Any:
        """Materialize this relation as a PyArrow Table."""
        return self.relation.to_arrow_table()
