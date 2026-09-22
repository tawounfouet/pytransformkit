from __future__ import annotations

import pytest

from pytransformkit.domain.data.data_types import StringType
from pytransformkit.domain.data.field import Field


def test_field_preserves_logical_definition() -> None:
    field = Field(
        name="email",
        data_type=StringType(),
        nullable=False,
        description="Customer email",
    )

    assert field.name == "email"
    assert field.data_type == StringType()
    assert field.nullable is False
    assert field.description == "Customer email"


@pytest.mark.parametrize("name", ["", "   "])
def test_field_rejects_empty_name(name: str) -> None:
    with pytest.raises(ValueError, match="Field name"):
        Field(name=name, data_type=StringType())


def test_field_rejects_non_domain_data_type() -> None:
    with pytest.raises(TypeError, match="DataType"):
        Field(name="email", data_type="string")  # type: ignore[arg-type]
