# 37 — PyTransformKit Declarative Schema — Round-Trip and Serialization Model

> **Document status:** DRAFT NORMATIVE SPECIFICATION  
> **Depends on:** 31_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SPECIFICATION.md  
> **Depends on:** 32_PYTRANSFORMKIT_DECLARATIVE_TYPE_SYSTEM_MAPPING.md  
> **Depends on:** 33_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_DOMAIN_MODEL.md  
> **Depends on:** 34_PYTRANSFORMKIT_SCHEMA_LOADER_COMPILER_AND_EXPORTER_SPEC.md  
> **Depends on:** 36_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SECURITY_AND_PARSING_POLICY.md  
> **Existing wire contract:** pytransformkit.schema / contract_version 1  
> **Declarative language version:** 1

---

# 1. Purpose

This document defines the relationship between declarative schema YAML and the existing canonical PyTransformKit serialization contracts.

It freezes:

- semantic round-trip guarantees;
- what state is lossless;
- what authoring information is intentionally not preserved;
- canonical declarative emission;
- the boundary between YAML and SchemaCodec;
- schema-name handling;
- single-schema and multi-schema identity;
- fingerprinting rules;
- package, declarative-language and wire-version independence;
- migration boundaries;
- compatibility expectations;
- golden/conformance testing strategy.

The governing distinction is:

~~~text
YAML = human authoring representation

SchemaCodec JSON = canonical software interchange representation

Schema = canonical logical Domain value
~~~

---

# 2. Three representations

PyTransformKit declarative schema support introduces three related but non-equivalent representations.

~~~text
1. DECLARATIVE AUTHORING
   YAML / SchemaDocument / SchemaDefinition

2. CANONICAL DOMAIN
   Schema / Field / DataType / StructField

3. CANONICAL WIRE
   SchemaCodec JSON contract
~~~

No layer replaces another.

---

# 3. Existing canonical wire contract

PyTransformKit already provides:

~~~python
SchemaCodec
~~~

with:

~~~text
contract = pytransformkit.schema
contract_version = 1
~~~

This existing wire contract remains authoritative for portable software interchange and canonical Schema fingerprinting.

---

# 4. Existing wire envelope

The canonical Schema wire representation uses the standard ContractCodec envelope:

~~~json
{
  "contract": "pytransformkit.schema",
  "contract_version": 1,
  "payload": {
    "...": "typed canonical Schema payload"
  }
}
~~~

Declarative YAML MUST NOT change this envelope.

---

# 5. Existing wire guarantees remain frozen

Declarative YAML does not weaken or redefine existing SchemaCodec guarantees, including:

- deterministic canonical JSON;
- UTF-8 representation;
- explicit contract identifier;
- explicit integer contract version;
- closed semantic type registry;
- unknown-type rejection;
- strict payload parsing;
- duplicate-key rejection;
- payload-size limits;
- nesting limits;
- migration hooks;
- SHA-256 fingerprinting over canonical bytes.

---

# 6. Declarative YAML is not SchemaCodec V2

Adding YAML authoring does NOT create:

~~~text
pytransformkit.schema contract_version = 2
~~~

and does NOT alter SchemaCodec version 1.

YAML is a separate authoring language with its own version namespace.

---

# 7. Version namespaces

At least three independent versions exist:

~~~text
PyTransformKit package version
Declarative schema language version
SchemaCodec wire contract version
~~~

Example:

~~~text
package version                  1.1.0
declarative schema version      1
SchemaCodec contract_version    1
~~~

This combination is valid.

---

# 8. Version independence rule

A change in one version namespace MUST NOT automatically force a change in another.

Examples:

- releasing PyTransformKit 1.1.0 does not imply declarative version 2;
- adding declarative authoring does not imply SchemaCodec version 2;
- a future SchemaCodec migration does not automatically imply declarative version 2.

Version changes are driven by contract semantics, not release-number coincidence.

---

# 9. Canonical semantic authority

The canonical semantic authority remains:

~~~text
Schema
Field
DataType
StructField
~~~

Both YAML and SchemaCodec encode or decode these semantics through different boundaries.

---

# 10. Forward conversion

Declarative loading follows:

~~~text
YAML
 ↓
SchemaDocument
 ↓
SchemaDefinition
 ↓
compiler
 ↓
Schema
~~~

The result is an ordinary canonical Schema indistinguishable from an equivalent Schema constructed directly in Python.

---

# 11. Reverse conversion

Declarative emission follows:

~~~text
Schema
 ↓
SchemaDefinitionExporter
 ↓
SchemaDefinition
 ↓
SchemaDocument
 ↓
YamlSchemaEmitter
 ↓
YAML
~~~

The reverse path is an Application-layer projection of canonical Domain state.

---

# 12. Primary round-trip guarantee

The principal V1 round-trip guarantee is:

~~~text
Schema
  ↓ dumps_schema(name=...)
YAML
  ↓ loads_schema(...)
Schema'

Schema == Schema'
~~~

This is semantic equality, not textual equality.

---

# 13. Type round-trip guarantee

For every supported canonical DataType:

~~~text
DataType
  ↓ declarative export
TypeDefinition / YAML
  ↓ declarative parse + resolve
DataType'

DataType == DataType'
~~~

This guarantee is recursive for list, struct and map types.

---

# 14. Field round-trip guarantee

The following canonical Field state MUST survive YAML round-trip:

~~~text
name
data_type
nullable
description
~~~

Field order within Schema MUST also survive.

---

# 15. Schema round-trip guarantee

The following canonical Schema state MUST survive:

~~~text
ordered tuple of Fields
all Field semantics
all nested DataType semantics
~~~

Nothing else is currently part of canonical Schema state.

---

# 16. Lossless DataType state

Declarative round-trip MUST preserve:

- integer width;
- integer signedness;
- float width;
- decimal precision;
- decimal scale;
- temporal units;
- timestamp timezone;
- list element type;
- list element nullability;
- struct field order;
- struct field types;
- struct field nullability;
- map key type;
- map value type;
- map value nullability;
- intentional UnknownType.

---

# 17. No semantic degradation

The exporter MUST NOT simplify canonical Domain state in a way that loses meaning.

Examples of prohibited degradation:

~~~text
uint32 → integer
float32 → float64
timestamp(ns) → timestamp(us)
timestamp(timezone=UTC) → timezone omitted
nullable=false → nullable=true
~~~

If state cannot be represented, export fails.

---

# 18. Authoring aliases are not preserved

Accepted author aliases normalize away.

Example:

~~~yaml
type: integer
~~~

loads as:

~~~text
IntegerType(bits=64, signed=true)
~~~

and canonical declarative export produces:

~~~yaml
type: int64
~~~

This is a successful semantic round-trip.

---

# 19. Short/long syntax is not preserved

Equivalent authoring forms MAY normalize to one canonical output.

Example input:

~~~yaml
type:
  timestamp:
    unit: us
~~~

may emit canonically as:

~~~yaml
type: timestamp
~~~

because both represent:

~~~text
TimestampType(unit="us", timezone=None)
~~~

---

# 20. Comments are not preserved

Input:

~~~yaml
# Business identifier
- name: customer_id
  type: int64
~~~

does not require the output to retain the comment.

Comments are authoring-only text, not Schema semantics.

---

# 21. Whitespace is not preserved

Indentation, blank lines and spacing are not part of semantic round-trip.

The emitter chooses deterministic canonical formatting.

---

# 22. Quoting style is not preserved

These authoring forms may be equivalent:

~~~yaml
name: customers
~~~

~~~yaml
name: "customers"
~~~

Canonical emission chooses quoting only when required for safe scalar interpretation.

---

# 23. Original key order outside semantic order

Field sequence order is semantic and MUST be preserved.

Mapping property order is not authored semantic state.

The emitter uses its canonical property ordering.

---

# 24. Anchors and aliases are not round-tripped

Anchors and aliases are forbidden at parse time.

Therefore no alias identity is ever part of declarative semantic state.

Canonical emission never produces them.

---

# 25. Schema name boundary

Canonical Schema currently has no name attribute.

Declarative SchemaDefinition does:

~~~text
SchemaDefinition.name
~~~

Therefore declarative schema name is authoring/document identity, not canonical Schema state.

---

# 26. Consequence for single-schema load

This call:

~~~python
schema = load_schema("customers.yml")
~~~

returns only Schema.

The declarative name is not hidden inside the returned object.

---

# 27. Consequence for single-schema export

Export requires explicit identity:

~~~python
text = dumps_schema(
    schema,
    name="customers",
)
~~~

The caller supplies the name because Schema cannot reconstruct it.

---

# 28. Single-schema identity round-trip

To preserve both Schema semantics and declaration identity across a load/use/dump flow, the caller must preserve or re-supply the name.

Conceptually:

~~~text
(name, Schema)
      ↓ export
YAML
      ↓ parse
(name, Schema)
~~~

A bare Schema alone cannot preserve declarative identity.

---

# 29. Multi-schema identity round-trip

Multi-schema helpers preserve declarative identity naturally through mapping keys.

~~~text
Mapping[str, Schema]
      ↓ dumps_schemas
YAML
      ↓ loads_schemas
Mapping[str, Schema]'
~~~

Required:

~~~text
same names
same iteration order
same Schema values
~~~

---

# 30. Multi-schema name source

For multi-schema export:

~~~python
{
    "customers": customer_schema,
    "orders": order_schema,
}
~~~

mapping keys become declarative schema names.

No name is read from Schema itself.

---

# 31. Schema declaration order

SchemaDocument preserves declaration order.

dumps_schemas SHOULD preserve caller Mapping iteration order.

loads_schemas MUST preserve document declaration order in its returned mapping.

This makes generated diffs deterministic without changing Schema semantics.

---

# 32. Canonical declarative emission

PyTransformKit V1 defines a canonical declarative YAML emission policy.

Canonical here means:

~~~text
one deterministic preferred YAML representation
for one SchemaDocument semantic value
~~~

It does NOT mean that YAML becomes the canonical wire format.

---

# 33. Canonical declarative property order

Emission SHOULD use the property order frozen in document 31.

Representative order:

~~~text
version
schema / schemas
name
fields
name
type
nullable
description
~~~

Nested type properties also use deterministic order.

---

# 34. Canonical nullable emission

Although nullable defaults to true while parsing, canonical generated field declarations SHOULD emit nullable explicitly.

Example:

~~~yaml
- name: email
  type: string
  nullable: true
~~~

This favors contract readability.

---

# 35. Canonical type spelling

The emitter MUST use canonical type names.

Examples:

~~~text
integer input alias → int64 output
float input alias   → float64 output
~~~

SQL/backend aliases are never emitted.

---

# 36. Canonical temporal emission

Default temporal state uses short form.

~~~text
TimeType(unit="us")
    → type: time

DurationType(unit="us")
    → type: duration

TimestampType(unit="us", timezone=None)
    → type: timestamp
~~~

Non-default state uses structured form.

---

# 37. Canonical declarative bytes are not wire bytes

Even if dumps_schema is deterministic, its UTF-8 YAML bytes are NOT the canonical Schema wire bytes.

Canonical wire bytes remain:

~~~python
SchemaCodec().to_bytes(schema)
~~~

This distinction is mandatory.

---

# 38. Schema fingerprint authority

Canonical Schema fingerprinting MUST continue to use:

~~~python
SchemaCodec().fingerprint(schema)
~~~

or an explicitly future-frozen Schema semantic fingerprint API.

Declarative YAML bytes MUST NOT become the Schema identity fingerprint source.

---

# 39. Why YAML must not define Schema fingerprint

YAML formatting may legitimately evolve without changing Schema semantics.

Examples:

- quoting improvements;
- line wrapping;
- emitter implementation replacement;
- harmless property formatting changes;
- comments in author input.

Hashing YAML bytes would incorrectly turn formatting into semantic identity.

---

# 40. Fingerprint invariant

Equivalent declarative authoring forms that compile to equal Schema values MUST produce the same canonical SchemaCodec fingerprint.

Conceptually:

~~~text
YAML A ─┐
        ├─→ same Schema → same SchemaCodec fingerprint
YAML B ─┘
~~~

---

# 41. Schema name and fingerprint

Because SchemaDefinition.name is not canonical Schema state:

~~~text
name=customers + Schema X
name=clients   + Schema X
~~~

produce the same SchemaCodec fingerprint for Schema X.

This is intentional.

---

# 42. Declarative document fingerprint

Declarative schema V1 does NOT define a public document fingerprint.

If a future need arises to identify:

~~~text
name + declarative version + schema mapping
~~~

that must receive a separate explicit fingerprint contract.

It MUST NOT overload SchemaCodec fingerprint semantics.

---

# 43. Wire serialization example

A canonical Schema wire document conceptually contains:

~~~json
{
  "contract": "pytransformkit.schema",
  "contract_version": 1,
  "payload": {
    "$type": "pytransformkit.data.schema",
    "fields": {
      "fields": {
        "$tuple": []
      }
    }
  }
}
~~~

The exact typed payload is governed by SchemaCodec and its golden contracts.

---

# 44. Declarative YAML example

The corresponding authoring representation may look like:

~~~yaml
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
~~~

The two representations target the same canonical Schema semantics but serve different audiences.

---

# 45. YAML is optimized for humans

Declarative YAML prioritizes:

- readability;
- concise type syntax;
- Git review;
- hand authoring;
- documentation;
- configuration ergonomics.

It deliberately hides internal semantic type IDs and wire collection markers.

---

# 46. Wire JSON is optimized for software contracts

SchemaCodec prioritizes:

- exact typed reconstruction;
- durable contract IDs;
- explicit contract version;
- deterministic bytes;
- migration support;
- machine-readable type identity;
- canonical fingerprints.

It is not designed as the primary hand-authored schema syntax.

---

# 47. No YAML-to-wire shortcut

The implementation SHOULD NOT translate raw YAML directly into SchemaCodec JSON.

Required path:

~~~text
YAML
 ↓
definitions
 ↓
Schema
 ↓ optional SchemaCodec serialization
wire JSON
~~~

The canonical Domain is the semantic bridge.

---

# 48. No wire-to-YAML shortcut

Similarly, raw SchemaCodec payload dictionaries SHOULD NOT be rewritten mechanically into YAML syntax.

Required path:

~~~text
wire JSON
 ↓ SchemaCodec
Schema
 ↓ declarative exporter
YAML
~~~

This prevents wire implementation details from leaking into authoring syntax.

---

# 49. Cross-representation conversion

Supported conceptual conversions are:

~~~text
YAML → Schema
Schema → YAML
Schema → wire JSON
wire JSON → Schema
YAML → Schema → wire JSON
wire JSON → Schema → YAML
~~~

There is no direct YAML-wire equivalence contract.

---

# 50. YAML to wire semantic invariant

If YAML Y compiles to Schema S:

~~~text
load(Y) = S
~~~

then:

~~~text
SchemaCodec.from_json(
    SchemaCodec.to_json(S)
) == S
~~~

The two round-trips compose through the canonical Domain.

---

# 51. Wire to YAML semantic invariant

If SchemaCodec decodes wire payload W to Schema S, and S is representable by declarative V1, then:

~~~text
W
 ↓ SchemaCodec
S
 ↓ dumps_schema(name=N)
Y
 ↓ loads_schema
S'

S == S'
~~~

---

# 52. Unsupported custom DataType boundary

SchemaCodec and the declarative exporter have separate closed-world policies.

If a canonical/custom DataType is not supported by declarative V1, YAML export MUST fail explicitly with PTK-DECL-012.

It MUST NOT copy arbitrary wire semantic type IDs into YAML.

---

# 53. Declarative language version

The root:

~~~yaml
version: 1
~~~

means:

~~~text
PyTransformKit declarative schema language version 1
~~~

It does NOT mean:

~~~text
SchemaCodec contract_version 1
~~~

even though both happen to be 1 initially.

---

# 54. Wire contract version

SchemaCodec's:

~~~json
"contract_version": 1
~~~

belongs exclusively to:

~~~text
contract = pytransformkit.schema
~~~

The declarative parser MUST NOT use this wire version as its document-version field.

---

# 55. Package version

The installed PyTransformKit package version controls which declarative and wire versions the implementation supports.

It is not embedded automatically as authoring schema semantics.

Declarative documents SHOULD NOT contain:

~~~yaml
pytransformkit_version: 1.1.0
~~~

unless a future specification introduces such a field.

---

# 56. Declarative compatibility

A parser supporting declarative V1 MUST reject future unknown versions.

Example:

~~~yaml
version: 2
~~~

fails until V2 support exists.

Fail-closed behavior prevents accidental interpretation under old semantics.

---

# 57. Wire compatibility

SchemaCodec maintains its own contract-version handling and MigrationRegistry behavior.

Declarative support MUST NOT alter wire migration rules.

---

# 58. Declarative migration boundary

Declarative V1 does NOT require an automatic migration framework.

If declarative V2 is introduced, the project may choose between:

~~~text
V1 parser + V2 parser
or
V1 → V2 authoring migration
~~~

That migration system is separate from SchemaCodec MigrationRegistry.

---

# 59. No shared migration registry by default

The existing wire MigrationRegistry SHOULD NOT be reused automatically for declarative YAML language migrations.

The contracts have different concerns:

~~~text
wire migration        = durable software payload evolution
declarative migration = human authoring language evolution
~~~

---

# 60. Canonical declarative re-emission

A valid non-canonical YAML source MAY be parsed and emitted into canonical declarative V1 form.

Example:

~~~text
author aliases
optional nullable omitted
non-canonical safe quoting
explicit default temporal structure
~~~

may normalize during emission.

---

# 61. Idempotent canonical emission

Canonical declarative emission SHOULD be semantically idempotent.

Required:

~~~text
Y1 = emit(parse(Y))
Y2 = emit(parse(Y1))

semantic(Y1) == semantic(Y2)
~~~

Preferably, under the same package/emitter version:

~~~text
Y1 bytes == Y2 bytes
~~~

---

# 62. Byte-stability scope

Generated YAML SHOULD be byte-stable under the same PyTransformKit version and emitter configuration.

However, byte stability across all future package releases is NOT a V1 compatibility guarantee.

Semantic stability is the stronger requirement.

---

# 63. Golden YAML fixtures

Implementation SHOULD maintain canonical emitted YAML fixtures for representative schemas.

Examples:

~~~text
schema_basic_v1.yml
schema_all_primitive_types_v1.yml
schema_decimal_v1.yml
schema_temporal_v1.yml
schema_nested_v1.yml
schemas_multi_v1.yml
~~~

Golden fixtures validate emitter determinism.

---

# 64. Existing wire golden fixtures remain independent

Existing SchemaCodec golden JSON fixtures MUST remain unchanged unless the wire contract itself changes under its compatibility policy.

Adding YAML fixtures does not replace them.

CI SHOULD maintain both families.

---

# 65. Two conformance suites

The repository SHOULD distinguish:

~~~text
WIRE CONTRACT SUITE
    SchemaCodec JSON
    exact canonical bytes
    contract_version
    wire migrations
    wire fingerprints

DECLARATIVE AUTHORING SUITE
    YAML grammar
    secure parser
    canonical emitter
    semantic Domain round-trip
~~~

---

# 66. Cross-suite bridge tests

Bridge tests SHOULD prove:

~~~text
YAML
 ↓ declarative load
Schema
 ↓ SchemaCodec
canonical wire JSON
 ↓ SchemaCodec
Schema'

Schema == Schema'
~~~

and the reverse:

~~~text
wire JSON
 ↓ SchemaCodec
Schema
 ↓ declarative dump
YAML
 ↓ declarative load
Schema'

Schema == Schema'
~~~

---

# 67. Fingerprint bridge test

For equivalent Schemas obtained through Python authoring, YAML loading or wire decoding:

~~~text
SchemaCodec().fingerprint(schema_python)
==
SchemaCodec().fingerprint(schema_yaml)
==
SchemaCodec().fingerprint(schema_wire)
~~~

when all three Schema values are equal.

---

# 68. Field description round-trip

Top-level Field.description is canonical Domain state and MUST survive YAML round-trip.

Example:

~~~yaml
- name: status
  type: string
  nullable: true
  description: Customer status
~~~

must produce a Field whose description equals the input string.

---

# 69. Nested StructField description boundary

Current canonical StructField has no description field.

Therefore declarative V1 rejects nested struct descriptions.

This prevents false promises of round-trip preservation.

---

# 70. UnknownType round-trip

Intentional UnknownType MUST survive:

~~~text
UnknownType()
 ↓ YAML
type: unknown
 ↓ parse
UnknownType()
~~~

A misspelled type never participates in this round-trip because it fails validation.

---

# 71. Empty Schema round-trip

If canonical Schema accepts an empty field tuple, declarative V1 SHOULD preserve it:

~~~python
Schema(fields=())
~~~

through:

~~~yaml
version: 1
schema:
  name: empty
  fields: []
~~~

---

# 72. Empty StructType round-trip

If canonical StructType accepts fields=(), declarative V1 SHOULD preserve:

~~~yaml
type:
  struct:
    fields: []
~~~

without inventing placeholder fields.

---

# 73. Ordering guarantee

Round-trip MUST preserve:

~~~text
Schema field order
StructType field order
multi-schema declaration/mapping order
~~~

Ordering MUST NOT be alphabetically normalized.

---

# 74. Unicode round-trip

UTF-8 schema names, field names and descriptions MUST preserve Unicode string value.

Emitter escaping differences are not semantic.

Declarative output must reload to the same Python strings.

---

# 75. Scalar ambiguity round-trip

String values resembling YAML scalars MUST preserve string semantics.

Example schema name:

~~~text
2026-10-01
~~~

may require quoting in emitted YAML.

Reloading MUST produce the same string, not a date object.

---

# 76. Timezone string round-trip

Timestamp timezone strings are opaque logical strings in declarative V1.

Example:

~~~text
Europe/Paris
~~~

must be preserved exactly unless canonical Domain itself later defines normalization.

---

# 77. No engine-specific serialization

Neither YAML nor SchemaCodec may depend on physical engine schemas for semantic round-trip.

Round-trip MUST succeed without:

~~~text
pandas
polars
pyarrow
duckdb
~~~

installed.

---

# 78. No hidden runtime state

Declarative export MUST not serialize runtime execution state, engine handles or provider objects.

The feature is scoped to logical Schema values only.

---

# 79. No secret-bearing metadata

Because declarative V1 does not support arbitrary metadata, export MUST not introduce credentials, environment values or secret references.

This keeps authoring output safe for normal source-control use subject to user-provided names/descriptions.

---

# 80. Diff ergonomics

Canonical YAML SHOULD favor stable Git diffs through:

- deterministic property order;
- preserved field order;
- stable indentation;
- explicit nullable values;
- canonical type names;
- one final newline.

Diff ergonomics are an authoring concern, not wire semantics.

---

# 81. Declarative canonicalization service

A future helper MAY provide:

~~~python
canonicalize_schema_yaml(text: str) -> str
~~~

implemented conceptually as:

~~~text
parse
 ↓
validate
 ↓
emit
~~~

Such a helper would canonicalize authoring syntax without involving SchemaCodec bytes.

---

# 82. Canonicalization and names

SchemaDocument-level parse/emit can preserve declarative names because the definition model retains them.

This differs from:

~~~text
load_schema → bare Schema
~~~

where authoring name is intentionally discarded.

---

# 83. No automatic YAML persistence inside Schema

Schema MUST NOT retain:

- source YAML text;
- comments;
- source path;
- declaration name;
- emitter formatting;
- parser nodes.

Those values are not canonical Schema semantics.

---

# 84. No automatic wire persistence inside Schema

Schema also does not retain its SchemaCodec JSON bytes.

Wire and YAML representations are generated from the Domain when required.

This keeps Schema representation-neutral.

---

# 85. Serialization architecture

The complete model is:

~~~text
                YAML
                 │
                 ▼
          declarative adapter
                 │
                 ▼
              Schema
             /      \
            /        \
           ▼          ▼
   SchemaCodec      engines
       JSON        adapters
~~~

Schema is the semantic center.

---

# 86. Compatibility matrix

| Concern | Version/authority |
| --- | --- |
| Python package | pytransformkit package version |
| Declarative YAML grammar | declarative version |
| Canonical Schema wire JSON | SchemaCodec contract_version |
| Schema semantic value | Domain classes |
| YAML formatting | emitter policy |
| Schema fingerprint | SchemaCodec canonical bytes |

---

# 87. Change classification — formatting only

Changing YAML indentation or safe quoting without changing parse semantics MAY be a patch-level emitter change.

It MUST still preserve deterministic output and semantic reload.

Such a change does not require a SchemaCodec contract change.

---

# 88. Change classification — declarative syntax

Adding/removing accepted properties or changing declarative meaning requires declarative-language compatibility analysis.

It may require declarative version 2.

It does not automatically require SchemaCodec version 2.

---

# 89. Change classification — Domain semantics

Changing canonical Schema/DataType semantics requires broader Domain compatibility analysis.

Such a change may affect:

- Python API;
- declarative mapping;
- SchemaCodec mapping;
- engine adapters;
- fingerprints.

It cannot be hidden as a YAML-only change.

---

# 90. Change classification — wire format

Changing SchemaCodec wire envelope or semantic payload compatibility follows the existing wire contract/version/migration policy.

It does not automatically require declarative grammar changes.

---

# 91. Declarative export failure policy

If a future canonical Domain value cannot be represented by declarative V1, export MUST fail with:

~~~text
DeclarativeSchemaExportError
PTK-DECL-012
~~~

The exporter MUST NOT silently omit the unsupported state.

---

# 92. Wire decoding failure remains wire error

If SchemaCodec fails to decode invalid wire JSON, existing serialization errors remain authoritative.

The failure MUST NOT be reclassified as a declarative YAML error unless the caller explicitly passes through a declarative conversion API after successful wire decoding.

---

# 93. Declarative parsing failure remains declarative error

Malformed YAML raises PTK-DECL-* errors.

It MUST NOT be wrapped as InvalidWirePayloadError because YAML authoring is not the wire contract.

---

# 94. Golden compatibility policy

Wire golden fixtures protect exact canonical JSON bytes.

Declarative golden fixtures protect the currently chosen canonical generated YAML.

However:

~~~text
wire golden compatibility = durable software contract
declarative golden compatibility = authoring output contract
~~~

Their release policies may differ.

---

# 95. Required round-trip test matrix

Tests MUST cover:

~~~text
primitive types
signed integers
unsigned integers
floats
decimal
date/time/timestamp/duration
binary
unknown
list
struct
map
deep nested combinations
nullable true/false
field descriptions
empty schema if Domain-valid
empty struct if Domain-valid
Unicode names/descriptions
multi-schema names/order
~~~

---

# 96. Authoring normalization tests

Tests SHOULD prove normalization such as:

~~~text
integer → int64
float → float64
explicit default timestamp → timestamp short form
omitted nullable → explicit canonical nullable
safe unquoted/quoted strings → canonical safe quoting
~~~

---

# 97. Wire bridge tests

Tests MUST verify that a Schema loaded from YAML can pass unchanged through SchemaCodec round-trip.

Likewise, a Schema decoded from SchemaCodec must survive declarative round-trip when its DataTypes are declarative-V1 representable.

---

# 98. Fingerprint tests

Tests MUST verify that equivalent Schema values originating from:

~~~text
direct Python construction
declarative YAML
SchemaCodec JSON
~~~

produce equal SchemaCodec fingerprints.

---

# 99. Name independence test

Tests SHOULD verify:

~~~text
dumps_schema(schema, name="customers")
dumps_schema(schema, name="clients")
~~~

produce different declarative documents but:

~~~text
SchemaCodec().fingerprint(schema)
~~~

remains unchanged.

---

# 100. Comment-loss test

A test MAY document that input comments are not preserved.

This should be treated as expected behavior, not a regression.

---

# 101. Deterministic emitter test

Repeated export of the same SchemaDocument under the same implementation version MUST produce identical output.

~~~text
emit(document) == emit(document)
~~~

including final newline policy.

---

# 102. Parser/emitter closure test

Every canonical YAML fixture emitted by PyTransformKit MUST be accepted by the hardened parser.

~~~text
emit
 ↓
parse
 ↓
validate
 ↓
success
~~~

---

# 103. Security closure

Canonical emission MUST never generate YAML constructs that the hardened parser rejects.

Therefore the emitter cannot generate:

~~~text
anchors
aliases
custom tags
merge keys
multi-document streams
ambiguous unsafe scalars
~~~

---

# 104. Decisions frozen by this document

## DEC-RT-01

Declarative YAML is an authoring format, not the canonical wire format.

## DEC-RT-02

Schema remains the semantic authority between YAML and wire JSON.

## DEC-RT-03

SchemaCodec remains pytransformkit.schema contract_version 1 unless the wire contract independently changes.

## DEC-RT-04

Declarative version and wire contract_version are independent namespaces.

## DEC-RT-05

Round-trip guarantees semantic equality, not textual YAML equality.

## DEC-RT-06

All canonical Schema/Field/DataType state representable by V1 must round-trip losslessly.

## DEC-RT-07

Comments, formatting, quoting style and author aliases are not preserved.

## DEC-RT-08

SchemaDefinition.name is declarative identity and is not injected into Schema.

## DEC-RT-09

Single-schema export requires an explicit name.

## DEC-RT-10

Multi-schema mapping keys preserve declarative names.

## DEC-RT-11

SchemaCodec fingerprint remains the canonical Schema fingerprint authority.

## DEC-RT-12

YAML bytes are not used as Schema semantic fingerprint input.

## DEC-RT-13

Declarative V1 defines no public document fingerprint.

## DEC-RT-14

Wire MigrationRegistry is not reused automatically for declarative-language migrations.

## DEC-RT-15

Canonical emitted YAML must be accepted by the same hardened parser.

---

# 105. Acceptance criteria

The round-trip/serialization model is satisfied when:

1. Schema → YAML → Schema preserves Schema equality;
2. every supported DataType round-trips recursively;
3. Field description and nullability are preserved;
4. Schema and StructField ordering are preserved;
5. author aliases normalize canonically;
6. comments and formatting are explicitly non-semantic;
7. single-schema naming remains explicit outside Schema;
8. multi-schema names/order round-trip through mappings;
9. SchemaCodec wire contract remains unchanged;
10. declarative and wire versions remain independent;
11. YAML bytes do not define Schema fingerprint;
12. equivalent Schema values have equal SchemaCodec fingerprints regardless of source representation;
13. YAML → Schema → wire JSON works without direct YAML-wire coupling;
14. wire JSON → Schema → YAML works for V1-representable schemas;
15. unrepresentable Domain state fails export rather than degrading;
16. canonical YAML emission is deterministic under one implementation version;
17. canonical emitted YAML passes hardened parsing;
18. existing wire golden fixtures remain independently qualified.

---

# 106. Next document

The next document freezes the public user-facing API surface:

~~~text
38_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_PUBLIC_API_SPEC.md
~~~

It must decide:

~~~text
public namespace
load_schema
loads_schema
load_schemas
loads_schemas
dump_schema
dumps_schema
dump_schemas
dumps_schemas
public errors
optional dependency behavior
advanced configuration exposure
root-export policy
typing signatures
stability classification
~~~

---

# 107. Final summary

PyTransformKit now has two deliberate representations around one canonical Schema Domain:

~~~text
             HUMAN AUTHORING
                  YAML
                   │
                   ▼
                Schema
               /      \
              /        \
             ▼          ▼
    CANONICAL WIRE     ENGINES
    SchemaCodec JSON   adapters
~~~

YAML optimizes for humans.

SchemaCodec JSON optimizes for durable software contracts.

Schema remains the semantic center.

> **One Schema semantics, one canonical wire contract, and one separate declarative authoring language.**