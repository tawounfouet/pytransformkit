# 31 — PyTransformKit Declarative Schema — Specification

> **Document status:** DRAFT NORMATIVE SPECIFICATION  
> **Depends on:** 28_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_EXPRESSION_DU_BESOIN.md  
> **Depends on:** 29_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_REQUIREMENTS_ANALYSIS.md  
> **Depends on:** 30_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ARCHITECTURE.md  
> **Declarative language version:** 1  
> **Primary format:** YAML  
> **Canonical Domain target:** Schema / Field / DataType

---

# 1. Purpose

This document defines the normative authoring grammar for PyTransformKit declarative schemas.

It specifies:

- document root structure;
- document versioning;
- single-schema form;
- multi-schema form;
- schema identifiers;
- field declarations;
- nullability;
- descriptions;
- logical type declarations;
- parameterized types;
- nested types;
- strictness rules;
- unknown-property behavior;
- duplicate handling;
- canonical emission shape;
- unsupported YAML features.

This document defines the syntax accepted by declarative schema version 1.

It does not define implementation classes or parser internals.

---

# 2. Design principle

The declarative format is an authoring language for canonical PyTransformKit schema semantics.

The invariant is:

~~~text
Declarative YAML
      ↓
SchemaDefinition
      ↓
SchemaDefinitionCompiler
      ↓
Schema
~~~

The YAML document is not itself the runtime schema.

---

# 3. Normative language

The keywords MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are normative.

Any example explicitly labeled invalid MUST be rejected.

Any example explicitly labeled canonical defines the preferred emitted form.

---

# 4. File extensions and encoding

The recommended file extensions are:

~~~text
.yaml
.yml
~~~

Both MAY be supported.

Documents MUST be UTF-8.

A UTF-8 BOM MAY be accepted but SHOULD NOT be emitted.

---

# 5. Root document shape

The root value MUST be a YAML mapping.

Valid:

~~~yaml
version: 1
schema:
  name: customers
  fields: []
~~~

Invalid:

~~~yaml
- version: 1
- schema: customers
~~~

Invalid:

~~~yaml
customers
~~~

---

# 6. Root properties

Version 1 supports exactly:

~~~text
version
schema
schemas
~~~

Rules:

1. version is REQUIRED;
2. exactly one of schema or schemas MUST be present;
3. schema and schemas MUST NOT appear together;
4. any other root property MUST be rejected.

---

# 7. Document version

The version declaration is:

~~~yaml
version: 1
~~~

Requirements:

- the value MUST be an integer;
- the value MUST equal 1 for this specification;
- string values such as "1" MUST be rejected;
- unsupported versions MUST fail explicitly.

Invalid:

~~~yaml
version: "1"
~~~

Invalid:

~~~yaml
version: 2
~~~

---

# 8. Single-schema form

Canonical form:

~~~yaml
version: 1

schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
~~~

The schema property MUST contain a schema-definition mapping.

In single-schema form, name is REQUIRED.

---

# 9. Multi-schema form

Canonical form:

~~~yaml
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
~~~

In multi-schema form:

- each mapping key is the schema name;
- the nested body MUST NOT repeat name;
- duplicate schema keys MUST fail;
- order SHOULD be preserved by the definition layer.

Invalid:

~~~yaml
schemas:
  customers:
    name: customers
    fields: []
~~~

---

# 10. Normalized internal meaning

Both authoring forms normalize conceptually to:

~~~text
SchemaDocument
├── version = 1
└── schemas
    ├── SchemaDefinition(...)
    └── SchemaDefinition(...)
~~~

Single-schema syntax is only authoring sugar.

It does not create a separate semantic model.

---

# 11. Schema-definition properties

Declarative schema V1 permits only:

~~~text
name      single-schema form only
fields
~~~

The following are not part of V1:

~~~text
description
metadata
owner
tags
tests
constraints
source
target
~~~

This reflects the actual canonical Domain, where Schema currently stores only ordered fields.

---

# 12. Schema names

A schema name MUST:

- be a YAML string;
- contain at least one non-whitespace character;
- preserve case exactly;
- remain deterministic under UTF-8 representation.

The language does not impose SQL identifier rules.

Examples that MAY be valid:

~~~text
customers
Customer360
customer-orders
sales_eu
~~~

Blank names MUST fail.

---

# 13. Fields property

Every schema definition MUST contain fields.

The value MUST be a YAML sequence.

Canonical empty schema:

~~~yaml
fields: []
~~~

The declarative language follows the canonical Domain on whether an empty Schema is semantically acceptable.

---

# 14. Field declaration

Each field MUST be a mapping.

Canonical:

~~~yaml
- name: customer_id
  type: int64
  nullable: false
~~~

Invalid:

~~~yaml
- customer_id
~~~

---

# 15. Field properties

A field supports exactly:

~~~text
name
type
nullable
description
~~~

Unknown field properties MUST be rejected.

Invalid:

~~~yaml
- name: customer_id
  type: int64
  nulable: false
~~~

---

# 16. Field name

name is REQUIRED.

It MUST be a non-empty string.

Valid:

~~~yaml
name: customer_id
~~~

Invalid:

~~~yaml
name: ""
~~~

Invalid:

~~~yaml
name: 123
~~~

---

# 17. Field nullability

nullable is OPTIONAL.

Its semantic default is true.

Therefore:

~~~yaml
- name: email
  type: string
~~~

is semantically equivalent to:

~~~yaml
- name: email
  type: string
  nullable: true
~~~

The value MUST be a YAML boolean.

Invalid:

~~~yaml
nullable: "false"
~~~

Invalid:

~~~yaml
nullable: 0
~~~

The canonical emitter SHOULD emit nullable explicitly for field readability.

---

# 18. Field description

description is OPTIONAL.

When present, it MUST be a non-empty string.

Canonical:

~~~yaml
description: Stable customer identifier
~~~

It maps directly to Field.description.

Explicit YAML null SHOULD be rejected.

Preferred absence representation:

~~~yaml
- name: email
  type: string
  nullable: true
~~~

not:

~~~yaml
description: null
~~~

---

# 19. Field order

Field order is significant.

The YAML sequence order MUST be preserved in Schema.fields.

The exporter MUST preserve Domain field order.

---

# 20. Duplicate field names

Field names MUST be unique within one schema.

Invalid:

~~~yaml
fields:
  - name: customer_id
    type: int64

  - name: customer_id
    type: string
~~~

Duplicates MUST fail before runtime execution.

---

# 21. Type syntax overview

A field type uses one of two forms.

Short scalar form:

~~~yaml
type: string
~~~

Structured long form:

~~~yaml
type:
  decimal:
    precision: 18
    scale: 2
~~~

Short form is preferred when the logical type has no non-default parameters.

Structured form is required for parameterized and nested types.

---

# 22. Canonical primitive type names

Declarative schema V1 defines these canonical primitive names:

~~~text
string
boolean
int8
int16
int32
int64
uint8
uint16
uint32
uint64
float32
float64
binary
date
time
timestamp
duration
unknown
~~~

The exact Domain mapping is frozen in document 32.

---

# 23. Integer types

Canonical signed integer forms:

~~~yaml
type: int8
type: int16
type: int32
type: int64
~~~

Canonical unsigned forms:

~~~yaml
type: uint8
type: uint16
type: uint32
type: uint64
~~~

The authoring alias:

~~~yaml
type: integer
~~~

MAY be accepted as equivalent to int64.

If accepted, canonical export MUST emit:

~~~yaml
type: int64
~~~

---

# 24. Float types

Canonical forms:

~~~yaml
type: float32
~~~

~~~yaml
type: float64
~~~

The alias:

~~~yaml
type: float
~~~

MAY be accepted as float64.

Canonical export MUST emit float64.

---

# 25. String type

Canonical:

~~~yaml
type: string
~~~

Declarative V1 defines no logical length, collation or encoding parameters for StringType.

---

# 26. Boolean type

Canonical:

~~~yaml
type: boolean
~~~

The alias bool SHOULD NOT be accepted in V1.

---

# 27. Binary type

Canonical:

~~~yaml
type: binary
~~~

No binary-length parameter exists in V1.

---

# 28. Decimal type

Decimal MUST use structured form.

Canonical:

~~~yaml
type:
  decimal:
    precision: 18
    scale: 2
~~~

Required properties:

~~~text
precision
scale
~~~

No other property is allowed.

Both values MUST be integers.

Constraints:

~~~text
precision > 0
scale >= 0
scale <= precision
~~~

---

# 29. Date type

Canonical:

~~~yaml
type: date
~~~

No structured parameters are defined.

---

# 30. Time type

Short form:

~~~yaml
type: time
~~~

means:

~~~text
unit = us
~~~

Structured form:

~~~yaml
type:
  time:
    unit: ms
~~~

Allowed units:

~~~text
s
ms
us
ns
~~~

No other property is allowed.

---

# 31. Timestamp type

Short form:

~~~yaml
type: timestamp
~~~

means:

~~~text
unit = us
timezone = absent
~~~

Structured form:

~~~yaml
type:
  timestamp:
    unit: us
    timezone: UTC
~~~

Allowed properties:

~~~text
unit
timezone
~~~

unit MUST be one of:

~~~text
s
ms
us
ns
~~~

timezone MUST be a non-empty string when present.

Omission means no timezone.

---

# 32. Duration type

Short form:

~~~yaml
type: duration
~~~

means unit = us.

Structured form:

~~~yaml
type:
  duration:
    unit: ns
~~~

Allowed units:

~~~text
s
ms
us
ns
~~~

---

# 33. Unknown type

Intentional unknown type is explicit:

~~~yaml
type: unknown
~~~

This maps to the canonical UnknownType.

A misspelled type MUST NOT map to unknown.

Invalid:

~~~yaml
type: unknowm
~~~

---

# 34. List type

List MUST use structured form.

Canonical:

~~~yaml
type:
  list:
    element:
      type: string
    element_nullable: true
~~~

Allowed properties:

~~~text
element
element_nullable
~~~

element is REQUIRED.

element_nullable is OPTIONAL and defaults to true.

---

# 35. List element holder

element is a type holder.

Canonical:

~~~yaml
element:
  type: int64
~~~

Nested list:

~~~yaml
element:
  type:
    list:
      element:
        type: string
      element_nullable: true
~~~

A list element has no field name.

---

# 36. Struct type

Struct MUST use structured form.

Canonical:

~~~yaml
type:
  struct:
    fields:
      - name: city
        type: string
        nullable: true

      - name: country
        type: string
        nullable: true
~~~

The struct body supports exactly:

~~~text
fields
~~~

---

# 37. Struct fields

StructField in the current Domain exposes:

~~~text
name
data_type
nullable
~~~

Therefore declarative struct fields support exactly:

~~~text
name
type
nullable
~~~

description MUST NOT be accepted for nested struct fields in V1 because canonical StructField cannot preserve it.

---

# 38. Struct field nullability

nullable defaults to true.

It maps directly to StructField.nullable.

Canonical emitter SHOULD emit it explicitly.

---

# 39. Struct field uniqueness

Struct field names MUST be unique within their containing struct.

Duplicate checks are recursive.

---

# 40. Map type

Map MUST use structured form.

Canonical:

~~~yaml
type:
  map:
    key:
      type: string
    value:
      type: int64
    value_nullable: true
~~~

Allowed properties:

~~~text
key
value
value_nullable
~~~

key is REQUIRED.

value is REQUIRED.

value_nullable is OPTIONAL and defaults to true.

---

# 41. Map key

key is a type holder:

~~~yaml
key:
  type: string
~~~

The declarative grammar MUST NOT impose engine-specific key restrictions.

Canonical Domain rules remain authoritative.

---

# 42. Map value

value is a type holder.

Example:

~~~yaml
value:
  type:
    decimal:
      precision: 18
      scale: 2
~~~

Nested values are recursively supported.

---

# 43. Type holder

A type holder is a mapping containing exactly:

~~~text
type
~~~

unless its surrounding grammar explicitly defines additional properties.

Example:

~~~yaml
element:
  type: string
~~~

A type holder is not a field and therefore does not own name, nullable or description.

---

# 44. Recursive nesting

Type declarations are recursive.

Valid example:

~~~yaml
type:
  list:
    element:
      type:
        struct:
          fields:
            - name: sku
              type: string
              nullable: false

            - name: quantity
              type: int64
              nullable: false
    element_nullable: false
~~~

Compilation MUST recursively produce canonical nested DataType objects.

---

# 45. Nested map/list/struct example

Valid:

~~~yaml
type:
  map:
    key:
      type: string
    value:
      type:
        list:
          element:
            type:
              struct:
                fields:
                  - name: code
                    type: string
                    nullable: false
                  - name: score
                    type: float64
                    nullable: true
          element_nullable: false
    value_nullable: true
~~~

The grammar does not special-case nesting combinations.

---

# 46. Structured type discriminator

A structured type mapping MUST contain exactly one type discriminator.

Valid:

~~~yaml
type:
  decimal:
    precision: 18
    scale: 2
~~~

Invalid:

~~~yaml
type:
  decimal:
    precision: 18
    scale: 2
  string: {}
~~~

---

# 47. Unknown structured type

Invalid:

~~~yaml
type:
  varchar:
    length: 255
~~~

Unknown type discriminators MUST fail.

They MUST NOT trigger plugin discovery or dynamic imports.

---

# 48. Unknown properties

Unknown properties MUST fail at every grammar level.

Invalid:

~~~yaml
type:
  decimal:
    precision: 18
    scale: 2
    rounding: half_even
~~~

rounding is not part of decimal V1 grammar.

---

# 49. Strict scalar typing

No string-to-boolean coercion:

~~~yaml
nullable: "false"
~~~

is invalid.

No string-to-integer coercion:

~~~yaml
precision: "18"
~~~

is invalid.

No integer-to-string coercion:

~~~yaml
name: 123
~~~

is invalid.

---

# 50. Explicit null

Explicit YAML null is not used as a generic missing-value marker in V1.

Invalid:

~~~yaml
description: null
~~~

Invalid:

~~~yaml
timezone: null
~~~

Properties with no value SHOULD be omitted.

---

# 51. Duplicate YAML keys

Duplicate mapping keys MUST be rejected before semantic decoding.

Invalid:

~~~yaml
nullable: true
nullable: false
~~~

Invalid:

~~~yaml
type:
  decimal:
    precision: 18
    precision: 20
    scale: 2
~~~

Last-value-wins parsing is prohibited.

---

# 52. YAML anchors and aliases

Anchors and aliases are unsupported in declarative schema V1.

Invalid:

~~~yaml
base: &base
  type: string

schema:
  name: customers
  fields:
    - name: email
      <<: *base
~~~

The parser MUST reject them.

---

# 53. YAML merge keys

Merge keys are unsupported.

Invalid:

~~~yaml
<<: *base
~~~

They MUST fail explicitly.

---

# 54. Custom YAML tags

Custom tags are unsupported.

Invalid:

~~~yaml
type: !CustomType {}
~~~

Invalid:

~~~yaml
type: !!python/object:some.module.Type {}
~~~

The parser MUST NOT instantiate Python objects from tags.

---

# 55. Multi-document YAML

YAML streams containing multiple documents are unsupported in V1.

Invalid:

~~~yaml
version: 1
schema:
  name: customers
  fields: []
---
version: 1
schema:
  name: orders
  fields: []
~~~

Multiple schemas belong under schemas in one logical document.

---

# 56. Includes

No include mechanism exists in V1.

Invalid:

~~~yaml
include: common.yml
~~~

Invalid:

~~~yaml
schema:
  include: customer_fields.yml
~~~

---

# 57. Inheritance

Schema inheritance is unsupported.

Invalid:

~~~yaml
schema:
  name: premium_customers
  extends: customers
~~~

---

# 58. Cross-schema references

Cross-schema type references are unsupported.

Invalid:

~~~yaml
type:
  ref: address
~~~

Nested structures MUST be declared explicitly in V1.

---

# 59. Environment interpolation

Implicit environment-variable interpolation is unsupported.

Invalid:

~~~yaml
type: ${FIELD_TYPE}
~~~

The declaration language does not read process environment variables.

---

# 60. Templating

Jinja-style templating is unsupported.

Invalid:

~~~yaml
type: "{{ some_variable }}"
~~~

No expression engine runs before YAML compilation.

---

# 61. Python expressions

Executable Python syntax is unsupported.

Invalid:

~~~yaml
type: "IntegerType(bits=64)"
~~~

Invalid:

~~~yaml
nullable: "1 == 1"
~~~

The declarative grammar expresses data, not executable source.

---

# 62. Quality rules

General data-quality tests are outside V1.

Invalid:

~~~yaml
tests:
  - unique
  - not_null
~~~

nullable remains schema semantics.

Quality rules require a separate specification.

---

# 63. Governance metadata

Arbitrary metadata is outside V1.

Invalid:

~~~yaml
metadata:
  classification: pii
~~~

Invalid:

~~~yaml
owner: data-platform
~~~

This prevents values from being accepted and then silently lost because current canonical Schema and Field do not preserve them.

---

# 64. Schema-level descriptions

Schema descriptions are unsupported in V1.

Invalid:

~~~yaml
schema:
  name: customers
  description: Customer master dataset
  fields: []
~~~

Field descriptions remain supported.

---

# 65. Canonical single-schema example

~~~yaml
version: 1

schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
      description: Stable customer identifier

    - name: email
      type: string
      nullable: true

    - name: account_balance
      type:
        decimal:
          precision: 18
          scale: 2
      nullable: true

    - name: created_at
      type:
        timestamp:
          unit: us
          timezone: UTC
      nullable: false
~~~

---

# 66. Canonical multi-schema example

~~~yaml
version: 1

schemas:
  customers:
    fields:
      - name: customer_id
        type: int64
        nullable: false

      - name: email
        type: string
        nullable: true

  orders:
    fields:
      - name: order_id
        type: int64
        nullable: false

      - name: customer_id
        type: int64
        nullable: false

      - name: amount
        type:
          decimal:
            precision: 18
            scale: 2
        nullable: false
~~~

---

# 67. Canonical nested example

~~~yaml
version: 1

schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false

    - name: addresses
      type:
        list:
          element:
            type:
              struct:
                fields:
                  - name: city
                    type: string
                    nullable: true

                  - name: country
                    type: string
                    nullable: true
          element_nullable: false
      nullable: true
~~~

---

# 68. Canonical map example

~~~yaml
version: 1

schema:
  name: metrics
  fields:
    - name: counters
      type:
        map:
          key:
            type: string
          value:
            type: int64
          value_nullable: false
      nullable: true
~~~

---

# 69. Canonical temporal example

~~~yaml
version: 1

schema:
  name: events
  fields:
    - name: event_date
      type: date
      nullable: false

    - name: event_time
      type:
        time:
          unit: us
      nullable: false

    - name: event_timestamp
      type:
        timestamp:
          unit: us
          timezone: UTC
      nullable: false

    - name: elapsed
      type:
        duration:
          unit: ms
      nullable: true
~~~

---

# 70. Canonical short forms

The emitter SHOULD use scalar short form when all parameters equal Domain defaults.

Preferred:

~~~yaml
type: string
type: boolean
type: int64
type: float64
type: binary
type: date
type: time
type: timestamp
type: duration
type: unknown
~~~

---

# 71. Canonical structured forms

The emitter MUST use structured form when a non-default parameter must be represented.

Examples:

~~~yaml
type:
  timestamp:
    unit: ns
    timezone: UTC
~~~

~~~yaml
type:
  time:
    unit: ms
~~~

~~~yaml
type:
  duration:
    unit: s
~~~

---

# 72. Canonical emitter policy

Declarative V1 SHOULD emit:

~~~text
version               always
schema name            always in single-schema form
fields                 always
field name             always
field type             always
field nullable         always
field description      when present
nested nullable flags  always
default type params    omitted via canonical short form
~~~

This intentionally favors explicit data-contract readability.

---

# 73. Property ordering

Canonical property ordering SHOULD be stable.

Root:

~~~text
version
schema | schemas
~~~

Single schema:

~~~text
name
fields
~~~

Field:

~~~text
name
type
nullable
description
~~~

Decimal:

~~~text
precision
scale
~~~

Timestamp:

~~~text
unit
timezone
~~~

List:

~~~text
element
element_nullable
~~~

Map:

~~~text
key
value
value_nullable
~~~

Stable ordering improves Git diffs.

---

# 74. Comments

Comments MAY appear in source YAML.

Example:

~~~yaml
# Stable business identifier
- name: customer_id
  type: int64
  nullable: false
~~~

Comments are not semantic.

Round-trip does not preserve them.

---

# 75. Quoting

Strings MAY be quoted where valid YAML permits.

The canonical emitter SHOULD quote strings when needed to prevent scalar ambiguity.

Exact logical string values MUST be preserved.

---

# 76. Case sensitivity

Property names are case-sensitive.

Invalid:

~~~yaml
Nullable: false
~~~

Type names are case-sensitive.

Canonical type names are lowercase.

---

# 77. Whitespace and indentation

Whitespace is not semantic beyond YAML syntax.

Canonical emission SHOULD use stable formatting.

Two-space indentation is RECOMMENDED.

---

# 78. YAML scalar ambiguity

Parser configuration MUST avoid unintended implicit typing for values such as:

~~~text
yes
no
on
off
2026-10-01
00123
~~~

A schema name or description that lexically resembles another YAML scalar type MUST remain a string when the grammar requires a string.

The exact loader strategy is defined in document 36.

---

# 79. Semantic equivalence

Two declarative inputs are semantically equivalent if they compile to equivalent canonical Schema objects.

Textual equality is not required.

If integer is accepted as an alias of int64:

~~~yaml
type: integer
~~~

and:

~~~yaml
type: int64
~~~

are semantically equivalent.

Canonical export still emits int64.

---

# 80. Diagnostic object paths

Errors SHOULD expose deterministic object paths.

Single-schema example:

~~~text
schema.fields[2].type.decimal.precision
~~~

Multi-schema example:

~~~text
schemas.customers.fields[2].type.decimal.precision
~~~

---

# 81. Source locations

When available, diagnostics SHOULD combine source and object path.

Example:

~~~text
schemas/customers.yml:14:11
schema.fields[2].type.decimal.precision
~~~

Source location is diagnostic context, not schema semantics.

---

# 82. Representative validation messages

Unknown field property:

~~~text
Unknown property 'nulable' at schema.fields[0].
Expected one of: name, type, nullable, description.
~~~

Unknown type:

~~~text
Unknown declarative type 'intger' at schema.fields[0].type.
~~~

Invalid decimal:

~~~text
Invalid decimal type at schema.fields[2].type.decimal:
scale must not exceed precision.
~~~

Duplicate field:

~~~text
Duplicate field name 'customer_id' at schema.fields[3].
~~~

---

# 83. Grammar summary

~~~text
Document
  := version + exactly one of (schema | schemas)

SingleSchema
  := name + fields

MultiSchemas
  := mapping[name -> SchemaBody]

SchemaBody
  := fields

Field
  := name + type + nullable? + description?

StructField
  := name + type + nullable?

Type
  := PrimitiveScalar
   | Decimal
   | Time
   | Timestamp
   | Duration
   | List
   | Struct
   | Map
~~~

---

# 84. Type grammar summary

~~~text
PrimitiveScalar
  := string
   | boolean
   | int8 | int16 | int32 | int64
   | uint8 | uint16 | uint32 | uint64
   | float32 | float64
   | binary
   | date
   | time
   | timestamp
   | duration
   | unknown

Decimal
  := decimal(precision, scale)

Time
  := time(unit?)

Timestamp
  := timestamp(unit?, timezone?)

Duration
  := duration(unit?)

List
  := list(element, element_nullable?)

Struct
  := struct(fields)

Map
  := map(key, value, value_nullable?)
~~~

---

# 85. Unsupported V1 features

Declarative schema V1 explicitly excludes:

~~~text
schema-level descriptions
arbitrary metadata
governance annotations
quality tests
constraints DSL
templating
Jinja
environment interpolation
includes
inheritance
cross-schema references
custom YAML tags
anchors
aliases
merge keys
multi-document YAML
remote loading semantics
engine-native dtypes
arbitrary Python type imports
expressions
runtime configuration
dataset source/target configuration
workflow configuration
~~~

---

# 86. Strict extension policy

Unknown properties are rejected.

Therefore new V1 grammar properties cannot simply appear without compatibility consideration.

Material grammar extensions SHOULD require:

- a new declarative language version; or
- an explicitly documented compatible extension rule.

V1 is closed by default.

---

# 87. Forward compatibility

A V1 parser MUST reject:

~~~yaml
version: 2
~~~

It MUST NOT perform best-effort future-version parsing.

Fail-closed behavior is part of the contract.

---

# 88. Backwards compatibility

A future PyTransformKit package that supports declarative language V2 SHOULD continue to support V1 according to release compatibility policy.

These versions remain independent:

~~~text
PyTransformKit package version
Declarative schema language version
Canonical wire contract version
~~~

---

# 89. Canonical export target

The V1 exporter MUST emit only V1-valid documents.

It MUST NOT emit unsupported properties.

It MUST NOT claim round-trip support for values absent from the canonical Domain.

---

# 90. Parser/exporter invariant

Every canonical document emitted by the V1 exporter MUST be accepted by the V1 parser.

The required property is:

~~~text
Schema
  ↓ export_v1
YAML
  ↓ parse_v1
SchemaDefinition
  ↓ compile
Schema'

semantic(Schema) == semantic(Schema')
~~~

---

# 91. Security assumptions

This grammar assumes parser enforcement of:

- safe scalar/container construction only;
- duplicate-key rejection;
- no custom tags;
- no anchors or aliases;
- no merge keys;
- no arbitrary object construction;
- controlled scalar resolution;
- bounded resource usage.

Document 36 freezes the concrete parser policy.

---

# 92. Conformance fixtures

The implementation SHOULD provide fixtures for at least:

~~~text
basic_schema.yml
multi_schema.yml
decimal_schema.yml
temporal_schema.yml
list_schema.yml
struct_schema.yml
map_schema.yml
deep_nested_schema.yml

invalid_version.yml
unknown_type.yml
unknown_property.yml
duplicate_field.yml
duplicate_key.yml
invalid_decimal.yml
invalid_boolean.yml
unsafe_tag.yml
anchor_alias.yml
multi_document.yml
~~~

---

# 93. Specification acceptance criteria

The grammar is correctly implemented when:

1. root structure is strictly validated;
2. version 1 is mandatory;
3. exactly one of schema or schemas exists;
4. single-schema name is mandatory;
5. multi-schema identity comes from mapping keys;
6. field order is preserved;
7. field names are unique;
8. field descriptions map to canonical Field.description;
9. nullability maps exactly to canonical semantics;
10. every canonical DataType has a representable declarative form;
11. parameterized types validate their parameters;
12. nested types compile recursively;
13. unknown properties fail;
14. unknown types fail;
15. duplicate YAML keys fail;
16. unsupported YAML features fail;
17. canonical export is deterministic;
18. canonical output re-loads;
19. semantic round-trip preserves all canonical Schema state.

---

# 94. Normative V1 example

~~~yaml
version: 1

schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
      description: Stable customer identifier

    - name: email
      type: string
      nullable: true

    - name: balance
      type:
        decimal:
          precision: 18
          scale: 2
      nullable: true

    - name: preferences
      type:
        map:
          key:
            type: string
          value:
            type: string
          value_nullable: true
      nullable: true

    - name: addresses
      type:
        list:
          element:
            type:
              struct:
                fields:
                  - name: city
                    type: string
                    nullable: true
                  - name: country
                    type: string
                    nullable: true
          element_nullable: false
      nullable: true
~~~

---

# 95. Next document

The next specification freezes the exhaustive correspondence between declarative type syntax and the existing Domain classes:

~~~text
32_PYTRANSFORMKIT_DECLARATIVE_TYPE_SYSTEM_MAPPING.md
~~~

It must map:

~~~text
YAML type declaration
        ↓
TypeDefinition
        ↓
DataType constructor
        ↓
canonical YAML emission
~~~

for:

~~~text
StringType
BooleanType
IntegerType
FloatType
DecimalType
DateType
TimeType
TimestampType
DurationType
BinaryType
ListType
StructType
MapType
UnknownType
~~~

---

# 96. Final summary

Declarative schema V1 is intentionally strict.

It provides a human-friendly form for existing PyTransformKit schema semantics without adding runtime behavior.

The contract is:

~~~text
YAML
 ↓
strict parsing
 ↓
versioned declarative grammar
 ↓
validated definitions
 ↓
canonical DataType resolution
 ↓
canonical Field values
 ↓
canonical Schema
~~~

It deliberately excludes templating, arbitrary metadata, quality DSLs, engine-native types, composition and executable configuration.

The governing rule remains:

> **The YAML syntax makes Schema easier to write; it does not redefine what Schema means.**
