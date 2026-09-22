from __future__ import annotations

import pytest

from pytransformkit.domain.data.field_path import FieldPath


def test_field_path_parses_dot_separated_path() -> None:
    path = FieldPath.of("customer.address.city")

    assert path.parts == ("customer", "address", "city")
    assert path.name == "city"
    assert str(path) == "customer.address.city"


@pytest.mark.parametrize("value", ["", "   ", ".email", "customer..email", "email."])
def test_field_path_rejects_empty_components(value: str) -> None:
    with pytest.raises(ValueError):
        FieldPath.of(value)


def test_field_path_requires_immutable_tuple_storage() -> None:
    with pytest.raises(TypeError, match="tuple"):
        FieldPath(["email"])  # type: ignore[arg-type]
