"""Internal declarative schema loading and dumping orchestration.

Stable public load/dump functions are intentionally introduced in LOT-37.
"""

from __future__ import annotations

from collections.abc import Mapping

from pytransformkit.domain.data import Schema
from pytransformkit.schema_io._compiler import SchemaDocumentCompiler
from pytransformkit.schema_io._exporter import SchemaDocumentExporter
from pytransformkit.schema_io._validation import SchemaDefinitionValidator
from pytransformkit.schema_io._yaml import YamlSchemaEmitter, YamlSchemaParser


class _DeclarativeSchemaLoader:
    """Wire parser, validator, and compiler without exposing a public API."""

    def __init__(
        self,
        *,
        parser: YamlSchemaParser | None = None,
        validator: SchemaDefinitionValidator | None = None,
        compiler: SchemaDocumentCompiler | None = None,
    ) -> None:
        self._parser = parser or YamlSchemaParser()
        self._validator = validator or SchemaDefinitionValidator()
        self._compiler = compiler or SchemaDocumentCompiler()

    def loads_schema(
        self,
        text: str | bytes,
        *,
        source: str | None = None,
    ) -> Schema:
        """Parse, validate, and compile exactly one declarative schema."""
        document = self._parser.parse(text, source=source)
        self._validator.validate_document(document, source=source)
        return self._compiler.compile_single(document, source=source)

    def loads_schemas(
        self,
        text: str | bytes,
        *,
        source: str | None = None,
    ) -> dict[str, Schema]:
        """Parse, validate, and compile all schemas atomically."""
        document = self._parser.parse(text, source=source)
        self._validator.validate_document(document, source=source)
        return self._compiler.compile(document, source=source)


class _DeclarativeSchemaExporter:
    """Wire Domain export, validation, and YAML emission internally."""

    def __init__(
        self,
        *,
        exporter: SchemaDocumentExporter | None = None,
        validator: SchemaDefinitionValidator | None = None,
        emitter: YamlSchemaEmitter | None = None,
    ) -> None:
        self._exporter = exporter or SchemaDocumentExporter()
        self._validator = validator or SchemaDefinitionValidator()
        self._emitter = emitter or YamlSchemaEmitter()

    def dumps_schema(
        self,
        schema: Schema,
        *,
        name: str,
    ) -> str:
        """Export one schema through definition validation before emission."""
        document = self._exporter.export_single(
            schema,
            name=name,
        )
        self._validator.validate_document(document)
        return self._emitter.emit(
            document,
            multi_schema=False,
        )

    def dumps_schemas(
        self,
        schemas: Mapping[str, Schema],
    ) -> str:
        """Export named schemas while preserving mapping iteration order."""
        document = self._exporter.export_many(schemas)
        self._validator.validate_document(document)
        return self._emitter.emit(
            document,
            multi_schema=True,
        )


def _loads_schema(
    text: str | bytes,
    *,
    source: str | None = None,
) -> Schema:
    """Internal single-schema YAML loading entry point."""
    return _DeclarativeSchemaLoader().loads_schema(text, source=source)


def _loads_schemas(
    text: str | bytes,
    *,
    source: str | None = None,
) -> dict[str, Schema]:
    """Internal multi-schema YAML loading entry point."""
    return _DeclarativeSchemaLoader().loads_schemas(text, source=source)


def _dumps_schema(
    schema: Schema,
    *,
    name: str,
) -> str:
    """Internal single-schema YAML dumping entry point."""
    return _DeclarativeSchemaExporter().dumps_schema(schema, name=name)


def _dumps_schemas(
    schemas: Mapping[str, Schema],
) -> str:
    """Internal multi-schema YAML dumping entry point."""
    return _DeclarativeSchemaExporter().dumps_schemas(schemas)
