"""Shared helpers for deterministic human Rich tables."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from rich.table import Table
from rich.text import Text


def build_table(
    *,
    columns: Sequence[str],
    rows: Iterable[Sequence[str]],
) -> Table:
    """Build a minimal table while preserving caller-provided row order."""
    table = Table(show_header=True, header_style="bold", box=None)
    for column in columns:
        table.add_column(column)
    for row in rows:
        table.add_row(*(Text(value) for value in row))
    return table


__all__ = ["build_table"]
