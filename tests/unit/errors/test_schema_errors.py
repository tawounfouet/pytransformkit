from __future__ import annotations

from pytransformkit.errors import (
    DuplicateFieldError,
    FieldCollisionError,
    FieldNotFoundError,
    PyTransformKitError,
)


def test_schema_errors_share_pytransformkit_root() -> None:
    assert isinstance(FieldNotFoundError("email"), PyTransformKitError)
    assert isinstance(DuplicateFieldError("email"), PyTransformKitError)
    assert isinstance(FieldCollisionError("email"), PyTransformKitError)


def test_schema_error_codes_are_stable_and_distinct() -> None:
    codes = {
        str(FieldNotFoundError("email").code),
        str(DuplicateFieldError("email").code),
        str(FieldCollisionError("email").code),
    }

    assert codes == {
        "PTK-SCHEMA-001",
        "PTK-SCHEMA-002",
        "PTK-SCHEMA-003",
    }
