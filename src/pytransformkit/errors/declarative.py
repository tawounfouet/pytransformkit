"""Declarative schema authoring errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode


@dataclass(frozen=True, slots=True)
class DeclarativeErrorContext:
    """Format-neutral source context for declarative schema diagnostics."""

    source: str | None = None
    line: int | None = None
    column: int | None = None
    object_path: str | None = None

    def __post_init__(self) -> None:
        for text_name, text_value in (
            ("source", self.source),
            ("object_path", self.object_path),
        ):
            if text_value is not None:
                if not isinstance(text_value, str):
                    raise TypeError(f"{text_name} must be a string or None.")
                if not text_value.strip():
                    raise ValueError(
                        f"{text_name} must contain non-whitespace text."
                    )

        for position_name, position_value in (
            ("line", self.line),
            ("column", self.column),
        ):
            if position_value is not None:
                if type(position_value) is not int:
                    raise TypeError(f"{position_name} must be an int or None.")
                if position_value <= 0:
                    raise ValueError(
                        f"{position_name} must be one-based when provided."
                    )


class DeclarativeSchemaError(PyTransformKitError):
    """Base class for declarative schema authoring failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-000")

    def __init__(
        self,
        message: str,
        *,
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.context = context or DeclarativeErrorContext()
        self.source = self.context.source
        self.line = self.context.line
        self.column = self.context.column
        self.object_path = self.context.object_path
        super().__init__(message)


class DeclarativeSchemaParseError(DeclarativeSchemaError):
    """Raised when declarative source cannot be parsed safely."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-001")

    def __init__(
        self,
        message: str = "Declarative schema parsing failed.",
        *,
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        super().__init__(message, context=context)


class DeclarativeSchemaVersionError(DeclarativeSchemaError):
    """Raised for missing, malformed, or unsupported declarative versions."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-002")

    def __init__(
        self,
        actual_version: object,
        *,
        supported_versions: tuple[int, ...] = (1,),
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.actual_version = actual_version
        self.supported_versions = supported_versions
        expected = ", ".join(str(version) for version in supported_versions)
        super().__init__(
            f"Unsupported declarative schema version {actual_version!r}; "
            f"expected one of: {expected}.",
            context=context,
        )


class DeclarativeSchemaValidationError(DeclarativeSchemaError):
    """Raised for structural or semantic declarative validation failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-003")

    def __init__(
        self,
        message: str = "Declarative schema validation failed.",
        *,
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        super().__init__(message, context=context)


class DeclarativeSchemaUnknownPropertyError(DeclarativeSchemaValidationError):
    """Raised when declarative input contains an unsupported property."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-004")

    def __init__(
        self,
        property_name: str,
        *,
        allowed_properties: tuple[str, ...] = (),
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.property_name = property_name
        self.allowed_properties = allowed_properties
        message = f"Unknown declarative property {property_name!r}."
        if allowed_properties:
            message += (
                " Expected one of: "
                + ", ".join(repr(value) for value in allowed_properties)
                + "."
            )
        super().__init__(message, context=context)


class DeclarativeSchemaTypeError(DeclarativeSchemaValidationError):
    """Raised for invalid or unsupported declarative logical type semantics."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-005")

    def __init__(
        self,
        type_name: str | None = None,
        *,
        expected_type_names: tuple[str, ...] = (),
        message: str | None = None,
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.type_name = type_name
        self.expected_type_names = expected_type_names
        if message is None:
            if type_name is None:
                message = "Invalid declarative logical type."
            else:
                message = f"Unknown declarative type {type_name!r}."
                if expected_type_names:
                    message += (
                        " Expected one of: "
                        + ", ".join(repr(value) for value in expected_type_names)
                        + "."
                    )
        super().__init__(message, context=context)


class DeclarativeSchemaDuplicateKeyError(DeclarativeSchemaParseError):
    """Raised when a declarative mapping contains a duplicate key."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-006")

    def __init__(
        self,
        key: str,
        *,
        context: DeclarativeErrorContext | None = None,
        first_context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.key = key
        self.first_context = first_context
        super().__init__(
            f"Duplicate declarative mapping key {key!r} is not allowed.",
            context=context,
        )


class DeclarativeSchemaDuplicateFieldError(DeclarativeSchemaValidationError):
    """Raised for duplicate logical field names in declarative schemas."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-007")

    def __init__(
        self,
        field_name: str,
        *,
        context: DeclarativeErrorContext | None = None,
        first_context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.field_name = field_name
        self.first_context = first_context
        super().__init__(
            f"Duplicate declarative field name {field_name!r} is not allowed.",
            context=context,
        )


class DeclarativeSchemaDuplicateSchemaError(DeclarativeSchemaValidationError):
    """Raised for duplicate schema identities in one declarative document."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-008")

    def __init__(
        self,
        schema_name: str,
        *,
        context: DeclarativeErrorContext | None = None,
        first_context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.schema_name = schema_name
        self.first_context = first_context
        super().__init__(
            f"Duplicate declarative schema name {schema_name!r} is not allowed.",
            context=context,
        )


class DeclarativeSchemaCardinalityError(DeclarativeSchemaError):
    """Raised when a helper receives the wrong number of schema declarations."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-009")

    def __init__(
        self,
        required_count: int,
        actual_count: int,
        *,
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.required_count = required_count
        self.actual_count = actual_count
        super().__init__(
            "Declarative schema cardinality mismatch: "
            f"expected {required_count}, got {actual_count}.",
            context=context,
        )


class DeclarativeSchemaDependencyError(DeclarativeSchemaError):
    """Raised when an optional declarative-schema dependency is unavailable."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-010")

    def __init__(
        self,
        dependency_name: str,
        *,
        extra_name: str = "yaml",
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.dependency_name = dependency_name
        self.extra_name = extra_name
        super().__init__(
            f"Declarative schema support requires optional dependency "
            f"{dependency_name!r}. Install with: "
            f'pip install "pytransformkit[{extra_name}]".',
            context=context,
        )


class DeclarativeSchemaIOError(DeclarativeSchemaError):
    """Raised for declarative schema filesystem I/O failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-011")

    def __init__(
        self,
        path: str,
        operation: str,
        *,
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.path = path
        self.operation = operation
        super().__init__(
            f"Declarative schema {operation} failed for {path!r}.",
            context=context,
        )


class DeclarativeSchemaExportError(DeclarativeSchemaError):
    """Raised when canonical state cannot be represented declaratively."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-012")

    def __init__(
        self,
        message: str = "Declarative schema export failed.",
        *,
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        super().__init__(message, context=context)


class DeclarativeSchemaLimitError(DeclarativeSchemaError):
    """Raised when declarative input exceeds a defensive resource limit."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-DECL-013")

    def __init__(
        self,
        limit_name: str,
        limit: int,
        actual: int,
        *,
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.limit_name = limit_name
        self.limit = limit
        self.actual = actual
        super().__init__(
            f"Declarative schema limit {limit_name!r} exceeded: "
            f"limit={limit}, actual={actual}.",
            context=context,
        )
