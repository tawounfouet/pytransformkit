"""Portable references to logical Datasets."""

from dataclasses import dataclass

from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.domain.shared.identifiers import DatasetId
from pytransformkit.domain.shared.version import Version


@dataclass(frozen=True, slots=True)
class DatasetReference:
    """Reference to a concrete logical Dataset identity or version."""

    dataset_id: DatasetId
    version: Version | None = None
    fingerprint: Fingerprint | None = None


@dataclass(frozen=True, slots=True)
class LogicalDatasetReference:
    """Name-based reference used while building logical plans."""

    name: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Logical Dataset reference name must not be empty.")
