"""Schema-focused CLI coordination services."""

from __future__ import annotations

from pathlib import Path

from pytransformkit.cli.exceptions import CLIUnsupportedOperationError
from pytransformkit.cli.models.reports import (
    SchemaFieldInspection,
    SchemaInspectionReport,
    SchemaValidationReport,
)
from pytransformkit.domain.data import (
    BinaryType,
    BooleanType,
    DataType,
    DateType,
    DecimalType,
    DurationType,
    FloatType,
    IntegerType,
    ListType,
    MapType,
    StringType,
    StructType,
    TimestampType,
    TimeType,
    UnknownType,
)
from pytransformkit.errors import (
    DeclarativeErrorContext,
    DeclarativeSchemaCardinalityError,
)
from pytransformkit.schema_io import load_schema, load_schemas

_REMOTE_SCHEMES = (
    "http://",
    "https://",
    "s3://",
    "gs://",
    "gcs://",
    "az://",
    "azure://",
    "ftp://",
    "ftps://",
    "ssh://",
)


def _path_text(path: str | Path) -> str:
    return str(path)


def _reject_remote_source(path: str) -> None:
    lowered = path.lstrip().lower()
    if lowered.startswith(_REMOTE_SCHEMES):
        raise CLIUnsupportedOperationError(
            "Remote schema sources are not supported by the PyTransformKit CLI."
        )


def _type_descriptor(data_type: DataType) -> tuple[str, dict[str, object] | None]:
    if isinstance(data_type, StringType):
        return "string", None
    if isinstance(data_type, BooleanType):
        return "boolean", None
    if isinstance(data_type, IntegerType):
        prefix = "int" if data_type.signed else "uint"
        return f"{prefix}{data_type.bits}", None
    if isinstance(data_type, FloatType):
        return f"float{data_type.bits}", None
    if isinstance(data_type, DecimalType):
        return (
            "decimal",
            {
                "precision": data_type.precision,
                "scale": data_type.scale,
            },
        )
    if isinstance(data_type, BinaryType):
        return "binary", None
    if isinstance(data_type, DateType):
        return "date", None
    if isinstance(data_type, TimeType):
        return "time", {"unit": data_type.unit}
    if isinstance(data_type, TimestampType):
        return (
            "timestamp",
            {
                "unit": data_type.unit,
                "timezone": data_type.timezone,
            },
        )
    if isinstance(data_type, DurationType):
        return "duration", {"unit": data_type.unit}
    if isinstance(data_type, UnknownType):
        return "unknown", None
    if isinstance(data_type, ListType):
        element_type, element_details = _type_descriptor(data_type.element_type)
        element: dict[str, object] = {
            "type": element_type,
            "nullable": data_type.element_nullable,
        }
        if element_details is not None:
            element["type_details"] = element_details
        return "list", {"element": element}
    if isinstance(data_type, StructType):
        fields: list[dict[str, object]] = []
        for field in data_type.fields:
            field_type, field_details = _type_descriptor(field.data_type)
            item: dict[str, object] = {
                "name": field.name,
                "type": field_type,
                "nullable": field.nullable,
            }
            if field_details is not None:
                item["type_details"] = field_details
            fields.append(item)
        return "struct", {"fields": fields}
    if isinstance(data_type, MapType):
        key_type, key_details = _type_descriptor(data_type.key_type)
        value_type, value_details = _type_descriptor(data_type.value_type)
        key: dict[str, object] = {"type": key_type}
        value: dict[str, object] = {
            "type": value_type,
            "nullable": data_type.value_nullable,
        }
        if key_details is not None:
            key["type_details"] = key_details
        if value_details is not None:
            value["type_details"] = value_details
        return "map", {
            "key": key,
            "value": value,
        }

    raise TypeError(
        f"Unsupported PyTransformKit data type {type(data_type).__name__!r}."
    )


class SchemaCLIService:
    """Coordinate CLI schema operations through stable public APIs."""

    def validate(self, path: str | Path) -> SchemaValidationReport:
        """Validate one explicitly named local declarative schema file."""
        path_text = _path_text(path)
        _reject_remote_source(path_text)
        load_schema(path_text)
        return SchemaValidationReport(path=path_text, valid=True)

    def inspect(self, path: str | Path) -> SchemaInspectionReport:
        """Inspect one explicit local declarative schema through public APIs."""
        path_text = _path_text(path)
        _reject_remote_source(path_text)
        schemas = load_schemas(path_text)
        if len(schemas) != 1:
            raise DeclarativeSchemaCardinalityError(
                1,
                len(schemas),
                context=DeclarativeErrorContext(source=path_text),
            )

        schema_name, schema = next(iter(schemas.items()))
        fields: list[SchemaFieldInspection] = []
        for field in schema:
            type_name, type_details = _type_descriptor(field.data_type)
            fields.append(
                SchemaFieldInspection(
                    name=field.name,
                    type=type_name,
                    nullable=field.nullable,
                    description=field.description,
                    type_details=type_details,
                )
            )

        return SchemaInspectionReport(
            path=path_text,
            schema_name=schema_name,
            fields=tuple(fields),
        )


__all__ = ["SchemaCLIService"]
