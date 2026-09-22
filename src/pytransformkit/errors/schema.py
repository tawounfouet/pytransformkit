"""Schema-related PyTransformKit errors."""

from typing import ClassVar

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode


class SchemaError(PyTransformKitError):
    """Base class for logical Schema failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-SCHEMA-000")


class FieldNotFoundError(SchemaError):
    """Raised when a requested logical field does not exist."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-SCHEMA-001")

    def __init__(self, field_name: str) -> None:
        self.field_name = field_name
        super().__init__(f"Field {field_name!r} was not found in the schema.")


class DuplicateFieldError(SchemaError):
    """Raised when a Schema contains duplicate logical field names."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-SCHEMA-002")

    def __init__(self, field_name: str) -> None:
        self.field_name = field_name
        super().__init__(f"Duplicate field name {field_name!r} is not allowed.")


class FieldCollisionError(SchemaError):
    """Raised when an operation would create a field-name collision."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-SCHEMA-003")

    def __init__(self, field_name: str) -> None:
        self.field_name = field_name
        super().__init__(f"Field name {field_name!r} collides with an existing field.")
