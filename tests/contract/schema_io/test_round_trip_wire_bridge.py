from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import pytest

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
from pytransformkit.schema_io import (
    dumps_schema,
    dumps_schemas,
    loads_schema,
    loads_schemas,
)
from pytransformkit.serialization import SchemaCodec

pytest.importorskip("yaml")

_FIXTURES = Path(__file__).parents[2] / "fixtures"
_SCHEMA_IO_FIXTURES = _FIXTURES / "schema_io"
_WIRE_FIXTURES = _FIXTURES / "wire"


def _basic_schema() -> Schema:
    return Schema(
        fields=(
            Field(
                "customer_id",
                IntegerType(),
                nullable=False,
            ),
            Field(
                "status",
                StringType(),
                description="Customer status",
            ),
        )
    )


def _primitive_schema() -> Schema:
    return Schema(
        fields=(
            Field("text", StringType()),
            Field("flag", BooleanType()),
            Field("i8", IntegerType(bits=8, signed=True)),
            Field("i16", IntegerType(bits=16, signed=True)),
            Field("i32", IntegerType(bits=32, signed=True)),
            Field("i64", IntegerType(bits=64, signed=True)),
            Field("u8", IntegerType(bits=8, signed=False)),
            Field("u16", IntegerType(bits=16, signed=False)),
            Field("u32", IntegerType(bits=32, signed=False)),
            Field("u64", IntegerType(bits=64, signed=False)),
            Field("f32", FloatType(bits=32)),
            Field("f64", FloatType(bits=64)),
            Field("payload", BinaryType()),
            Field("business_date", DateType()),
            Field("uncertain", UnknownType()),
        )
    )


def _decimal_schema() -> Schema:
    return Schema(
        fields=(
            Field(
                "amount",
                DecimalType(precision=38, scale=9),
                nullable=False,
                description="High precision amount",
            ),
        )
    )


def _temporal_schema() -> Schema:
    return Schema(
        fields=(
            Field("default_time", TimeType()),
            Field("ns_time", TimeType(unit="ns"), nullable=False),
            Field("default_timestamp", TimestampType()),
            Field(
                "utc_timestamp",
                TimestampType(unit="us", timezone="UTC"),
                nullable=False,
            ),
            Field("ns_timestamp", TimestampType(unit="ns")),
            Field("default_duration", DurationType()),
            Field(
                "seconds_duration",
                DurationType(unit="s"),
                nullable=False,
            ),
        )
    )


def _nested_schema() -> Schema:
    return Schema(
        fields=(
            Field(
                "profiles",
                ListType(
                    element_type=StructType(
                        fields=(
                            StructField(
                                "customer_id",
                                IntegerType(),
                                nullable=False,
                            ),
                            StructField(
                                "attributes",
                                MapType(
                                    key_type=StringType(),
                                    value_type=ListType(
                                        element_type=StringType(),
                                        element_nullable=False,
                                    ),
                                    value_nullable=False,
                                ),
                                nullable=True,
                            ),
                        )
                    ),
                    element_nullable=False,
                ),
                nullable=False,
            ),
        )
    )


_SINGLE_GOLDENS = (
    ("schema_basic_v1.yml", "customers", _basic_schema),
    ("schema_all_primitive_types_v1.yml", "primitive_types", _primitive_schema),
    ("schema_decimal_v1.yml", "money", _decimal_schema),
    ("schema_temporal_v1.yml", "events", _temporal_schema),
    ("schema_nested_v1.yml", "nested", _nested_schema),
)


@pytest.mark.parametrize(("fixture_name", "schema_name", "factory"), _SINGLE_GOLDENS)
def test_single_schema_goldens_are_semantically_and_byte_stable(
    fixture_name: str,
    schema_name: str,
    factory: object,
) -> None:
    expected_text = (_SCHEMA_IO_FIXTURES / fixture_name).read_text(encoding="utf-8")
    expected_schema = factory()  # type: ignore[operator]

    loaded = loads_schemas(expected_text)
    assert tuple(loaded) == (schema_name,)
    assert loaded[schema_name] == expected_schema

    emitted = dumps_schema(expected_schema, name=schema_name)
    assert emitted == expected_text
    assert loads_schema(emitted) == expected_schema
    assert dumps_schema(loads_schema(emitted), name=schema_name) == emitted


def test_multi_schema_golden_preserves_identity_order_and_semantics() -> None:
    expected_text = (_SCHEMA_IO_FIXTURES / "schemas_multi_v1.yml").read_text(
        encoding="utf-8"
    )
    expected = OrderedDict(
        (
            (
                "customers",
                Schema(
                    fields=(
                        Field(
                            "customer_id",
                            IntegerType(),
                            nullable=False,
                        ),
                    )
                ),
            ),
            (
                "orders",
                Schema(
                    fields=(
                        Field("order_id", IntegerType(), nullable=False),
                        Field("customer_id", IntegerType(), nullable=False),
                    )
                ),
            ),
            (
                "payments",
                Schema(
                    fields=(
                        Field("payment_id", StringType(), nullable=False),
                        Field(
                            "amount",
                            DecimalType(precision=18, scale=2),
                            nullable=False,
                        ),
                    )
                ),
            ),
        )
    )

    loaded = loads_schemas(expected_text)

    assert tuple(loaded) == tuple(expected)
    assert loaded == dict(expected)
    assert dumps_schemas(expected) == expected_text
    assert loads_schemas(dumps_schemas(expected)) == dict(expected)


def test_authoring_aliases_and_default_forms_normalize_canonically() -> None:
    authored = """\
version: 1
schema:
  name: normalized
  fields:
    - name: integer_value
      type: integer
    - name: float_value
      type: float
    - name: timestamp_value
      type:
        timestamp:
          unit: us
    - name: time_value
      type:
        time:
          unit: us
    - name: duration_value
      type:
        duration:
          unit: us
"""
    schema = loads_schema(authored)
    canonical = dumps_schema(schema, name="normalized")

    assert "type: integer\n" not in canonical
    assert "type: float\n" not in canonical
    assert "type: int64\n" in canonical
    assert "type: float64\n" in canonical
    assert "type: timestamp\n" in canonical
    assert "type: time\n" in canonical
    assert "type: duration\n" in canonical
    assert canonical.count("nullable: true") == 5
    assert dumps_schema(loads_schema(canonical), name="normalized") == canonical


def test_unicode_and_field_description_survive_semantic_round_trip() -> None:
    schema = Schema(
        fields=(
            Field(
                "libellé",
                StringType(),
                nullable=False,
                description="Client déjà actif — Île-de-France",
            ),
        )
    )

    emitted = dumps_schema(schema, name="données_clients")
    restored = loads_schema(emitted)

    assert restored == schema
    assert restored.fields[0].description == "Client déjà actif — Île-de-France"
    assert "données_clients" in emitted
    assert "\\u" not in emitted


def test_schema_codec_wire_contract_remains_frozen_at_v1() -> None:
    assert SchemaCodec.contract == "pytransformkit.schema"
    assert SchemaCodec.contract_version == 1

    codec = SchemaCodec()
    assert codec.contract == "pytransformkit.schema"
    assert codec.contract_version == 1


def test_yaml_basic_golden_composes_to_unchanged_schema_codec_golden() -> None:
    yaml_text = (_SCHEMA_IO_FIXTURES / "schema_basic_v1.yml").read_text(
        encoding="utf-8"
    )
    wire_golden = (_WIRE_FIXTURES / "schema_v1.json").read_bytes()
    schema = loads_schema(yaml_text)
    codec = SchemaCodec()

    assert schema == _basic_schema()
    assert codec.to_bytes(schema) + b"\n" == wire_golden
    assert codec.from_json(wire_golden) == schema


def test_wire_golden_composes_through_yaml_without_wire_drift() -> None:
    wire_golden = (_WIRE_FIXTURES / "schema_v1.json").read_bytes()
    codec = SchemaCodec()

    from_wire = codec.from_json(wire_golden)
    yaml_text = dumps_schema(from_wire, name="customers")
    from_yaml = loads_schema(yaml_text)

    assert from_yaml == from_wire == _basic_schema()
    assert codec.to_bytes(from_yaml) + b"\n" == wire_golden
    assert codec.from_json(codec.to_json(from_yaml)) == from_yaml


@pytest.mark.parametrize(
    ("fixture_name", "schema_name"),
    (
        ("schema_basic_v1.yml", "customers"),
        ("schema_all_primitive_types_v1.yml", "primitive_types"),
        ("schema_decimal_v1.yml", "money"),
        ("schema_temporal_v1.yml", "events"),
        ("schema_nested_v1.yml", "nested"),
    ),
)
def test_yaml_schema_codec_schema_bridge_is_semantically_closed(
    fixture_name: str,
    schema_name: str,
) -> None:
    yaml_text = (_SCHEMA_IO_FIXTURES / fixture_name).read_text(encoding="utf-8")
    codec = SchemaCodec()

    schema_from_yaml = loads_schema(yaml_text)
    schema_from_wire = codec.from_json(codec.to_json(schema_from_yaml))
    yaml_from_wire = dumps_schema(schema_from_wire, name=schema_name)
    restored = loads_schema(yaml_from_wire)

    assert schema_from_wire == schema_from_yaml
    assert restored == schema_from_yaml
    assert codec.fingerprint(schema_from_wire) == codec.fingerprint(schema_from_yaml)
    assert codec.fingerprint(restored) == codec.fingerprint(schema_from_yaml)


def test_python_yaml_and_wire_values_share_one_schema_fingerprint() -> None:
    python_schema = _basic_schema()
    yaml_schema = loads_schema(
        (_SCHEMA_IO_FIXTURES / "schema_basic_v1.yml").read_text(encoding="utf-8")
    )
    wire_schema = SchemaCodec().from_json(
        (_WIRE_FIXTURES / "schema_v1.json").read_bytes()
    )
    codec = SchemaCodec()

    assert python_schema == yaml_schema == wire_schema
    assert codec.fingerprint(python_schema) == codec.fingerprint(yaml_schema)
    assert codec.fingerprint(python_schema) == codec.fingerprint(wire_schema)


def test_declarative_name_is_independent_from_schema_codec_fingerprint() -> None:
    schema = _basic_schema()
    customers_yaml = dumps_schema(schema, name="customers")
    clients_yaml = dumps_schema(schema, name="clients")
    codec = SchemaCodec()

    customers_schema = loads_schema(customers_yaml)
    clients_schema = loads_schema(clients_yaml)

    assert customers_yaml != clients_yaml
    assert customers_schema == clients_schema == schema
    assert codec.fingerprint(customers_schema) == codec.fingerprint(clients_schema)
    assert codec.to_bytes(customers_schema) == codec.to_bytes(clients_schema)


def test_declarative_yaml_bytes_are_not_wire_bytes() -> None:
    schema = _basic_schema()
    yaml_bytes = dumps_schema(schema, name="customers").encode("utf-8")
    wire_bytes = SchemaCodec().to_bytes(schema)

    assert yaml_bytes != wire_bytes
    assert yaml_bytes.startswith(b"version: 1\n")
    assert wire_bytes.startswith(b'{"contract":"pytransformkit.schema"')
