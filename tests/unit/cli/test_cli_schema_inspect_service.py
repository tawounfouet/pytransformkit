from __future__ import annotations

import pytest

from pytransformkit.cli.models.reports import SchemaInspectionReport
from pytransformkit.cli.services import schema as schema_service
from pytransformkit.domain.data import (
    BinaryType,
    BooleanType,
    DateType,
    DecimalType,
    DurationType,
    Field,
    FloatType,
    IntegerType,
    ListType,
    MapType,
    Schema,
    StringType,
    StructField,
    StructType,
    TimestampType,
    TimeType,
    UnknownType,
)
from pytransformkit.errors import DeclarativeSchemaCardinalityError


def test_schema_inspect_preserves_name_order_and_field_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = Schema(
        fields=(
            Field(
                "customer_id",
                IntegerType(bits=64, signed=True),
                nullable=False,
                description="Stable identifier",
            ),
            Field("email", StringType(), nullable=True),
        )
    )
    seen: list[str] = []

    def fake_load_schemas(path: str) -> dict[str, Schema]:
        seen.append(path)
        return {"customers": schema}

    monkeypatch.setattr(schema_service, "load_schemas", fake_load_schemas)

    report = schema_service.SchemaCLIService().inspect("schemas/customers.yml")

    assert isinstance(report, SchemaInspectionReport)
    assert seen == ["schemas/customers.yml"]
    assert report.path == "schemas/customers.yml"
    assert report.schema_name == "customers"
    assert [field.name for field in report.fields] == ["customer_id", "email"]
    assert report.fields[0].type == "int64"
    assert report.fields[0].nullable is False
    assert report.fields[0].description == "Stable identifier"
    assert report.fields[1].type == "string"
    assert report.fields[1].description is None


def test_schema_inspect_describes_all_canonical_type_families(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = Schema(
        fields=(
            Field("text", StringType()),
            Field("flag", BooleanType()),
            Field("signed", IntegerType(bits=32, signed=True)),
            Field("unsigned", IntegerType(bits=16, signed=False)),
            Field("ratio", FloatType(bits=32)),
            Field("amount", DecimalType(precision=18, scale=2)),
            Field("payload", BinaryType()),
            Field("business_date", DateType()),
            Field("local_time", TimeType(unit="ns")),
            Field("occurred_at", TimestampType(unit="ms", timezone="UTC")),
            Field("elapsed", DurationType(unit="s")),
            Field("uncertain", UnknownType()),
            Field(
                "tags",
                ListType(
                    element_type=StringType(),
                    element_nullable=False,
                ),
            ),
            Field(
                "address",
                StructType(
                    fields=(
                        StructField(
                            "city",
                            StringType(),
                            nullable=False,
                        ),
                    )
                ),
            ),
            Field(
                "attributes",
                MapType(
                    key_type=StringType(),
                    value_type=IntegerType(),
                    value_nullable=False,
                ),
            ),
        )
    )
    monkeypatch.setattr(
        schema_service,
        "load_schemas",
        lambda path: {"all_types": schema},
    )

    report = schema_service.SchemaCLIService().inspect("schema.yml")
    by_name = {field.name: field for field in report.fields}

    assert by_name["text"].type == "string"
    assert by_name["flag"].type == "boolean"
    assert by_name["signed"].type == "int32"
    assert by_name["unsigned"].type == "uint16"
    assert by_name["ratio"].type == "float32"
    assert by_name["amount"].type == "decimal"
    assert by_name["amount"].type_details == {"precision": 18, "scale": 2}
    assert by_name["payload"].type == "binary"
    assert by_name["business_date"].type == "date"
    assert by_name["local_time"].type_details == {"unit": "ns"}
    assert by_name["occurred_at"].type_details == {
        "unit": "ms",
        "timezone": "UTC",
    }
    assert by_name["elapsed"].type_details == {"unit": "s"}
    assert by_name["uncertain"].type == "unknown"
    assert by_name["tags"].type_details == {
        "element": {
            "type": "string",
            "nullable": False,
        }
    }
    assert by_name["address"].type_details == {
        "fields": [
            {
                "name": "city",
                "type": "string",
                "nullable": False,
            }
        ]
    }
    assert by_name["attributes"].type_details == {
        "key": {"type": "string"},
        "value": {
            "type": "int64",
            "nullable": False,
        },
    }


def test_schema_inspect_requires_exactly_one_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        schema_service,
        "load_schemas",
        lambda path: {
            "customers": Schema(fields=()),
            "orders": Schema(fields=()),
        },
    )

    with pytest.raises(DeclarativeSchemaCardinalityError) as error:
        schema_service.SchemaCLIService().inspect("schemas.yml")

    assert str(error.value.code) == "PTK-DECL-009"
    assert error.value.required_count == 1
    assert error.value.actual_count == 2
    assert error.value.source == "schemas.yml"


def test_schema_inspection_report_is_not_schema_codec_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        schema_service,
        "load_schemas",
        lambda path: {"customers": Schema(fields=())},
    )

    payload = schema_service.SchemaCLIService().inspect("schema.yml").to_data()

    assert payload == {
        "path": "schema.yml",
        "schema": {
            "name": "customers",
            "fields": [],
        },
    }
    assert "contract" not in payload
    assert "contract_version" not in payload
    assert "payload" not in payload
