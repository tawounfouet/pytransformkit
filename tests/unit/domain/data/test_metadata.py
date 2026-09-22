from __future__ import annotations

import pytest

from pytransformkit.domain.data.metadata import DatasetMetadata


def test_dataset_metadata_preserves_values() -> None:
    metadata = DatasetMetadata(
        name="customers",
        description="Customer master data",
        tags=frozenset({"crm", "gold"}),
    )

    assert metadata.name == "customers"
    assert metadata.description == "Customer master data"
    assert metadata.tags == frozenset({"crm", "gold"})


@pytest.mark.parametrize(
    ("name", "description"),
    [
        ("", None),
        ("   ", None),
        (None, ""),
        (None, "   "),
    ],
)
def test_dataset_metadata_rejects_blank_text(
    name: str | None,
    description: str | None,
) -> None:
    with pytest.raises(ValueError):
        DatasetMetadata(name=name, description=description)


def test_dataset_metadata_requires_frozenset_tags() -> None:
    with pytest.raises(TypeError, match="frozenset"):
        DatasetMetadata(tags={"crm"})  # type: ignore[arg-type]


def test_dataset_metadata_rejects_blank_tag() -> None:
    with pytest.raises(ValueError, match="tags"):
        DatasetMetadata(tags=frozenset({"crm", "   "}))
