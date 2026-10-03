# PyTransformKit Declarative Schema — Getting Started

PyTransformKit 1.1 adds a stable declarative authoring layer for the canonical
`Schema` Domain model. The declarative format is designed for human-authored
YAML while `SchemaCodec` remains the canonical machine wire contract.

## 1. Install the YAML capability

Declarative YAML support is intentionally optional:

```bash
pip install "pytransformkit[yaml]"
```

The core package keeps a zero mandatory runtime-dependency baseline. Importing
`pytransformkit` or `pytransformkit.schema_io` does not require PyYAML. A YAML
operation without the extra fails explicitly with `PTK-DECL-010`.

## 2. Stable public namespace

The stable authoring surface lives under:

```python
from pytransformkit.schema_io import (
    dump_schema,
    dump_schemas,
    dumps_schema,
    dumps_schemas,
    load_schema,
    load_schemas,
    loads_schema,
    loads_schemas,
)
```

These eight functions are additive to the 1.0 public contract and are not
promoted to the package root.

## 3. Author a Schema in Python

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

`Schema` remains the canonical semantic authority. Declarative YAML does not
introduce a second runtime schema model.

## 4. Author the equivalent Schema in YAML

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

Load it from memory:

```python
from pytransformkit.schema_io import loads_schema

schema = loads_schema(
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
```

Or from a file:

```python
from pytransformkit.schema_io import load_schema

schema = load_schema("schemas/customers.yml")
```

## 5. Dump a Schema to canonical YAML

```python
from pytransformkit.schema_io import dumps_schema

yaml_text = dumps_schema(schema, name="customers")
print(yaml_text)
```

To write directly to a file:

```python
from pytransformkit.schema_io import dump_schema

dump_schema(schema, "schemas/customers.yml", name="customers")
```

The emitter produces deterministic UTF-8 YAML with one final newline. A
successful canonical round-trip satisfies:

```text
Schema
  ↓ dumps_schema
canonical YAML
  ↓ loads_schema
Schema'

Schema == Schema'
```

## 6. Multiple schemas in one document

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
```

Load the mapping:

```python
from pytransformkit.schema_io import load_schemas

schemas = load_schemas("schemas/domain.yml")

customers = schemas["customers"]
orders = schemas["orders"]
```

And emit a mapping of Schemas:

```python
from pytransformkit.schema_io import dumps_schemas

text = dumps_schemas(
    {
        "customers": customers,
        "orders": orders,
    }
)
```

## 7. Python and YAML are equivalent authoring paths

The declarative layer compiles into the same Domain values used by Python
authoring:

```text
Python authoring ───────────────┐
                               ↓
                             Schema
                               ↑
YAML → hardened parser → compiler
```

The YAML `schema.name` identifies the declaration for authoring and
multi-schema lookup. It is not part of canonical `Schema` state.

## 8. YAML is not the wire contract

Use declarative YAML for human authoring. Use `SchemaCodec` when you need the
versioned canonical JSON wire format:

```python
from pytransformkit.serialization import SchemaCodec

codec = SchemaCodec()
payload = codec.to_json(schema)
restored = codec.from_json(payload)

assert restored == schema
```

The two contracts remain deliberately distinct:

```text
Declarative YAML
  human authoring
  version: 1
  canonicalizable presentation

SchemaCodec JSON
  machine interchange
  contract: pytransformkit.schema
  contract_version: 1
  byte-frozen wire compatibility
```

Adding declarative YAML in 1.1 does not change the existing SchemaCodec wire
bytes, contract ID or contract version.

## 9. Error handling

All released declarative failures inherit from
`DeclarativeSchemaError` and from `PyTransformKitError`.

```python
from pytransformkit.errors import DeclarativeSchemaError
from pytransformkit.schema_io import loads_schema

try:
    loads_schema("version: 99\nschema:\n  name: invalid\n  fields: []\n")
except DeclarativeSchemaError as error:
    print(error.error_code)
    print(error)
```

The stable declarative code range is:

```text
PTK-DECL-000 → PTK-DECL-013
```

Notable codes include:

- `PTK-DECL-001` — unsafe or invalid YAML syntax;
- `PTK-DECL-002` — unsupported declarative version;
- `PTK-DECL-003` — structural/semantic validation failure;
- `PTK-DECL-005` — invalid logical type;
- `PTK-DECL-010` — optional YAML dependency unavailable;
- `PTK-DECL-011` — filesystem I/O failure;
- `PTK-DECL-012` — export failure;
- `PTK-DECL-013` — defensive resource limit exceeded.

## 10. Security model

Declarative input is treated as untrusted data. The parser rejects or prevents:

- Python/object YAML tags;
- custom tags;
- anchors and aliases;
- merge keys;
- duplicate mapping keys;
- multi-document streams;
- non-finite numbers;
- oversized or excessively nested documents;
- implicit file includes;
- network access;
- environment-variable interpolation;
- plugin or execution-engine activation.

The supported path is intentionally narrow:

```text
untrusted YAML
      ↓
hardened parser
      ↓
declarative definitions
      ↓
semantic validation
      ↓
compiler
      ↓
canonical Schema
```

## 11. Where to continue

For complete examples covering primitive, decimal, temporal, nested and
multi-schema declarations, see:

`docs/specifications/42_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_REFERENCE_EXAMPLES.md`

The frozen public API is defined by:

- `contracts/public_api_v1_1.json`;
- `contracts/error_codes_v1_1.json`.

Executable documentation is qualified in CI through
`scripts/guides/declarative_schema.py`.
