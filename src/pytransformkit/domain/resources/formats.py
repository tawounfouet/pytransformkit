"""Portable physical resource format semantics."""

from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath

from pytransformkit.domain.resources.reference import ResourceReference


class ResourceFormat(StrEnum):
    """Tabular physical formats supported by the LOT-20 local I/O profile."""

    CSV = "csv"
    JSONL = "jsonl"
    PARQUET = "parquet"
    ARROW_IPC = "arrow_ipc"


_MEDIA_TYPES: dict[str, ResourceFormat] = {
    "text/csv": ResourceFormat.CSV,
    "application/x-ndjson": ResourceFormat.JSONL,
    "application/ndjson": ResourceFormat.JSONL,
    "application/jsonl": ResourceFormat.JSONL,
    "application/vnd.apache.parquet": ResourceFormat.PARQUET,
    "application/x-parquet": ResourceFormat.PARQUET,
    "application/vnd.apache.arrow.file": ResourceFormat.ARROW_IPC,
    "application/vnd.apache.arrow.stream": ResourceFormat.ARROW_IPC,
}

_SUFFIXES: dict[str, ResourceFormat] = {
    ".csv": ResourceFormat.CSV,
    ".jsonl": ResourceFormat.JSONL,
    ".ndjson": ResourceFormat.JSONL,
    ".parquet": ResourceFormat.PARQUET,
    ".arrow": ResourceFormat.ARROW_IPC,
    ".feather": ResourceFormat.ARROW_IPC,
    ".ipc": ResourceFormat.ARROW_IPC,
}


def infer_resource_format(reference: ResourceReference) -> ResourceFormat:
    """Infer a supported format from media type first, then locator suffix."""
    if not isinstance(reference, ResourceReference):
        raise TypeError("reference must be a ResourceReference.")

    if reference.media_type is not None:
        normalized = reference.media_type.split(";", maxsplit=1)[0].strip().lower()
        if normalized in _MEDIA_TYPES:
            return _MEDIA_TYPES[normalized]

    suffix = PurePosixPath(reference.locator.replace("\\", "/")).suffix.lower()
    if suffix in _SUFFIXES:
        return _SUFFIXES[suffix]

    raise ValueError(
        "Unable to infer a supported resource format from "
        f"{reference.locator!r} / {reference.media_type!r}."
    )
