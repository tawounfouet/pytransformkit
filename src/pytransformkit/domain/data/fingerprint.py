"""Deterministic semantic fingerprints for logical Schema values."""

from __future__ import annotations

import hashlib
import json

from pytransformkit.domain.data.data_types import (
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
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.shared.fingerprint import Fingerprint


def schema_fingerprint(schema: Schema) -> Fingerprint:
    """Fingerprint ordered field names, types and nullability."""
    if not isinstance(schema, Schema):
        raise TypeError("schema_fingerprint requires a Schema.")

    payload = [
        {
            "name": field.name,
            "data_type": _data_type_payload(field.data_type),
            "nullable": field.nullable,
        }
        for field in schema.fields
    ]
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return Fingerprint(
        algorithm="sha256",
        value=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )


def _data_type_payload(data_type: DataType) -> object:
    if isinstance(data_type, StringType):
        return {"type": "string"}
    if isinstance(data_type, BooleanType):
        return {"type": "boolean"}
    if isinstance(data_type, IntegerType):
        return {
            "type": "integer",
            "bits": data_type.bits,
            "signed": data_type.signed,
        }
    if isinstance(data_type, FloatType):
        return {"type": "float", "bits": data_type.bits}
    if isinstance(data_type, DecimalType):
        return {
            "type": "decimal",
            "precision": data_type.precision,
            "scale": data_type.scale,
        }
    if isinstance(data_type, DateType):
        return {"type": "date"}
    if isinstance(data_type, TimeType):
        return {"type": "time", "unit": data_type.unit}
    if isinstance(data_type, TimestampType):
        return {
            "type": "timestamp",
            "unit": data_type.unit,
            "timezone": data_type.timezone,
        }
    if isinstance(data_type, DurationType):
        return {"type": "duration", "unit": data_type.unit}
    if isinstance(data_type, BinaryType):
        return {"type": "binary"}
    if isinstance(data_type, ListType):
        return {
            "type": "list",
            "element_type": _data_type_payload(data_type.element_type),
            "element_nullable": data_type.element_nullable,
        }
    if isinstance(data_type, StructType):
        return {
            "type": "struct",
            "fields": [
                {
                    "name": field.name,
                    "data_type": _data_type_payload(field.data_type),
                    "nullable": field.nullable,
                }
                for field in data_type.fields
            ],
        }
    if isinstance(data_type, MapType):
        return {
            "type": "map",
            "key_type": _data_type_payload(data_type.key_type),
            "value_type": _data_type_payload(data_type.value_type),
            "value_nullable": data_type.value_nullable,
        }
    if isinstance(data_type, UnknownType):
        return {"type": "unknown"}
    raise TypeError(f"Unsupported logical DataType {type(data_type).__name__!r}.")
