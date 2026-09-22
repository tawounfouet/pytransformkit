from __future__ import annotations

import pytest

from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.errors.schema import (
    DuplicateFieldError,
    FieldCollisionError,
    FieldNotFoundError,
)


def _customer_schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
        )
    )


def test_empty_schema_is_allowed() -> None:
    schema = Schema(fields=())

    assert len(schema) == 0
    assert schema.names() == ()


def test_schema_requires_tuple_storage() -> None:
    with pytest.raises(TypeError, match="tuple"):
        Schema(fields=[])  # type: ignore[arg-type]


def test_schema_rejects_duplicate_field_names() -> None:
    with pytest.raises(DuplicateFieldError) as error:
        Schema(
            fields=(
                Field("email", StringType()),
                Field("email", StringType()),
            )
        )

    assert str(error.value.code) == "PTK-SCHEMA-002"


def test_schema_is_case_sensitive() -> None:
    schema = Schema(
        fields=(
            Field("email", StringType()),
            Field("Email", StringType()),
        )
    )

    assert schema.names() == ("email", "Email")


def test_field_lookup_returns_exact_field() -> None:
    schema = _customer_schema()

    assert schema.field("email") == Field("email", StringType(), nullable=True)


def test_missing_field_raises_typed_error() -> None:
    schema = _customer_schema()

    with pytest.raises(FieldNotFoundError) as error:
        schema.field("missing")

    assert error.value.field_name == "missing"
    assert str(error.value.code) == "PTK-SCHEMA-001"


def test_select_preserves_requested_order() -> None:
    schema = _customer_schema()

    selected = schema.select(("status", "customer_id"))

    assert selected.names() == ("status", "customer_id")


def test_select_rejects_missing_field() -> None:
    schema = _customer_schema()

    with pytest.raises(FieldNotFoundError):
        schema.select(("customer_id", "missing"))


def test_drop_preserves_remaining_order() -> None:
    schema = _customer_schema()

    dropped = schema.drop(("email",))

    assert dropped.names() == ("customer_id", "status")


def test_drop_rejects_missing_field() -> None:
    schema = _customer_schema()

    with pytest.raises(FieldNotFoundError):
        schema.drop(("missing",))


def test_rename_preserves_field_position() -> None:
    schema = _customer_schema()

    renamed = schema.rename({"email": "normalized_email"})

    assert renamed.names() == ("customer_id", "normalized_email", "status")


def test_rename_rejects_missing_source() -> None:
    schema = _customer_schema()

    with pytest.raises(FieldNotFoundError):
        schema.rename({"missing": "new_name"})


def test_rename_rejects_collision() -> None:
    schema = _customer_schema()

    with pytest.raises(FieldCollisionError) as error:
        schema.rename({"email": "status"})

    assert error.value.field_name == "status"
    assert str(error.value.code) == "PTK-SCHEMA-003"


def test_append_adds_field_at_end() -> None:
    schema = _customer_schema()

    appended = schema.append(Field("created_at", StringType()))

    assert appended.names() == (
        "customer_id",
        "email",
        "status",
        "created_at",
    )


def test_append_rejects_collision() -> None:
    schema = _customer_schema()

    with pytest.raises(FieldCollisionError):
        schema.append(Field("email", StringType()))


def test_replace_preserves_logical_position() -> None:
    schema = _customer_schema()

    replaced = schema.replace(Field("email", StringType(), nullable=False))

    assert replaced.names() == ("customer_id", "email", "status")
    assert replaced.field("email").nullable is False


def test_replace_rejects_missing_field() -> None:
    schema = _customer_schema()

    with pytest.raises(FieldNotFoundError):
        schema.replace(Field("missing", StringType()))
