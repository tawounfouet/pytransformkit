"""Logical Dataset aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pytransformkit.domain.data.metadata import DatasetMetadata
from pytransformkit.domain.data.references import DatasetReference
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.data.statistics import DatasetStatistics
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.domain.shared.identifiers import DatasetId
from pytransformkit.domain.shared.version import Version


@dataclass(frozen=True, slots=True, eq=False)
class Dataset:
    """Logical Dataset identity and metadata, never physical engine data."""

    id: DatasetId
    schema: Schema
    metadata: DatasetMetadata = field(default_factory=DatasetMetadata)
    version: Version | None = None
    fingerprint: Fingerprint | None = None
    statistics: DatasetStatistics | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, DatasetId):
            raise TypeError("Dataset id must be a DatasetId.")
        if not isinstance(self.schema, Schema):
            raise TypeError("Dataset schema must be a Schema.")
        if not isinstance(self.metadata, DatasetMetadata):
            raise TypeError("Dataset metadata must be DatasetMetadata.")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Dataset):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def reference(self) -> DatasetReference:
        """Create a portable reference to this logical Dataset."""
        return DatasetReference(
            dataset_id=self.id,
            version=self.version,
            fingerprint=self.fingerprint,
        )
