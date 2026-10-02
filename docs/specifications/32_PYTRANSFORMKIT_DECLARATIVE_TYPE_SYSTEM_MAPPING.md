# 32 — PyTransformKit Declarative Type System Mapping

> **Document status:** DRAFT NORMATIVE SPECIFICATION  
> **Depends on:** 31_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SPECIFICATION.md  
> **Canonical Domain source:** src/pytransformkit/domain/data/data_types.py  
> **Declarative language version:** 1  
> **Scope:** Exhaustive YAML ↔ DataType mapping

---

# 1. Purpose

This document defines the exhaustive mapping between declarative schema V1 type
syntax and the canonical PyTransformKit DataType hierarchy.

It freezes, for every supported logical type:

- accepted YAML syntax;
- normalized TypeDefinition meaning;
- canonical DataType constructor;
- validation rules;
- default values;
- accepted aliases;
- canonical emitted YAML form;
- semantic round-trip expectations.

The core invariant is:

~~~text
YAML type syntax
      ↓
TypeDefinition
      ↓
DeclarativeTypeResolver
      ↓
canonical DataType
~~~

and in reverse:

~~~text
canonical DataType
      ↓
TypeDefinitionExporter
      ↓
canonical YAML type syntax
~~~

---

# 2. Canonical Domain type inventory

Declarative schema V1 maps to the current canonical Domain types:

~~~text
DataType
├── StringType
├── BooleanType
├── IntegerType
├── FloatType
├── DecimalType
├── DateType
├── TimeType
├── TimestampType
├── DurationType
├── BinaryType
├── ListType
├── StructType
├── MapType
└── UnknownType
~~~

StructType embeds:

~~~text
StructField
├── name
├── data_type
└── nullable
~~~

No declarative type may introduce semantics that cannot be represented by this
Domain model.

---

# 3. Mapping principles

The mapping follows six rules.

## MAP-01 — Domain is authoritative

Declarative syntax follows the Domain type system.

The YAML language does not define an independent logical type hierarchy.

## MAP-02 — Closed-world resolution

Only explicitly defined type names are accepted.

Unknown names fail.

## MAP-03 — Canonical export is unique

The parser may accept selected aliases.

The exporter emits one canonical representation.

## MAP-04 — Defaults equal Domain defaults

When declarative syntax omits an optional type parameter, the default MUST match the
current canonical DataType constructor default.

## MAP-05 — Recursive mapping

Nested types recursively reuse this same mapping specification.

## MAP-06 — Engine neutrality

Declarative type names map to PyTransformKit logical types, never directly to
Pandas, Polars, Arrow or DuckDB dtypes.

---

# 4. Canonical mapping table

| Declarative form | Canonical Domain value | Canonical export |
| --- | --- | --- |
| string | StringType() | string |
| boolean | BooleanType() | boolean |
| int8 | IntegerType(bits=8, signed=True) | int8 |
| int16 | IntegerType(bits=16, signed=True) | int16 |
| int32 | IntegerType(bits=32, signed=True) | int32 |
| int64 | IntegerType(bits=64, signed=True) | int64 |
| uint8 | IntegerType(bits=8, signed=False) | uint8 |
| uint16 | IntegerType(bits=16, signed=False) | uint16 |
| uint32 | IntegerType(bits=32, signed=False) | uint32 |
| uint64 | IntegerType(bits=64, signed=False) | uint64 |
| float32 | FloatType(bits=32) | float32 |
| float64 | FloatType(bits=64) | float64 |
| decimal(...) | DecimalType(precision, scale) | decimal(...) |
| binary | BinaryType() | binary |
| date | DateType() | date |
| time | TimeType(unit="us") | time |
| time(unit) | TimeType(unit=...) | time or structured time |
| timestamp | TimestampType(unit="us", timezone=None) | timestamp |
| timestamp(unit, timezone) | TimestampType(...) | timestamp or structured timestamp |
| duration | DurationType(unit="us") | duration |
| duration(unit) | DurationType(unit=...) | duration or structured duration |
| list(...) | ListType(...) | structured list |
| struct(...) | StructType(...) | structured struct |
| map(...) | MapType(...) | structured map |
| unknown | UnknownType() | unknown |

---

# 5. TypeDefinition model expectation

The declarative model SHOULD normalize authoring syntax into explicit type-definition
values.

A possible shape is:

~~~text
TypeDefinition
├── StringTypeDefinition
├── BooleanTypeDefinition
├── IntegerTypeDefinition
│   ├── bits
│   └── signed
├── FloatTypeDefinition
│   └── bits
├── DecimalTypeDefinition
│   ├── precision
│   └── scale
├── DateTypeDefinition
├── TimeTypeDefinition
│   └── unit
├── TimestampTypeDefinition
│   ├── unit
│   └── timezone
├── DurationTypeDefinition
│   └── unit
├── BinaryTypeDefinition
├── ListTypeDefinition
│   ├── element
│   └── element_nullable
├── StructTypeDefinition
│   └── fields
├── MapTypeDefinition
│   ├── key
│   ├── value
│   └── value_nullable
└── UnknownTypeDefinition
~~~

Exact Python class names are frozen later in document 33.

The semantic fields above are normative.

---

# 6. StringType

## Accepted YAML

~~~yaml
type: string
~~~

## Normalized meaning

~~~text
StringTypeDefinition()
~~~

## Domain mapping

~~~python
StringType()
~~~

or equivalently:

~~~python
DataType.string()
~~~

## Parameters

None.

## Invalid structured forms

~~~yaml
type:
  string:
    length: 255
~~~

~~~yaml
type:
  string:
    encoding: utf-8
~~~

Length, collation and encoding are not part of canonical StringType semantics.

## Canonical export

~~~yaml
type: string
~~~

---

# 7. BooleanType

## Accepted YAML

~~~yaml
type: boolean
~~~

## Domain mapping

~~~python
BooleanType()
~~~

or:

~~~python
DataType.boolean()
~~~

## Parameters

None.

## Aliases

Declarative V1 does NOT accept:

~~~text
bool
yesno
bit
~~~

## Canonical export

~~~yaml
type: boolean
~~~

---

# 8. IntegerType model

Canonical IntegerType has:

~~~text
bits: int = 64
signed: bool = true
~~~

Valid bit widths are:

~~~text
8
16
32
64
~~~

Declarative V1 intentionally exposes canonical scalar aliases rather than a
parameterized integer object.

---

# 9. Signed integer mapping

## int8

~~~yaml
type: int8
~~~

maps to:

~~~python
IntegerType(bits=8, signed=True)
~~~

## int16

~~~yaml
type: int16
~~~

maps to:

~~~python
IntegerType(bits=16, signed=True)
~~~

## int32

~~~yaml
type: int32
~~~

maps to:

~~~python
IntegerType(bits=32, signed=True)
~~~

## int64

~~~yaml
type: int64
~~~

maps to:

~~~python
IntegerType(bits=64, signed=True)
~~~

---

# 10. Unsigned integer mapping

## uint8

~~~yaml
type: uint8
~~~

maps to:

~~~python
IntegerType(bits=8, signed=False)
~~~

## uint16

~~~yaml
type: uint16
~~~

maps to:

~~~python
IntegerType(bits=16, signed=False)
~~~

## uint32

~~~yaml
type: uint32
~~~

maps to:

~~~python
IntegerType(bits=32, signed=False)
~~~

## uint64

~~~yaml
type: uint64
~~~

maps to:

~~~python
IntegerType(bits=64, signed=False)
~~~

---

# 11. Integer authoring alias

The authoring alias:

~~~yaml
type: integer
~~~

is ACCEPTED in declarative V1.

It normalizes to:

~~~python
IntegerType(bits=64, signed=True)
~~~

Rationale:

- it matches the common human expectation for a generic integer;
- it preserves the current IntegerType default;
- it makes simple declarations ergonomic;
- canonical export remains unambiguous.

Canonical export MUST emit:

~~~yaml
type: int64
~~~

and never:

~~~yaml
type: integer
~~~

---

# 12. Integer forms not accepted

Declarative V1 rejects parameterized integer syntax such as:

~~~yaml
type:
  integer:
    bits: 64
    signed: true
~~~

The scalar vocabulary already covers every canonical valid IntegerType combination.

It also rejects:

~~~text
long
short
smallint
bigint
tinyint
int
uint
~~~

unless a future declarative language version explicitly adds aliases.

---

# 13. FloatType model

Canonical FloatType has:

~~~text
bits: int = 64
~~~

Allowed values are:

~~~text
32
64
~~~

---

# 14. Float mappings

## float32

~~~yaml
type: float32
~~~

maps to:

~~~python
FloatType(bits=32)
~~~

## float64

~~~yaml
type: float64
~~~

maps to:

~~~python
FloatType(bits=64)
~~~

---

# 15. Float authoring alias

The alias:

~~~yaml
type: float
~~~

is ACCEPTED.

It normalizes to:

~~~python
FloatType(bits=64)
~~~

Canonical export MUST emit:

~~~yaml
type: float64
~~~

---

# 16. Float forms not accepted

Invalid:

~~~yaml
type:
  float:
    bits: 64
~~~

Invalid aliases:

~~~text
double
real
single
numeric
~~~

unless explicitly introduced in a future language version.

---

# 17. DecimalType

Canonical DecimalType has:

~~~text
precision: int
scale: int
~~~

and Domain invariants:

~~~text
precision > 0
scale >= 0
scale <= precision
~~~

---

# 18. Decimal YAML mapping

Canonical declaration:

~~~yaml
type:
  decimal:
    precision: 18
    scale: 2
~~~

maps to:

~~~python
DecimalType(
    precision=18,
    scale=2,
)
~~~

or:

~~~python
DataType.decimal(
    precision=18,
    scale=2,
)
~~~

---

# 19. Decimal validation

precision MUST:

- be an integer;
- be greater than zero.

scale MUST:

- be an integer;
- be non-negative;
- not exceed precision.

Invalid:

~~~yaml
type:
  decimal:
    precision: 0
    scale: 0
~~~

Invalid:

~~~yaml
type:
  decimal:
    precision: 10
    scale: 11
~~~

Invalid:

~~~yaml
type:
  decimal:
    precision: "18"
    scale: 2
~~~

---

# 20. Decimal defaults

No decimal parameter has a declarative default.

Both precision and scale are REQUIRED.

Invalid:

~~~yaml
type:
  decimal:
    precision: 18
~~~

Invalid:

~~~yaml
type: decimal
~~~

---

# 21. Decimal aliases

Declarative V1 does not accept:

~~~text
numeric
number
fixed
money
~~~

These names can carry backend-specific semantics and are therefore excluded.

---

# 22. BinaryType

Accepted:

~~~yaml
type: binary
~~~

maps to:

~~~python
BinaryType()
~~~

or:

~~~python
DataType.binary()
~~~

No parameters are supported.

Invalid:

~~~yaml
type:
  binary:
    length: 1024
~~~

Canonical export:

~~~yaml
type: binary
~~~

---

# 23. DateType

Accepted:

~~~yaml
type: date
~~~

maps to:

~~~python
DateType()
~~~

or:

~~~python
DataType.date()
~~~

No parameters are supported.

Canonical export:

~~~yaml
type: date
~~~

---

# 24. Time units

TimeType, TimestampType and DurationType share the canonical time-unit vocabulary:

~~~text
s
ms
us
ns
~~~

Meaning:

| Unit | Meaning |
| --- | --- |
| s | second |
| ms | millisecond |
| us | microsecond |
| ns | nanosecond |

The canonical Domain default is:

~~~text
us
~~~

Any other unit MUST fail.

---

# 25. TimeType short form

~~~yaml
type: time
~~~

maps to:

~~~python
TimeType(unit="us")
~~~

or:

~~~python
DataType.time()
~~~

Canonical export uses short form when unit equals us:

~~~yaml
type: time
~~~

---

# 26. TimeType structured form

~~~yaml
type:
  time:
    unit: ms
~~~

maps to:

~~~python
TimeType(unit="ms")
~~~

Allowed body properties:

~~~text
unit
~~~

unit is REQUIRED in structured form.

Invalid:

~~~yaml
type:
  time: {}
~~~

The short form exists for defaults.

---

# 27. TimeType canonical emission

Domain value:

~~~python
TimeType(unit="us")
~~~

emits:

~~~yaml
type: time
~~~

Domain value:

~~~python
TimeType(unit="ns")
~~~

emits:

~~~yaml
type:
  time:
    unit: ns
~~~

---

# 28. TimestampType model

Canonical TimestampType has:

~~~text
unit: str = "us"
timezone: str | None = None
~~~

timezone, when not None, MUST contain non-whitespace text.

---

# 29. TimestampType short form

~~~yaml
type: timestamp
~~~

maps to:

~~~python
TimestampType(
    unit="us",
    timezone=None,
)
~~~

or:

~~~python
DataType.timestamp()
~~~

Canonical export uses short form only for this exact state.

---

# 30. TimestampType structured form without timezone

~~~yaml
type:
  timestamp:
    unit: ns
~~~

maps to:

~~~python
TimestampType(
    unit="ns",
    timezone=None,
)
~~~

---

# 31. TimestampType structured form with timezone

~~~yaml
type:
  timestamp:
    unit: us
    timezone: UTC
~~~

maps to:

~~~python
TimestampType(
    unit="us",
    timezone="UTC",
)
~~~

timezone is treated as a logical opaque timezone identifier string.

Declarative V1 does not normalize timezone aliases.

---

# 32. Timestamp timezone validation

Valid examples MAY include:

~~~text
UTC
Europe/Paris
America/New_York
+02:00
~~~

provided the Domain accepts the non-empty string.

Declarative V1 does not require an IANA timezone database lookup.

This avoids creating environment-dependent validation.

Blank values MUST fail.

Invalid:

~~~yaml
timezone: ""
~~~

Explicit null MUST fail.

Omission represents no timezone.

---

# 33. Timestamp canonical emission

~~~python
TimestampType(unit="us", timezone=None)
~~~

emits:

~~~yaml
type: timestamp
~~~

~~~python
TimestampType(unit="ns", timezone=None)
~~~

emits:

~~~yaml
type:
  timestamp:
    unit: ns
~~~

~~~python
TimestampType(unit="us", timezone="UTC")
~~~

emits:

~~~yaml
type:
  timestamp:
    unit: us
    timezone: UTC
~~~

---

# 34. DurationType short form

~~~yaml
type: duration
~~~

maps to:

~~~python
DurationType(unit="us")
~~~

or:

~~~python
DataType.duration()
~~~

Canonical export uses short form when unit is us.

---

# 35. DurationType structured form

~~~yaml
type:
  duration:
    unit: ms
~~~

maps to:

~~~python
DurationType(unit="ms")
~~~

Structured duration body supports exactly:

~~~text
unit
~~~

---

# 36. Duration canonical emission

~~~python
DurationType(unit="us")
~~~

emits:

~~~yaml
type: duration
~~~

~~~python
DurationType(unit="s")
~~~

emits:

~~~yaml
type:
  duration:
    unit: s
~~~

---

# 37. UnknownType

Intentional unknown logical type is declared as:

~~~yaml
type: unknown
~~~

maps to:

~~~python
UnknownType()
~~~

or:

~~~python
DataType.unknown()
~~~

UnknownType means the type is intentionally unspecified or not precisely inferred.

It MUST NOT be used as fallback for invalid declarations.

Therefore:

~~~yaml
type: intger
~~~

is an error, not UnknownType.

---

# 38. ListType model

Canonical ListType has:

~~~text
element_type: DataType
element_nullable: bool = true
~~~

Declarative syntax mirrors these semantics.

---

# 39. ListType mapping

Canonical:

~~~yaml
type:
  list:
    element:
      type: string
    element_nullable: true
~~~

maps to:

~~~python
ListType(
    element_type=StringType(),
    element_nullable=True,
)
~~~

or:

~~~python
DataType.list_of(
    StringType(),
    element_nullable=True,
)
~~~

---

# 40. List element_nullable default

If omitted:

~~~yaml
type:
  list:
    element:
      type: string
~~~

the semantic default is:

~~~text
element_nullable = true
~~~

The canonical emitter SHOULD emit element_nullable explicitly.

This keeps nested nullability visible.

---

# 41. List element type recursion

element.type recursively follows the complete type grammar.

Example:

~~~yaml
type:
  list:
    element:
      type:
        decimal:
          precision: 18
          scale: 2
    element_nullable: false
~~~

maps to:

~~~python
ListType(
    element_type=DecimalType(18, 2),
    element_nullable=False,
)
~~~

---

# 42. Nested lists

Valid:

~~~yaml
type:
  list:
    element:
      type:
        list:
          element:
            type: int64
          element_nullable: false
    element_nullable: true
~~~

maps conceptually to:

~~~python
ListType(
    element_type=ListType(
        element_type=IntegerType(bits=64, signed=True),
        element_nullable=False,
    ),
    element_nullable=True,
)
~~~

---

# 43. List invalid forms

Invalid scalar:

~~~yaml
type: list
~~~

Invalid missing element:

~~~yaml
type:
  list:
    element_nullable: false
~~~

Invalid named element:

~~~yaml
type:
  list:
    element:
      name: item
      type: string
~~~

A list element is a type holder, not a StructField.

---

# 44. StructType model

Canonical StructType has:

~~~text
fields: tuple[StructField, ...]
~~~

Each StructField has:

~~~text
name
data_type
nullable
~~~

Struct field order is semantic and MUST be preserved.

---

# 45. StructType mapping

~~~yaml
type:
  struct:
    fields:
      - name: city
        type: string
        nullable: true

      - name: postal_code
        type: string
        nullable: false
~~~

maps to:

~~~python
StructType(
    fields=(
        StructField(
            name="city",
            data_type=StringType(),
            nullable=True,
        ),
        StructField(
            name="postal_code",
            data_type=StringType(),
            nullable=False,
        ),
    )
)
~~~

---

# 46. Struct field nullability default

If omitted:

~~~yaml
- name: city
  type: string
~~~

the semantic default is:

~~~text
nullable = true
~~~

Canonical emission SHOULD include nested nullable explicitly.

---

# 47. Struct field descriptions

StructField does not contain description in the current Domain.

Therefore invalid:

~~~yaml
- name: city
  type: string
  nullable: true
  description: Customer city
~~~

No description may be silently dropped.

---

# 48. Struct field uniqueness

Duplicate nested field names MUST fail.

Invalid:

~~~yaml
type:
  struct:
    fields:
      - name: city
        type: string

      - name: city
        type: int64
~~~

This matches StructType Domain invariants.

---

# 49. Empty struct

The current Domain permits:

~~~python
StructType(fields=())
~~~

Therefore declarative V1 MAY accept:

~~~yaml
type:
  struct:
    fields: []
~~~

The exporter MUST preserve an empty canonical struct if it exists.

---

# 50. Struct recursive nesting

A StructField type may itself be any supported DataType.

Example:

~~~yaml
type:
  struct:
    fields:
      - name: coordinates
        type:
          struct:
            fields:
              - name: latitude
                type: float64
                nullable: false
              - name: longitude
                type: float64
                nullable: false
        nullable: true
~~~

---

# 51. MapType model

Canonical MapType has:

~~~text
key_type: DataType
value_type: DataType
value_nullable: bool = true
~~~

The Domain currently does not impose a restricted set of key DataTypes.

Declarative V1 therefore does not invent one.

---

# 52. MapType mapping

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

maps to:

~~~python
MapType(
    key_type=StringType(),
    value_type=IntegerType(bits=64, signed=True),
    value_nullable=True,
)
~~~

or:

~~~python
DataType.map_of(
    StringType(),
    IntegerType(bits=64, signed=True),
    value_nullable=True,
)
~~~

---

# 53. Map value_nullable default

If omitted:

~~~yaml
type:
  map:
    key:
      type: string
    value:
      type: int64
~~~

the semantic default is:

~~~text
value_nullable = true
~~~

Canonical emitter SHOULD emit value_nullable explicitly.

---

# 54. Map key recursion

The key type holder accepts any canonical DataType under current Domain rules.

Example:

~~~yaml
key:
  type: int64
~~~

Declarative V1 does not impose engine-specific map-key restrictions.

If a future Domain rule narrows key types, declarative validation must follow it.

---

# 55. Map value recursion

Map value may be arbitrarily nested within configured depth limits.

Example:

~~~yaml
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
      element_nullable: false
~~~

---

# 56. Map invalid forms

Invalid scalar:

~~~yaml
type: map
~~~

Invalid missing key:

~~~yaml
type:
  map:
    value:
      type: string
~~~

Invalid missing value:

~~~yaml
type:
  map:
    key:
      type: string
~~~

---

# 57. Type aliases policy

Declarative V1 accepts exactly two ergonomic aliases:

~~~text
integer → int64
float   → float64
~~~

No other aliases are accepted.

Rationale:

- both correspond to current Domain defaults;
- both are common authoring terms;
- neither creates engine-specific semantics;
- canonical export remains explicit.

---

# 58. Canonical alias normalization

The parser normalizes:

~~~yaml
type: integer
~~~

to:

~~~text
IntegerTypeDefinition(bits=64, signed=true)
~~~

and:

~~~yaml
type: float
~~~

to:

~~~text
FloatTypeDefinition(bits=64)
~~~

The exporter never emits aliases.

---

# 59. Unsupported SQL-style aliases

Declarative V1 rejects:

~~~text
varchar
char
text
smallint
bigint
tinyint
double
real
numeric
number
datetime
datetime64
array
object
json
variant
~~~

These names may differ across engines and ecosystems.

Users must express canonical logical semantics instead.

---

# 60. Unsupported engine-native names

Declarative V1 rejects engine-native dtype names such as:

~~~text
Int64
Utf8
LargeUtf8
pl.String
pd.Int64Dtype
pa.int64
duckdb.VARCHAR
~~~

The correct path is:

~~~text
declarative logical type
        ↓
PyTransformKit DataType
        ↓
engine adapter
        ↓
physical dtype
~~~

---

# 61. Validation order

Type resolution SHOULD follow this order:

~~~text
1. determine scalar vs structured form
2. validate discriminator
3. validate allowed properties
4. validate scalar parameter types
5. apply documented defaults
6. validate semantic constraints
7. recursively resolve child type definitions
8. construct canonical DataType
~~~

---

# 62. Domain constructor validation

The declarative resolver SHOULD validate before construction for good diagnostics.

The canonical DataType constructor MUST still be allowed to enforce its own
invariants.

The architecture therefore preserves:

~~~text
declarative validation
        ↓
Domain constructor validation
~~~

No declarative code bypasses Domain invariants.

---

# 63. Error path examples

Invalid decimal precision:

~~~text
schema.fields[2].type.decimal.precision
~~~

Invalid list child:

~~~text
schema.fields[4].type.list.element.type
~~~

Invalid nested struct field:

~~~text
schema.fields[5].type.struct.fields[1].type
~~~

Invalid map value:

~~~text
schema.fields[6].type.map.value.type
~~~

---

# 64. Canonical type emission algorithm

Given a DataType, the exporter applies deterministic dispatch:

~~~text
StringType      → string
BooleanType     → boolean
IntegerType     → int*/uint*
FloatType       → float*
DecimalType     → decimal structure
DateType        → date
TimeType        → time short/structured
TimestampType   → timestamp short/structured
DurationType    → duration short/structured
BinaryType      → binary
ListType        → list structure
StructType      → struct structure
MapType         → map structure
UnknownType     → unknown
~~~

Unknown DataType subclasses MUST fail export rather than being guessed.

---

# 65. Integer export algorithm

For IntegerType:

~~~text
bits=8,  signed=true   → int8
bits=16, signed=true   → int16
bits=32, signed=true   → int32
bits=64, signed=true   → int64
bits=8,  signed=false  → uint8
bits=16, signed=false  → uint16
bits=32, signed=false  → uint32
bits=64, signed=false  → uint64
~~~

Any impossible state should already be rejected by Domain construction.

---

# 66. Float export algorithm

~~~text
bits=32 → float32
bits=64 → float64
~~~

No alias is emitted.

---

# 67. Temporal export algorithm

For TimeType:

~~~text
unit=us → scalar time
other   → structured time
~~~

For DurationType:

~~~text
unit=us → scalar duration
other   → structured duration
~~~

For TimestampType:

~~~text
unit=us + timezone=None
    → scalar timestamp

otherwise
    → structured timestamp
~~~

---

# 68. Nested export algorithm

ListType:

~~~text
list:
  element:
    type: <recursive export>
  element_nullable: <bool>
~~~

StructType:

~~~text
struct:
  fields:
    - name: ...
      type: <recursive export>
      nullable: <bool>
~~~

MapType:

~~~text
map:
  key:
    type: <recursive export>
  value:
    type: <recursive export>
  value_nullable: <bool>
~~~

---

# 69. Semantic equality target

The mapping MUST satisfy:

~~~text
DataType
   ↓ export
YAML type
   ↓ parse
TypeDefinition
   ↓ resolve
DataType'

DataType == DataType'
~~~

using the canonical dataclass value semantics of current DataType implementations.

---

# 70. Primitive round-trip examples

~~~text
StringType()
→ string
→ StringType()
~~~

~~~text
IntegerType(bits=32, signed=False)
→ uint32
→ IntegerType(bits=32, signed=False)
~~~

~~~text
FloatType(bits=64)
→ float64
→ FloatType(bits=64)
~~~

~~~text
UnknownType()
→ unknown
→ UnknownType()
~~~

---

# 71. Parameterized round-trip examples

~~~text
DecimalType(18, 2)
→ decimal(18, 2)
→ DecimalType(18, 2)
~~~

~~~text
TimestampType(unit="ns", timezone="UTC")
→ timestamp(unit=ns, timezone=UTC)
→ TimestampType(unit="ns", timezone="UTC")
~~~

---

# 72. Nested round-trip example

~~~text
ListType(
  StructType(
    city: StringType
    country: StringType
  ),
  element_nullable=false
)

        ↓

YAML list/struct declaration

        ↓

same canonical ListType value
~~~

---

# 73. No lossy mapping

A declarative mapping is considered valid only when it can preserve canonical Domain
state.

The resolver/exporter MUST NOT:

- drop signedness;
- drop integer width;
- drop float width;
- drop decimal precision;
- drop decimal scale;
- drop temporal unit;
- drop timestamp timezone;
- drop list element nullability;
- drop struct field nullability;
- drop map value nullability;
- reorder struct fields.

---

# 74. No engine-dependent mapping

The following is prohibited:

~~~text
int64
 ↓
if pandas then ...
if polars then ...
~~~

Type resolution produces only canonical DataType values.

Engine adapters remain solely responsible for physical mapping.

---

# 75. Compatibility with schema serialization

Declarative type syntax and canonical DataType serialization MAY represent the same
logical values differently.

Declarative YAML is for human authoring.

Canonical serialization remains the software interchange contract.

No declarative type name is automatically a wire-contract identifier.

---

# 76. Compatibility with future Domain types

If PyTransformKit adds a new canonical DataType in a future release, declarative V1
does not automatically gain support for it.

Support requires:

1. explicit mapping design;
2. parser grammar update;
3. exporter update;
4. round-trip tests;
5. compatibility decision for declarative language versioning.

Closed-world behavior is intentional.

---

# 77. Unsupported custom DataType subclasses

If a user constructs an unknown custom subclass:

~~~python
class MyType(DataType):
    ...
~~~

the declarative V1 exporter MUST fail.

It MUST NOT emit a Python-qualified class name.

It MUST NOT use repr as a transport format.

---

# 78. Type resolver purity

DeclarativeTypeResolver SHOULD be a pure deterministic service.

It MUST NOT:

- access filesystem;
- access network;
- import engines;
- inspect environment variables;
- activate plugins implicitly;
- mutate global state.

Input:

~~~text
TypeDefinition
~~~

Output:

~~~text
DataType
~~~

---

# 79. Type exporter purity

TypeDefinitionExporter SHOULD also be deterministic and side-effect free.

Input:

~~~text
DataType
~~~

Output:

~~~text
TypeDefinition
~~~

No YAML formatting occurs at this layer.

---

# 80. Suggested resolver interface

Conceptually:

~~~python
class DeclarativeTypeResolver:
    def resolve(
        self,
        definition: TypeDefinition,
    ) -> DataType:
        ...
~~~

The implementation SHOULD use explicit dispatch rather than dynamic imports.

---

# 81. Suggested exporter interface

Conceptually:

~~~python
class DeclarativeTypeExporter:
    def export(
        self,
        data_type: DataType,
    ) -> TypeDefinition:
        ...
~~~

Exact public visibility is defined later.

These may remain internal application services.

---

# 82. Suggested scalar registry

An internal immutable mapping MAY represent simple scalar types:

~~~text
string   → StringType
boolean  → BooleanType
int8     → IntegerType(8, true)
...
unknown  → UnknownType
~~~

Parameterized and nested types SHOULD use explicit resolver branches.

This keeps recursive validation understandable.

---

# 83. No mutable plugin registry in V1

Declarative V1 type mapping is fixed.

There is no automatic plugin extension such as:

~~~yaml
type: my_company_type
~~~

Plugin-defined logical types require a separate versioned extension design.

---

# 84. Test matrix — primitive types

Positive tests MUST cover:

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
integer alias
float32
float64
float alias
binary
date
time
timestamp
duration
unknown
~~~

Each test MUST assert exact DataType equality.

---

# 85. Test matrix — decimal

Tests MUST cover:

~~~text
precision=1, scale=0
precision=18, scale=2
scale=precision
precision <= 0
scale < 0
scale > precision
string precision
float precision
unknown property
missing precision
missing scale
~~~

---

# 86. Test matrix — temporal

Tests MUST cover every allowed unit:

~~~text
s
ms
us
ns
~~~

and reject:

~~~text
seconds
microseconds
NS
empty
null
integer
~~~

Timestamp tests MUST cover:

~~~text
timezone absent
timezone UTC
timezone Europe/Paris
blank timezone
explicit null timezone
~~~

---

# 87. Test matrix — list

Tests MUST cover:

~~~text
primitive element
parameterized element
nested list
struct element
map element
element_nullable true
element_nullable false
default element_nullable
missing element
invalid child type
unknown property
~~~

---

# 88. Test matrix — struct

Tests MUST cover:

~~~text
empty struct
one field
multiple ordered fields
nested struct
list field
map field
default nested nullable
explicit nested nullable
duplicate nested fields
nested description rejection
unknown field property
~~~

---

# 89. Test matrix — map

Tests MUST cover:

~~~text
primitive key/value
nested value
nested key under Domain-permitted semantics
value_nullable true
value_nullable false
default value_nullable
missing key
missing value
invalid key type syntax
invalid value type syntax
unknown property
~~~

---

# 90. Canonical mapping acceptance criteria

The type-system mapping is correct when:

1. every canonical DataType has one declarative representation;
2. every declarative canonical form maps to exactly one DataType state;
3. integer width and signedness are preserved;
4. float width is preserved;
5. decimal precision and scale are preserved;
6. temporal units are preserved;
7. timestamp timezone is preserved;
8. list element type and nullability are preserved;
9. struct field order and nullability are preserved;
10. map key/value types and value nullability are preserved;
11. intentional UnknownType remains distinct from invalid input;
12. accepted aliases normalize deterministically;
13. canonical exporter never emits aliases;
14. unknown logical type names fail;
15. unsupported DataType subclasses fail export;
16. no engine dependency participates in mapping;
17. nested round-trip equality holds recursively.

---

# 91. Exhaustive canonical mapping reference

~~~text
YAML              DOMAIN

string            StringType()

boolean           BooleanType()

int8              IntegerType(bits=8, signed=True)
int16             IntegerType(bits=16, signed=True)
int32             IntegerType(bits=32, signed=True)
int64             IntegerType(bits=64, signed=True)

uint8             IntegerType(bits=8, signed=False)
uint16            IntegerType(bits=16, signed=False)
uint32            IntegerType(bits=32, signed=False)
uint64            IntegerType(bits=64, signed=False)

integer           alias → IntegerType(bits=64, signed=True)

float32           FloatType(bits=32)
float64           FloatType(bits=64)
float             alias → FloatType(bits=64)

decimal           DecimalType(precision, scale)

binary            BinaryType()

date              DateType()

time              TimeType(unit="us")
time{unit}        TimeType(unit)

timestamp         TimestampType(unit="us", timezone=None)
timestamp{...}    TimestampType(unit, timezone)

duration          DurationType(unit="us")
duration{unit}    DurationType(unit)

list              ListType(element_type, element_nullable)

struct            StructType(tuple[StructField, ...])

map               MapType(key_type, value_type, value_nullable)

unknown           UnknownType()
~~~

---

# 92. Recommended canonical examples

## Integer

~~~yaml
type: int64
~~~

## Decimal

~~~yaml
type:
  decimal:
    precision: 18
    scale: 2
~~~

## Timestamp with timezone

~~~yaml
type:
  timestamp:
    unit: us
    timezone: UTC
~~~

## List

~~~yaml
type:
  list:
    element:
      type: string
    element_nullable: false
~~~

## Struct

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

## Map

~~~yaml
type:
  map:
    key:
      type: string
    value:
      type: int64
    value_nullable: false
~~~

---

# 93. Decisions frozen by this document

## DEC-TYPE-01

Declarative V1 maps only to the current canonical DataType hierarchy.

## DEC-TYPE-02

integer is accepted as an alias for int64.

## DEC-TYPE-03

float is accepted as an alias for float64.

## DEC-TYPE-04

Canonical export never emits aliases.

## DEC-TYPE-05

Integer canonical names encode width and signedness.

## DEC-TYPE-06

Decimal requires explicit precision and scale.

## DEC-TYPE-07

Temporal short forms represent Domain defaults.

## DEC-TYPE-08

Nested types are recursively representable.

## DEC-TYPE-09

StructField descriptions are unsupported because the Domain cannot preserve them.

## DEC-TYPE-10

Map key types follow Domain semantics, not engine-specific restrictions.

## DEC-TYPE-11

UnknownType must be requested explicitly.

## DEC-TYPE-12

Unknown type names never fall back to UnknownType.

## DEC-TYPE-13

Custom Python DataType subclasses cannot be serialized declaratively in V1.

## DEC-TYPE-14

Type mapping is closed-world and plugin-independent in V1.

---

# 94. Relationship with document 31

Document 31 defines the YAML grammar.

This document defines the semantic meaning of every valid type declaration.

Therefore:

~~~text
31 = syntax
32 = type semantics
~~~

If a conflict exists, the stricter interpretation that preserves the canonical
Domain and round-trip safety MUST be preferred until the specifications are
reconciled.

---

# 95. Next document

The next document freezes the application-layer definition objects themselves:

~~~text
33_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_DOMAIN_MODEL.md
~~~

Despite the filename, these are not canonical PyTransformKit Domain objects.

That document must precisely define:

~~~text
SchemaDocument
SchemaDefinition
FieldDefinition
TypeDefinition
Primitive and nested TypeDefinition variants
source diagnostic context
immutability
equality
validation boundaries
~~~

and their relationship to canonical:

~~~text
Schema
Field
DataType
StructField
~~~

---

# 96. Final summary

The declarative type system does not invent new data semantics.

It is a human-readable projection of the canonical PyTransformKit DataType model.

The complete direction is:

~~~text
human YAML type
      ↓
closed declarative vocabulary
      ↓
TypeDefinition
      ↓
DeclarativeTypeResolver
      ↓
canonical DataType
      ↓
engine adapters
~~~

and never:

~~~text
YAML
  ↓
engine-native dtype
~~~

The contract can therefore be summarized as:

> One logical type system, one canonical Domain representation, multiple authoring syntaxes.
