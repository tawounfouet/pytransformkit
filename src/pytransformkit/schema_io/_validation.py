"""Semantic validation for normalized declarative schema definitions."""

from __future__ import annotations

from typing import NoReturn

from pytransformkit.errors import (
    DeclarativeErrorContext,
    DeclarativeSchemaDuplicateFieldError,
    DeclarativeSchemaDuplicateSchemaError,
    DeclarativeSchemaTypeError,
    DeclarativeSchemaValidationError,
    DeclarativeSchemaVersionError,
)
from pytransformkit.schema_io._model import (
    BinaryTypeDefinition,
    BooleanTypeDefinition,
    DateTypeDefinition,
    DecimalTypeDefinition,
    DurationTypeDefinition,
    FieldDefinition,
    FloatTypeDefinition,
    IntegerTypeDefinition,
    ListTypeDefinition,
    MapTypeDefinition,
    SchemaDefinition,
    SchemaDocument,
    StringTypeDefinition,
    StructFieldDefinition,
    StructTypeDefinition,
    TimestampTypeDefinition,
    TimeTypeDefinition,
    TypeDefinition,
    UnknownTypeDefinition,
)

_INTEGER_BITS = frozenset({8, 16, 32, 64})
_FLOAT_BITS = frozenset({32, 64})
_TIME_UNITS = frozenset({"s", "ms", "us", "ns"})
_SUPPORTED_TYPE_DEFINITIONS = frozenset(
    {
        StringTypeDefinition,
        BooleanTypeDefinition,
        IntegerTypeDefinition,
        FloatTypeDefinition,
        DecimalTypeDefinition,
        BinaryTypeDefinition,
        DateTypeDefinition,
        TimeTypeDefinition,
        TimestampTypeDefinition,
        DurationTypeDefinition,
        UnknownTypeDefinition,
        ListTypeDefinition,
        StructTypeDefinition,
        MapTypeDefinition,
    }
)


class SchemaDefinitionValidator:
    """Validate normalized declarative schema values deterministically."""

    def validate_document(
        self,
        document: SchemaDocument,
        *,
        source: str | None = None,
    ) -> None:
        """Validate one normalized document without mutating it."""
        if type(document) is not SchemaDocument:
            raise DeclarativeSchemaValidationError(
                "Expected a SchemaDocument.",
                context=self._context(source, "$"),
            )

        self._validate_version(document.version, source=source)

        if not isinstance(document.schemas, tuple):
            raise DeclarativeSchemaValidationError(
                "Document schemas must be a tuple.",
                context=self._context(source, "schemas"),
            )

        first_schema_indexes: dict[str, int] = {}
        for schema_index, schema in enumerate(document.schemas):
            schema_path = f"schemas[{schema_index}]"
            if type(schema) is not SchemaDefinition:
                raise DeclarativeSchemaValidationError(
                    "Document schemas must contain only SchemaDefinition values.",
                    context=self._context(source, schema_path),
                )

            self._validate_non_blank_text(
                schema.name,
                path=f"{schema_path}.name",
                source=source,
                label="Schema name",
            )

            first_schema_index = first_schema_indexes.get(schema.name)
            if first_schema_index is not None:
                raise DeclarativeSchemaDuplicateSchemaError(
                    schema.name,
                    context=self._context(source, f"{schema_path}.name"),
                    first_context=self._context(
                        source,
                        f"schemas[{first_schema_index}].name",
                    ),
                )
            first_schema_indexes[schema.name] = schema_index

            self._validate_schema(
                schema,
                path=schema_path,
                source=source,
            )

    def _validate_version(
        self,
        version: object,
        *,
        source: str | None,
    ) -> None:
        if type(version) is not int or version != 1:
            raise DeclarativeSchemaVersionError(
                version,
                supported_versions=(1,),
                context=self._context(source, "version"),
            )

    def _validate_schema(
        self,
        schema: SchemaDefinition,
        *,
        path: str,
        source: str | None,
    ) -> None:
        if not isinstance(schema.fields, tuple):
            raise DeclarativeSchemaValidationError(
                "Schema fields must be a tuple.",
                context=self._context(source, f"{path}.fields"),
            )

        first_field_indexes: dict[str, int] = {}
        for field_index, field in enumerate(schema.fields):
            field_path = f"{path}.fields[{field_index}]"
            if type(field) is not FieldDefinition:
                raise DeclarativeSchemaValidationError(
                    "Schema fields must contain only FieldDefinition values.",
                    context=self._context(source, field_path),
                )

            self._validate_non_blank_text(
                field.name,
                path=f"{field_path}.name",
                source=source,
                label="Field name",
            )

            self._validate_non_blank_text(
                field.name,
                path=f"{field_path}.name",
                source=source,
                label="Struct field name",
            )

            first_field_index = first_field_indexes.get(field.name)
            if first_field_index is not None:
                raise DeclarativeSchemaDuplicateFieldError(
                    field.name,
                    context=self._context(source, f"{field_path}.name"),
                    first_context=self._context(
                        source,
                        f"{path}.fields[{first_field_index}].name",
                    ),
                )
            first_field_indexes[field.name] = field_index

            self._validate_field(
                field,
                path=field_path,
                source=source,
            )

    def _validate_field(
        self,
        field: FieldDefinition,
        *,
        path: str,
        source: str | None,
    ) -> None:
        self._validate_bool(
            field.nullable,
            path=f"{path}.nullable",
            source=source,
            label="Field nullable",
        )

        if field.description is not None:
            self._validate_non_blank_text(
                field.description,
                path=f"{path}.description",
                source=source,
                label="Field description",
            )

        self._validate_type(
            field.data_type,
            path=f"{path}.type",
            source=source,
        )

    def _validate_type(
        self,
        definition: object,
        *,
        path: str,
        source: str | None,
    ) -> None:
        if type(definition) not in _SUPPORTED_TYPE_DEFINITIONS:
            raise DeclarativeSchemaTypeError(
                message=(
                    "Unsupported declarative TypeDefinition subclass "
                    f"{type(definition).__name__!r}."
                ),
                context=self._context(source, path),
            )

        if isinstance(
            definition,
            (
                StringTypeDefinition,
                BooleanTypeDefinition,
                BinaryTypeDefinition,
                DateTypeDefinition,
                UnknownTypeDefinition,
            ),
        ):
            return

        if isinstance(definition, IntegerTypeDefinition):
            self._validate_exact_int(
                definition.bits,
                path=f"{path}.integer.bits",
                source=source,
                label="Integer bits",
            )
            if definition.bits not in _INTEGER_BITS:
                self._raise_type_error(
                    f"Integer bits must be one of {sorted(_INTEGER_BITS)!r}.",
                    path=f"{path}.integer.bits",
                    source=source,
                )
            self._validate_type_bool(
                definition.signed,
                path=f"{path}.integer.signed",
                source=source,
                label="Integer signed",
            )
            return

        if isinstance(definition, FloatTypeDefinition):
            self._validate_exact_int(
                definition.bits,
                path=f"{path}.float.bits",
                source=source,
                label="Float bits",
            )
            if definition.bits not in _FLOAT_BITS:
                self._raise_type_error(
                    f"Float bits must be one of {sorted(_FLOAT_BITS)!r}.",
                    path=f"{path}.float.bits",
                    source=source,
                )
            return

        if isinstance(definition, DecimalTypeDefinition):
            self._validate_decimal(
                definition,
                path=f"{path}.decimal",
                source=source,
            )
            return

        if isinstance(definition, TimeTypeDefinition):
            self._validate_time_unit(
                definition.unit,
                path=f"{path}.time.unit",
                source=source,
            )
            return

        if isinstance(definition, TimestampTypeDefinition):
            self._validate_time_unit(
                definition.unit,
                path=f"{path}.timestamp.unit",
                source=source,
            )
            if definition.timezone is not None:
                if not isinstance(definition.timezone, str):
                    self._raise_type_error(
                        "Timestamp timezone must be a string when provided.",
                        path=f"{path}.timestamp.timezone",
                        source=source,
                    )
                if not definition.timezone.strip():
                    self._raise_type_error(
                        "Timestamp timezone must not be blank.",
                        path=f"{path}.timestamp.timezone",
                        source=source,
                    )
            return

        if isinstance(definition, DurationTypeDefinition):
            self._validate_time_unit(
                definition.unit,
                path=f"{path}.duration.unit",
                source=source,
            )
            return

        if isinstance(definition, ListTypeDefinition):
            self._validate_type_bool(
                definition.element_nullable,
                path=f"{path}.list.element_nullable",
                source=source,
                label="List element_nullable",
            )
            self._validate_type(
                definition.element_type,
                path=f"{path}.list.element.type",
                source=source,
            )
            return

        if isinstance(definition, StructTypeDefinition):
            self._validate_struct(
                definition,
                path=f"{path}.struct",
                source=source,
            )
            return

        if isinstance(definition, MapTypeDefinition):
            self._validate_type_bool(
                definition.value_nullable,
                path=f"{path}.map.value_nullable",
                source=source,
                label="Map value_nullable",
            )
            self._validate_type(
                definition.key_type,
                path=f"{path}.map.key.type",
                source=source,
            )
            self._validate_type(
                definition.value_type,
                path=f"{path}.map.value.type",
                source=source,
            )
            return

        raise AssertionError("Supported TypeDefinition validation is not exhaustive.")

    def _validate_decimal(
        self,
        definition: DecimalTypeDefinition,
        *,
        path: str,
        source: str | None,
    ) -> None:
        self._validate_exact_int(
            definition.precision,
            path=f"{path}.precision",
            source=source,
            label="Decimal precision",
        )
        self._validate_exact_int(
            definition.scale,
            path=f"{path}.scale",
            source=source,
            label="Decimal scale",
        )
        if definition.precision <= 0:
            self._raise_type_error(
                "Decimal precision must be greater than zero.",
                path=f"{path}.precision",
                source=source,
            )
        if definition.scale < 0:
            self._raise_type_error(
                "Decimal scale must be non-negative.",
                path=f"{path}.scale",
                source=source,
            )
        if definition.scale > definition.precision:
            self._raise_type_error(
                "Decimal scale must not exceed precision.",
                path=f"{path}.scale",
                source=source,
            )

    def _validate_struct(
        self,
        definition: StructTypeDefinition,
        *,
        path: str,
        source: str | None,
    ) -> None:
        if not isinstance(definition.fields, tuple):
            self._raise_type_error(
                "Struct fields must be a tuple.",
                path=f"{path}.fields",
                source=source,
            )

        first_field_indexes: dict[str, int] = {}
        for field_index, field in enumerate(definition.fields):
            field_path = f"{path}.fields[{field_index}]"
            if type(field) is not StructFieldDefinition:
                self._raise_type_error(
                    "Struct fields must contain only StructFieldDefinition values.",
                    path=field_path,
                    source=source,
                )

            first_field_index = first_field_indexes.get(field.name)
            if first_field_index is not None:
                raise DeclarativeSchemaDuplicateFieldError(
                    field.name,
                    context=self._context(source, f"{field_path}.name"),
                    first_context=self._context(
                        source,
                        f"{path}.fields[{first_field_index}].name",
                    ),
                )
            first_field_indexes[field.name] = field_index

            self._validate_bool(
                field.nullable,
                path=f"{field_path}.nullable",
                source=source,
                label="Struct field nullable",
            )
            self._validate_type(
                field.data_type,
                path=f"{field_path}.type",
                source=source,
            )

    def _validate_time_unit(
        self,
        unit: object,
        *,
        path: str,
        source: str | None,
    ) -> None:
        if not isinstance(unit, str):
            self._raise_type_error(
                "Temporal unit must be a string.",
                path=path,
                source=source,
            )
        if unit not in _TIME_UNITS:
            self._raise_type_error(
                f"Temporal unit must be one of {sorted(_TIME_UNITS)!r}.",
                path=path,
                source=source,
            )

    def _validate_exact_int(
        self,
        value: object,
        *,
        path: str,
        source: str | None,
        label: str,
    ) -> None:
        if type(value) is not int:
            self._raise_type_error(
                f"{label} must be an int.",
                path=path,
                source=source,
            )

    def _validate_type_bool(
        self,
        value: object,
        *,
        path: str,
        source: str | None,
        label: str,
    ) -> None:
        if type(value) is not bool:
            self._raise_type_error(
                f"{label} must be a bool.",
                path=path,
                source=source,
            )

    def _validate_bool(
        self,
        value: object,
        *,
        path: str,
        source: str | None,
        label: str,
    ) -> None:
        if type(value) is not bool:
            raise DeclarativeSchemaValidationError(
                f"{label} must be a bool.",
                context=self._context(source, path),
            )

    def _validate_non_blank_text(
        self,
        value: object,
        *,
        path: str,
        source: str | None,
        label: str,
    ) -> None:
        if not isinstance(value, str):
            raise DeclarativeSchemaValidationError(
                f"{label} must be a string.",
                context=self._context(source, path),
            )
        if not value.strip():
            raise DeclarativeSchemaValidationError(
                f"{label} must not be blank.",
                context=self._context(source, path),
            )

    def _raise_type_error(
        self,
        message: str,
        *,
        path: str,
        source: str | None,
    ) -> NoReturn:
        raise DeclarativeSchemaTypeError(
            message=message,
            context=self._context(source, path),
        )

    @staticmethod
    def _context(
        source: str | None,
        object_path: str,
    ) -> DeclarativeErrorContext:
        return DeclarativeErrorContext(
            source=source,
            object_path=object_path,
        )
