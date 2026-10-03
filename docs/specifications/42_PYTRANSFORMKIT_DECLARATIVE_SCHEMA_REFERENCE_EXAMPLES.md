# PyTransformKit Declarative Schema — Reference Examples

This reference uses the frozen PyTransformKit 1.1 declarative grammar. All
examples compile to the canonical Domain `Schema` model through
`pytransformkit.schema_io`.

## 1. Basic customer schema

```yaml
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
```

Equivalent Python:

```python
from pytransformkit.domain.data import Field, IntegerType, Schema, StringType

schema = Schema(
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
```

## 2. Primitive logical types

```yaml
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
```

The authoring aliases `integer` and `float` normalize canonically to
`int64` and `float64`.

## 3. Decimal

```yaml
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
      description: High precision amount
```

Equivalent Python type:

```python
from pytransformkit.domain.data import DecimalType

amount_type = DecimalType(precision=38, scale=9)
```

## 4. Temporal types

```yaml
version: 1
schema:
  name: events
  fields:
    - name: default_time
      type: time
      nullable: true
    - name: ns_time
      type:
        time:
          unit: ns
      nullable: false
    - name: default_timestamp
      type: timestamp
      nullable: true
    - name: utc_timestamp
      type:
        timestamp:
          unit: us
          timezone: UTC
      nullable: false
    - name: ns_timestamp
      type:
        timestamp:
          unit: ns
      nullable: true
    - name: default_duration
      type: duration
      nullable: true
    - name: seconds_duration
      type:
        duration:
          unit: s
      nullable: false
```

Allowed time units are `s`, `ms`, `us`, and `ns`. The default unit for
`time`, `timestamp`, and `duration` is `us`.

## 5. List

```yaml
version: 1
schema:
  name: tags
  fields:
    - name: tags
      type:
        list:
          element:
            type: string
          element_nullable: false
      nullable: true
```

Equivalent Python:

```python
from pytransformkit.domain.data import Field, ListType, Schema, StringType

schema = Schema(
    fields=(
        Field(
            "tags",
            ListType(
                element_type=StringType(),
                element_nullable=False,
            ),
        ),
    )
)
```

## 6. Struct

```yaml
version: 1
schema:
  name: profile
  fields:
    - name: profile
      type:
        struct:
          fields:
            - name: customer_id
              type: int64
              nullable: false
            - name: email
              type: string
              nullable: true
      nullable: false
```

Equivalent Python:

```python
from pytransformkit.domain.data import (
    IntegerType,
    StringType,
    StructField,
    StructType,
)

profile_type = StructType(
    fields=(
        StructField("customer_id", IntegerType(), nullable=False),
        StructField("email", StringType(), nullable=True),
    )
)
```

## 7. Map

```yaml
version: 1
schema:
  name: attributes
  fields:
    - name: attributes
      type:
        map:
          key:
            type: string
          value:
            type: string
          value_nullable: false
      nullable: true
```

Equivalent Python:

```python
from pytransformkit.domain.data import MapType, StringType

attributes_type = MapType(
    key_type=StringType(),
    value_type=StringType(),
    value_nullable=False,
)
```

## 8. Deeply nested list / struct / map

```yaml
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
                          type:
                            list:
                              element:
                                type: string
                              element_nullable: false
                        value_nullable: false
                    nullable: true
          element_nullable: false
      nullable: false
```

Nested nullability is semantic state and survives YAML → Schema → YAML
round-trips.

## 9. Multiple schemas

```yaml
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
  payments:
    fields:
      - name: payment_id
        type: string
        nullable: false
      - name: amount
        type:
          decimal:
            precision: 18
            scale: 2
        nullable: false
```

```python
from pytransformkit.schema_io import loads_schemas

schemas = loads_schemas(text)

assert tuple(schemas) == ("customers", "orders", "payments")
```

Declaration order is preserved.

## 10. Load / dump round-trip

```python
from pytransformkit.schema_io import dumps_schema, loads_schema

schema = loads_schema(
    """
version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
"""
)

canonical_yaml = dumps_schema(schema, name="customers")
restored = loads_schema(canonical_yaml)

assert restored == schema
assert dumps_schema(restored, name="customers") == canonical_yaml
```

The second assertion proves canonical emission is idempotent.

## 11. Python vs YAML equivalence

```python
from pytransformkit.domain.data import Field, IntegerType, Schema
from pytransformkit.schema_io import loads_schema

python_schema = Schema(
    fields=(
        Field("customer_id", IntegerType(), nullable=False),
    )
)

yaml_schema = loads_schema(
    """
version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
"""
)

assert yaml_schema == python_schema
```

The YAML declaration name is authoring metadata and is not stored in the
canonical `Schema` value.

## 12. YAML / wire bridge

```python
from pytransformkit.schema_io import loads_schema
from pytransformkit.serialization import SchemaCodec

schema = loads_schema(yaml_text)

codec = SchemaCodec()\nwire = codec.to_json(schema)
restored = codec.from_json(wire)

assert restored == schema
assert codec.contract == "pytransformkit.schema"
assert codec.contract_version == 1
```

Declarative YAML is not a replacement for the canonical JSON wire contract.

## 13. Error handling

```python
from pytransformkit.errors import (
    DeclarativeSchemaError,
    DeclarativeSchemaTypeError,
)
from pytransformkit.schema_io import loads_schema

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
except DeclarativeSchemaError:
    raise AssertionError("Unexpected declarative error classification")
```

## 14. Missing YAML dependency

The namespace stays importable without the `yaml` extra. Actual YAML
operations fail closed:

```text
pytransformkit.schema_io import          PASS
PyYAML absent                            PASS
loads_schema(...)                        PTK-DECL-010
```

Install the capability with:

```bash
pip install "pytransformkit[yaml]"
```

## 15. Security-sensitive syntax

The following features are deliberately unsupported and rejected:

```yaml
# custom / object tags
value: !Custom {}

# anchors / aliases
base: &base
  type: string
copy: *base

# merge keys
value:
  <<: *base
```

Multi-document YAML, duplicate keys, unsafe Python tags, non-finite numbers and
resource-limit violations are also rejected.

## 16. Canonical fixtures

The repository freezes representative canonical YAML under:

```text
tests/fixtures/schema_io/
├── schema_basic_v1.yml
├── schema_all_primitive_types_v1.yml
├── schema_decimal_v1.yml
├── schema_temporal_v1.yml
├── schema_nested_v1.yml
└── schemas_multi_v1.yml
```

The executable counterpart of this reference is:

`scripts/guides/declarative_schema.py`
