from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.dataset import Dataset
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.metadata import DatasetMetadata
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.data.statistics import DatasetStatistics
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.domain.shared.identifiers import DatasetId
from pytransformkit.domain.shared.version import Version


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType()),
        )
    )


def test_dataset_preserves_logical_state_without_native_data() -> None:
    dataset = Dataset(
        id=DatasetId.new(),
        schema=_schema(),
        metadata=DatasetMetadata(name="customers"),
        version=Version(1, 0, 0),
        fingerprint=Fingerprint("sha256", "abc"),
        statistics=DatasetStatistics(row_count=10, field_count=2),
    )

    assert dataset.schema.names() == ("customer_id", "email")
    assert dataset.metadata.name == "customers"
    assert not hasattr(dataset, "data")
    assert not hasattr(dataset, "dataframe")


def test_dataset_equality_is_based_on_dataset_id() -> None:
    dataset_id = DatasetId.new()

    left = Dataset(id=dataset_id, schema=_schema())
    right = Dataset(
        id=dataset_id,
        schema=Schema(fields=(Field("other", StringType()),)),
    )

    assert left == right
    assert hash(left) == hash(right)


def test_different_dataset_ids_are_distinct() -> None:
    assert Dataset(id=DatasetId.new(), schema=_schema()) != Dataset(
        id=DatasetId.new(),
        schema=_schema(),
    )


def test_dataset_reference_carries_version_and_fingerprint() -> None:
    dataset_id = DatasetId.new()
    dataset = Dataset(
        id=dataset_id,
        schema=_schema(),
        version=Version(2, 1, 0),
        fingerprint=Fingerprint("sha256", "def"),
    )

    reference = dataset.reference()

    assert reference.dataset_id == dataset_id
    assert reference.version == Version(2, 1, 0)
    assert reference.fingerprint == Fingerprint("sha256", "def")


def test_dataset_is_logically_immutable() -> None:
    dataset = Dataset(id=DatasetId.new(), schema=_schema())

    with pytest.raises(FrozenInstanceError):
        dataset.schema = Schema(fields=())  # type: ignore[misc]


def test_dataset_rejects_non_domain_schema() -> None:
    with pytest.raises(TypeError, match="Schema"):
        Dataset(
            id=DatasetId.new(),
            schema="customer_id,email",  # type: ignore[arg-type]
        )
