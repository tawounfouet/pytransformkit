from __future__ import annotations

import pytest

from pytransformkit.domain.data.statistics import DatasetStatistics


def test_dataset_statistics_are_optional() -> None:
    assert DatasetStatistics() == DatasetStatistics(
        row_count=None,
        byte_size=None,
        field_count=None,
    )


def test_dataset_statistics_preserve_non_negative_values() -> None:
    statistics = DatasetStatistics(
        row_count=100,
        byte_size=2048,
        field_count=3,
    )

    assert statistics.row_count == 100
    assert statistics.byte_size == 2048
    assert statistics.field_count == 3


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("row_count", {"row_count": -1}),
        ("byte_size", {"byte_size": -1}),
        ("field_count", {"field_count": -1}),
    ],
)
def test_dataset_statistics_reject_negative_values(
    field_name: str,
    kwargs: dict[str, int],
) -> None:
    with pytest.raises(ValueError, match=field_name):
        DatasetStatistics(**kwargs)
