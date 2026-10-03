"""Lightweight version inspection service."""

from __future__ import annotations

import platform
from importlib.metadata import version

from pytransformkit.cli.models.reports import VersionReport


class VersionService:
    """Collect version metadata without importing optional engines."""

    def inspect(self) -> VersionReport:
        """Return the installed package and interpreter versions."""
        return VersionReport(
            pytransformkit=version("pytransformkit"),
            python=platform.python_version(),
        )


__all__ = ["VersionService"]
