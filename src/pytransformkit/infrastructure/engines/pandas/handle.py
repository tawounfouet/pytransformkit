"""Pandas physical Dataset handle."""

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True, slots=True)
class PandasDatasetHandle:
    """Opaque runtime wrapper around a pandas.DataFrame."""

    dataframe: Any

    def __post_init__(self) -> None:
        if not isinstance(self.dataframe, pd.DataFrame):
            raise TypeError(
                "PandasDatasetHandle dataframe must be a pandas.DataFrame."
            )

    @property
    def engine_id(self) -> str:
        return "pandas"
