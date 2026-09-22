from __future__ import annotations

import pytest

from pytransformkit.domain.data.references import (
    DatasetReference,
    LogicalDatasetReference,
)
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.domain.shared.identifiers import DatasetId
from pytransformkit.domain.shared.version import Version


def test_dataset_reference_preserves_identity_and_version() -> None:
    dataset_id = DatasetId.new()
    reference = DatasetReference(
        dataset_id=dataset_id,
        version=Version(1, 0, 0),
        fingerprint=Fingerprint("sha256", "abc"),
    )

    assert reference.dataset_id == dataset_id
    assert reference.version == Version(1, 0, 0)
    assert reference.fingerprint == Fingerprint("sha256", "abc")


def test_dataset_reference_rejects_wrong_identifier_type() -> None:
    with pytest.raises(TypeError, match="DatasetId"):
        DatasetReference(dataset_id="id")  # type: ignore[arg-type]


@pytest.mark.parametrize("name", ["", "   "])
def test_logical_dataset_reference_rejects_blank_name(name: str) -> None:
    with pytest.raises(ValueError, match="name"):
        LogicalDatasetReference(name=name)


def test_logical_dataset_reference_preserves_name() -> None:
    assert LogicalDatasetReference("customers").name == "customers"
