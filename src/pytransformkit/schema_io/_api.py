"""Internal declarative schema loading orchestration.

Stable public load/dump functions are intentionally introduced in LOT-37.
"""

from __future__ import annotations

from pytransformkit.domain.data import Schema
from pytransformkit.schema_io._compiler import SchemaDocumentCompiler
from pytransformkit.schema_io._validation import SchemaDefinitionValidator
from pytransformkit.schema_io._yaml import YamlSchemaParser


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
