"""Stable declarative schema loading and dumping API."""

from __future__ import annotations

import os
from collections.abc import Mapping

from pytransformkit.domain.data import Schema
from pytransformkit.errors import (
    DeclarativeErrorContext,
    DeclarativeSchemaExportError,
    DeclarativeSchemaIOError,
    DeclarativeSchemaValidationError,
)
from pytransformkit.schema_io._compiler import SchemaDocumentCompiler
from pytransformkit.schema_io._exporter import SchemaDocumentExporter
from pytransformkit.schema_io._validation import SchemaDefinitionValidator
from pytransformkit.schema_io._yaml import YamlSchemaEmitter, YamlSchemaParser


class _DeclarativeSchemaLoader:
    """Wire parser, validator, and compiler without exposing a public service."""

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


def load_schema(
    path: str | os.PathLike[str],
) -> Schema:
    """Load exactly one canonical Schema from an explicit UTF-8 YAML file."""
    path_text = _path_text(path)
    text = _read_text(path_text)
    return loads_schema(text, source=path_text)


def loads_schema(
    text: str,
    *,
    source: str | None = None,
) -> Schema:
    """Load exactly one canonical Schema from declarative YAML text."""
    _require_text(text)
    return _loads_schema(text, source=source)


def load_schemas(
    path: str | os.PathLike[str],
) -> dict[str, Schema]:
    """Load one or more named Schemas from an explicit UTF-8 YAML file."""
    path_text = _path_text(path)
    text = _read_text(path_text)
    return loads_schemas(text, source=path_text)


def loads_schemas(
    text: str,
    *,
    source: str | None = None,
) -> dict[str, Schema]:
    """Load one or more named Schemas from declarative YAML text."""
    _require_text(text)
    return _loads_schemas(text, source=source)


def dump_schema(
    schema: Schema,
    path: str | os.PathLike[str],
    *,
    name: str,
) -> None:
    """Write one explicitly named Schema as canonical UTF-8 YAML."""
    path_text = _path_text(path)
    text = dumps_schema(schema, name=name)
    _write_text(path_text, text)


def dumps_schema(
    schema: Schema,
    *,
    name: str,
) -> str:
    """Emit one explicitly named Schema as canonical declarative YAML."""
    try:
        return _dumps_schema(schema, name=name)
    except DeclarativeSchemaValidationError as exc:
        raise DeclarativeSchemaExportError(
            "Generated single-schema declarative document failed validation."
        ) from exc


def dump_schemas(
    schemas: Mapping[str, Schema],
    path: str | os.PathLike[str],
) -> None:
    """Write named Schemas as one canonical UTF-8 YAML document."""
    path_text = _path_text(path)
    text = dumps_schemas(schemas)
    _write_text(path_text, text)


def dumps_schemas(
    schemas: Mapping[str, Schema],
) -> str:
    """Emit named Schemas as canonical declarative YAML."""
    try:
        return _dumps_schemas(schemas)
    except DeclarativeSchemaValidationError as exc:
        raise DeclarativeSchemaExportError(
            "Generated multi-schema declarative document failed validation."
        ) from exc


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


def _read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as stream:
            return stream.read()
    except (OSError, UnicodeError) as exc:
        raise DeclarativeSchemaIOError(
            path,
            "read",
            context=DeclarativeErrorContext(source=path),
        ) from exc


def _write_text(path: str, text: str) -> None:
    try:
        with open(path, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
    except (OSError, UnicodeError) as exc:
        raise DeclarativeSchemaIOError(
            path,
            "write",
            context=DeclarativeErrorContext(source=path),
        ) from exc


def _path_text(path: str | os.PathLike[str]) -> str:
    value = os.fspath(path)
    if not isinstance(value, str):
        raise TypeError("path must resolve to str, not bytes.")
    return value


def _require_text(text: object) -> None:
    if not isinstance(text, str):
        raise TypeError("text must be str.")
