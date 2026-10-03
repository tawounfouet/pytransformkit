"""Shared primitives for presentation-neutral CLI reports."""

from __future__ import annotations

from typing import TypeAlias

ReportData: TypeAlias = dict[str, object]

__all__ = ["ReportData"]
