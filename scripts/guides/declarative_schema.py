"""Executable companion to the PyTransformKit declarative schema documentation."""

from __future__ import annotations

from pytransformkit.domain.data import (
    DecimalType,
    Field,
    IntegerType,
    ListType,
    MapType,
    Schema,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from pytransformkit.errors import DeclarativeSchemaTypeError
from pytransformkit.schema_io import dumps_schema, dumps_schemas, loads_schema, loads_schemas
from pytransformkit.serialization import SchemaCodec


def _basic_and_equivalence() -> Schema:
    yaml_schema = loads_schema(
        """
version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
    - name: status
      type: string
      nullable: true
      description: Customer status
"""
    )
    python_schema = Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field(
                "status",
                StringType(),
                nullable=True,
                description="Customer status",
            ),
        )
    )
    assert yaml_schema == python_schema
    return yaml_schema


def _primitive_types() -> None:
    schema = loads_schema(
        """
version: 1
schema:
  name: primitive_types
  fields:
    - {name: text, type: string, nullable: true}
    - {name: flag, type: boolean, nullable: true}
    - {name: i8, type: int8, nullable: true}
    - {name: i16, type: int16, nullable: true}
    - {name: i32, type: int32, nullable: true}
    - {name: i64, type: int64, nullable: true}
    - {name: u8, type: uint8, nullable: true}
    - {name: u16, type: uint16, nullable: true}
    - {name: u32, type: uint32, nullable: true}
    - {name: u64, type: uint64, nullable: true}
    - {name: f32, type: float32, nullable: true}
    - {name: f64, type: float64, nullable: true}
    - {name: payload, type: binary, nullable: true}
    - {name: business_date, type: date, nullable: true}
    - {name: uncertain, type: unknown, nullable: true}
"""
    )
    assert len(schema.fields) == 15


def _decimal_and_temporal() -> None:
    decimal_schema = loads_schema(
        """
version: 1
schema:
  name: money
  fields:
    - name: amount
      type:
        decimal:
          precision: 38
          scale: 9
      nullable: false
"""
    )
    assert decimal_schema.fields[0].data_type == DecimalType(precision=38, scale=9)

    temporal = loads_schema(
        """
version: 1
schema:
  name: events
  fields:
    - name: occurred_at
      type:
        timestamp:
          unit: us
          timezone: UTC
      nullable: false
"""
    )
    assert temporal.fields[0].data_type == TimestampType(unit="us", timezone="UTC")


def _nested_types() -> None:
    schema = loads_schema(
        """
version: 1
schema:
  name: nested
  fields:
    - name: profiles
      type:
        list:
          element:
            type:
              struct:
                fields:
                  - name: customer_id
                    type: int64
                    nullable: false
                  - name: attributes
                    type:
                      map:
                        key:
                          type: string
                        value:
                          type: string
                        value_nullable: false
                    nullable: true
          element_nullable: false
      nullable: false
"""
    )

    expected = ListType(
        element_type=StructType(
            fields=(
                StructField("customer_id", IntegerType(), nullable=False),
                StructField(
                    "attributes",
                    MapType(
                        key_type=StringType(),
                        value_type=StringType(),
                        value_nullable=False,
                    ),
                    nullable=True,
                ),
            )
        ),
        element_nullable=False,
    )
    assert schema.fields[0].data_type == expected


def _multi_schema() -> None:
    schemas = loads_schemas(
        """
version: 1
schemas:
  customers:
    fields:
      - name: customer_id
        type: int64
        nullable: false
  orders:
    fields:
      - name: order_id
        type: int64
        nullable: false
      - name: customer_id
        type: int64
        nullable: false
"""
    )
    assert tuple(schemas) == ("customers", "orders")
    emitted = dumps_schemas(schemas)
    assert loads_schemas(emitted) == schemas


def _round_trip_and_wire(schema: Schema) -> None:
    yaml_text = dumps_schema(schema, name="customers")
    assert loads_schema(yaml_text) == schema
    assert dumps_schema(loads_schema(yaml_text), name="customers") == yaml_text

    wire = SchemaCodec.to_json(schema)
    assert SchemaCodec.from_json(wire) == schema
    assert SchemaCodec.contract == "pytransformkit.schema"
    assert SchemaCodec.contract_version == 1


def _typed_error() -> None:
    try:
        loads_schema(
            """
version: 1
schema:
  name: invalid
  fields:
    - name: payload
      type: not-a-type
"""
        )
    except DeclarativeSchemaTypeError as error:
        assert str(error.error_code) == "PTK-DECL-005"
    else:
        raise AssertionError("Expected DeclarativeSchemaTypeError.")


def main() -> int:
    schema = _basic_and_equivalence()
    _primitive_types()
    _decimal_and_temporal()
    _nested_types()
    _multi_schema()
    _round_trip_and_wire(schema)
    _typed_error()
    print("Declarative schema documentation examples: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
