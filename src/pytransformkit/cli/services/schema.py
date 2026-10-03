"""Schema-focused CLI coordination services."""

from __future__ import annotations

from pathlib import Path

from pytransformkit.cli.exceptions import CLIUnsupportedOperationError
from pytransformkit.cli.models.reports import SchemaValidationReport
from pytransformkit.schema_io import load_schema

_REMOTE_SCHEMES = (
    "http://",
    "https://",
    "s3://",
    "gs://",
    "gcs://",
    "az://",
    "azure://",
    "ftp://",
    "ftps://",
    "ssh://",
)


def _path_text(path: str | Path) -> str:
    return str(path)


def _reject_remote_source(path: str) -> None:
    lowered = path.lstrip().lower()
    if lowered.startswith(_REMOTE_SCHEMES):
        raise CLIUnsupportedOperationError(
            "Remote schema sources are not supported by the PyTransformKit CLI."
        )


class SchemaCLIService:
    """Coordinate CLI schema operations through stable public APIs."""

    def validate(self, path: str | Path) -> SchemaValidationReport:
        """Validate one explicitly named local declarative schema file."""
        path_text = _path_text(path)
        _reject_remote_source(path_text)
        load_schema(path_text)
        return SchemaValidationReport(path=path_text, valid=True)


__all__ = ["SchemaCLIService"]
