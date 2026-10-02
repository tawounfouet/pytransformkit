"""Export canonical Schema values into declarative definition models."""

from __future__ import annotations

from collections.abc import Mapping

from pytransformkit.domain.data import Field, Schema
from pytransformkit.errors import (
    DeclarativeErrorContext,
    DeclarativeSchemaExportError,
)
from pytransformkit.schema_io._model import (
    FieldDefinition,
    SchemaDefinition,
    SchemaDocument,
)
from pytransformkit.schema_io._type_resolution import DeclarativeTypeExporter


class SchemaDefinitionExporter:
    """Project canonical Schema state into declarative V1 definitions."""

    def __init__(
        self,
        type_exporter: DeclarativeTypeExporter | None = None,
    ) -> None:
        self._type_exporter = type_exporter or DeclarativeTypeExporter()

    def export(
        self,
        schema: Schema,
        *,
        name: str,
        source: str | None = None,
        object_path: str = "schema",
    ) -> SchemaDefinition:
        """Export one canonical Schema under an explicit declarative name."""
        self._require_schema(schema, source=source, object_path=object_path)
        self._require_name(
            name,
            source=source,
            object_path=f"{object_path}.name",
        )

        fields = tuple(
            self._export_field(
                field,
                source=source,
                object_path=f"{object_path}.fields[{index}]",
            )
            for index, field in enumerate(schema.fields)
        )
        return SchemaDefinition(name=name, fields=fields)

    def _export_field(
        self,
        field: Field,
        *,
        source: str | None,
        object_path: str,
    ) -> FieldDefinition:
        if not isinstance(field, Field):
            raise DeclarativeSchemaExportError(
                "Canonical Schema fields must contain only Field values.",
                context=_context(source, object_path),
            )

        if not isinstance(field.name, str) or not field.name.strip():
            raise DeclarativeSchemaExportError(
                "Canonical Field name must be a non-empty string.",
                context=_context(source, f"{object_path}.name"),
            )

        if type(field.nullable) is not bool:
            raise DeclarativeSchemaExportError(
                "Canonical Field nullable must be a bool for declarative V1 export.",
                context=_context(source, f"{object_path}.nullable"),
            )

        if field.description is not None:
            if not isinstance(field.description, str) or not field.description.strip():
                raise DeclarativeSchemaExportError(
                    "Canonical Field description must be a non-empty string when present.",
                    context=_context(source, f"{object_path}.description"),
                )

        try:
            data_type = self._type_exporter.export(field.data_type)
        except DeclarativeSchemaExportError as exc:
            raise DeclarativeSchemaExportError(
                f"Canonical Field {field.name!r} has a type that cannot be "
                "represented by declarative V1.",
                context=_context(source, f"{object_path}.type"),
            ) from exc

        return FieldDefinition(
            name=field.name,
            data_type=data_type,
            nullable=field.nullable,
            description=field.description,
        )

    @staticmethod
    def _require_schema(
        schema: object,
        *,
        source: str | None,
        object_path: str,
    ) -> None:
        if not isinstance(schema, Schema):
            raise DeclarativeSchemaExportError(
                "Expected a canonical Schema value.",
                context=_context(source, object_path),
            )
        if not isinstance(schema.fields, tuple):
            raise DeclarativeSchemaExportError(
                "Canonical Schema fields must be a tuple.",
                context=_context(source, f"{object_path}.fields"),
            )

    @staticmethod
    def _require_name(
        name: object,
        *,
        source: str | None,
        object_path: str,
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            raise DeclarativeSchemaExportError(
                "Declarative schema name must be a non-empty string.",
                context=_context(source, object_path),
            )


class SchemaDocumentExporter:
    """Export one or more named canonical schemas into SchemaDocument."""

    def __init__(
        self,
        schema_exporter: SchemaDefinitionExporter | None = None,
    ) -> None:
        self._schema_exporter = schema_exporter or SchemaDefinitionExporter()

    def export_single(
        self,
        schema: Schema,
        *,
        name: str,
        source: str | None = None,
    ) -> SchemaDocument:
        """Export exactly one explicitly named schema."""
        definition = self._schema_exporter.export(
            schema,
            name=name,
            source=source,
            object_path="schema",
        )
        return SchemaDocument(version=1, schemas=(definition,))

    def export_many(
        self,
        schemas: Mapping[str, Schema],
        *,
        source: str | None = None,
    ) -> SchemaDocument:
        """Export a mapping while preserving caller iteration order."""
        if not isinstance(schemas, Mapping):
            raise DeclarativeSchemaExportError(
                "Expected a Mapping[str, Schema] for multi-schema export.",
                context=_context(source, "schemas"),
            )

        definitions: list[SchemaDefinition] = []
        for index, (name, schema) in enumerate(schemas.items()):
            definitions.append(
                self._schema_exporter.export(
                    schema,
                    name=name,
                    source=source,
                    object_path=f"schemas[{index}]",
                )
            )

        return SchemaDocument(
            version=1,
            schemas=tuple(definitions),
        )


def _context(
    source: str | None,
    object_path: str,
) -> DeclarativeErrorContext:
    return DeclarativeErrorContext(
        source=source,
        object_path=object_path,
    )
