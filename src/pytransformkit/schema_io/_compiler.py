"""Compilation of validated declarative definitions into canonical Domain schemas."""

from __future__ import annotations

from pytransformkit.domain.data import Field, Schema
from pytransformkit.errors import (
    DeclarativeErrorContext,
    DeclarativeSchemaCardinalityError,
    DeclarativeSchemaDuplicateFieldError,
    DeclarativeSchemaError,
    DeclarativeSchemaTypeError,
    DeclarativeSchemaValidationError,
    DuplicateFieldError,
)
from pytransformkit.schema_io._model import (
    FieldDefinition,
    SchemaDefinition,
    SchemaDocument,
)
from pytransformkit.schema_io._type_resolution import DeclarativeTypeResolver


class SchemaDefinitionCompiler:
    """Compile one normalized SchemaDefinition into canonical Schema."""

    def __init__(
        self,
        type_resolver: DeclarativeTypeResolver | None = None,
    ) -> None:
        self._type_resolver = type_resolver or DeclarativeTypeResolver()

    def compile(
        self,
        definition: SchemaDefinition,
        *,
        source: str | None = None,
        object_path: str = "schema",
    ) -> Schema:
        """Compile one definition while preserving canonical Domain invariants."""
        compiled_fields = tuple(
            self._compile_field(
                field,
                source=source,
                object_path=f"{object_path}.fields[{index}]",
            )
            for index, field in enumerate(definition.fields)
        )

        try:
            return Schema(fields=compiled_fields)
        except DuplicateFieldError as exc:
            first_index, duplicate_index = _duplicate_indexes(
                definition,
                exc.field_name,
            )
            raise DeclarativeSchemaDuplicateFieldError(
                exc.field_name,
                context=_context(
                    source,
                    f"{object_path}.fields[{duplicate_index}].name",
                ),
                first_context=_context(
                    source,
                    f"{object_path}.fields[{first_index}].name",
                ),
            ) from exc

    def _compile_field(
        self,
        definition: FieldDefinition,
        *,
        source: str | None,
        object_path: str,
    ) -> Field:
        try:
            data_type = self._type_resolver.resolve(definition.data_type)
        except DeclarativeSchemaError:
            raise
        except (TypeError, ValueError) as exc:
            raise DeclarativeSchemaTypeError(
                message=(
                    "Canonical DataType construction failed for declarative field "
                    f"{definition.name!r}."
                ),
                context=_context(source, f"{object_path}.type"),
            ) from exc

        try:
            return Field(
                name=definition.name,
                data_type=data_type,
                nullable=definition.nullable,
                description=definition.description,
            )
        except (TypeError, ValueError) as exc:
            raise DeclarativeSchemaValidationError(
                "Canonical Field construction rejected the declarative field.",
                context=_context(source, object_path),
            ) from exc


class SchemaDocumentCompiler:
    """Compile validated SchemaDocument values without attaching schema names."""

    def __init__(
        self,
        schema_compiler: SchemaDefinitionCompiler | None = None,
    ) -> None:
        self._schema_compiler = schema_compiler or SchemaDefinitionCompiler()

    def compile(
        self,
        document: SchemaDocument,
        *,
        source: str | None = None,
    ) -> dict[str, Schema]:
        """Compile all schemas atomically while preserving declaration order."""
        compiled: dict[str, Schema] = {}
        for index, definition in enumerate(document.schemas):
            compiled[definition.name] = self._schema_compiler.compile(
                definition,
                source=source,
                object_path=f"schemas[{index}]",
            )
        return compiled

    def compile_single(
        self,
        document: SchemaDocument,
        *,
        source: str | None = None,
    ) -> Schema:
        """Compile exactly one schema and reject ambiguous cardinality."""
        actual_count = len(document.schemas)
        if actual_count != 1:
            raise DeclarativeSchemaCardinalityError(
                required_count=1,
                actual_count=actual_count,
                context=_context(source, "schemas"),
            )

        return self._schema_compiler.compile(
            document.schemas[0],
            source=source,
            object_path="schemas[0]",
        )


def _duplicate_indexes(
    definition: SchemaDefinition,
    field_name: str,
) -> tuple[int, int]:
    first_index: int | None = None
    for index, field in enumerate(definition.fields):
        if field.name != field_name:
            continue
        if first_index is None:
            first_index = index
            continue
        return first_index, index

    raise AssertionError(
        "Canonical DuplicateFieldError did not correspond to declarative fields."
    )


def _context(
    source: str | None,
    object_path: str,
) -> DeclarativeErrorContext:
    return DeclarativeErrorContext(
        source=source,
        object_path=object_path,
    )
