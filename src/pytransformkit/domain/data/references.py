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

    def __post_init__(self) -> None:
        if not isinstance(self.dataset_id, DatasetId):
            raise TypeError("Dataset reference id must be a DatasetId.")
        if self.version is not None and not isinstance(self.version, Version):
            raise TypeError("Dataset reference version must be a Version.")
        if self.fingerprint is not None and not isinstance(
            self.fingerprint, Fingerprint
        ):
            raise TypeError("Dataset reference fingerprint must be a Fingerprint.")


@dataclass(frozen=True, slots=True)
class LogicalDatasetReference:
    """Name-based reference used while building logical plans."""

    name: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Logical Dataset reference name must not be empty.")
