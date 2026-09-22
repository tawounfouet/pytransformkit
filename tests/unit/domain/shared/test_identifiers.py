from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from pytransformkit.domain.shared.identifiers import DatasetId, PipelineId


def test_new_creates_typed_uuid_identifier() -> None:
    identifier = DatasetId.new()

    assert isinstance(identifier.value, UUID)
    assert isinstance(identifier, DatasetId)


def test_parse_round_trips_uuid_string() -> None:
    value = uuid4()

    identifier = DatasetId.parse(str(value))

    assert identifier.value == value
    assert str(identifier) == str(value)


def test_identifiers_with_same_type_and_uuid_are_equal() -> None:
    value = uuid4()

    assert DatasetId(value) == DatasetId(value)
    assert hash(DatasetId(value)) == hash(DatasetId(value))


def test_identifiers_with_different_types_are_not_equal() -> None:
    value = uuid4()

    assert DatasetId(value) != PipelineId(value)


def test_identifier_rejects_non_uuid_value() -> None:
    with pytest.raises(TypeError, match="UUID"):
        DatasetId("not-a-uuid")  # type: ignore[arg-type]
