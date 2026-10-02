# 33 — PyTransformKit Declarative Schema — Domain Model

> **Document status:** DRAFT NORMATIVE SPECIFICATION  
> **Depends on:** 30_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ARCHITECTURE.md  
> **Depends on:** 31_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SPECIFICATION.md  
> **Depends on:** 32_PYTRANSFORMKIT_DECLARATIVE_TYPE_SYSTEM_MAPPING.md  
> **Scope:** Declarative definition model and intermediate representation  
> **Canonical Domain target:** Schema / Field / DataType / StructField

---

# 1. Purpose

This document defines the application-layer model used to represent declarative
schema authoring intent before compilation into the canonical PyTransformKit Domain.

It freezes the responsibilities and semantics of:

- SchemaDocument;
- SchemaDefinition;
- FieldDefinition;
- TypeDefinition;
- all concrete TypeDefinition variants;
- StructFieldDefinition;
- source diagnostic context;
- equality and immutability rules;
- validation boundaries;
- conversion boundaries toward canonical Domain objects.

Despite the filename, these objects are NOT new canonical PyTransformKit Domain
objects.

They are declarative authoring definitions.

---

# 2. Core distinction

The architecture contains two distinct semantic levels:

~~~text
DECLARATIVE DEFINITION MODEL
    represents authored intent

CANONICAL DOMAIN MODEL
    represents PyTransformKit schema semantics
~~~

The flow is:

~~~text
YAML
  ↓
SchemaDocument
  ↓
SchemaDefinition
  ↓
FieldDefinition
  ↓
TypeDefinition
  ↓
SchemaDefinitionCompiler
  ↓
Schema
  ↓
Field
  ↓
DataType
~~~

The definition model exists to make parsing, validation and diagnostics explicit.

It MUST NOT replace canonical Domain objects.

---

# 3. Naming note

The term "Domain Model" in this filename refers to the conceptual model of the
declarative-schema feature.

Architecturally, the implementation belongs to:

~~~text
application/declarative
~~~

and not:

~~~text
domain/data
~~~

This distinction is normative.

---

# 4. Design goals

The declarative definition model MUST be:

- immutable;
- engine-independent;
- YAML-independent;
- parser-independent;
- filesystem-independent;
- deterministic;
- structurally explicit;
- recursively representable;
- suitable for validation;
- suitable for source-aware diagnostics;
- compilable into canonical Domain objects;
- exportable from canonical Domain objects where semantics are preserved.

---

# 5. Non-goals

The definition model MUST NOT:

- execute transformations;
- own physical engine types;
- replace Schema;
- replace Field;
- replace DataType;
- own runtime state;
- own I/O resources;
- own workflow semantics;
- own quality execution;
- import YAML libraries;
- perform filesystem access;
- perform network access;
- dynamically import user-specified Python classes.

---

# 6. Proposed module

The model SHOULD live in:

~~~text
src/pytransformkit/application/declarative/model.py
~~~

Supporting modules may include:

~~~text
application/declarative/
├── model.py
├── validation.py
├── type_resolution.py
├── compiler.py
└── exporter.py
~~~

The model module MUST remain free of YAML-specific dependencies.

---

# 7. Model overview

The target object graph is:

~~~text
SchemaDocument
├── version
└── schemas: tuple[SchemaDefinition, ...]

SchemaDefinition
├── name
└── fields: tuple[FieldDefinition, ...]

FieldDefinition
├── name
├── data_type: TypeDefinition
├── nullable
└── description

TypeDefinition
├── StringTypeDefinition
├── BooleanTypeDefinition
├── IntegerTypeDefinition
├── FloatTypeDefinition
├── DecimalTypeDefinition
├── DateTypeDefinition
├── TimeTypeDefinition
├── TimestampTypeDefinition
├── DurationTypeDefinition
├── BinaryTypeDefinition
├── ListTypeDefinition
├── StructTypeDefinition
├── MapTypeDefinition
└── UnknownTypeDefinition

StructTypeDefinition
└── fields: tuple[StructFieldDefinition, ...]

StructFieldDefinition
├── name
├── data_type: TypeDefinition
└── nullable
~~~

---

# 8. Immutability rule

All declarative definition values SHOULD use immutable value semantics.

Preferred implementation style:

~~~python
@dataclass(frozen=True, slots=True)
~~~

Rationale:

- authored intent must not change during compilation;
- validation should operate on stable input;
- equality should be deterministic;
- nested definitions become safe to reuse;
- accidental parser mutation is prevented;
- future fingerprinting remains possible.

---

# 9. SchemaDocument

SchemaDocument is the format-neutral root of one declarative schema document.

Proposed definition:

~~~python
@dataclass(frozen=True, slots=True)
class SchemaDocument:
    version: int
    schemas: tuple[SchemaDefinition, ...]
~~~

Responsibilities:

- preserve declarative language version;
- preserve schema definition order;
- provide one normalized representation for single- and multi-schema authoring;
- act as the input boundary for document-level validation.

It MUST NOT preserve YAML AST nodes.

---

# 10. SchemaDocument.version

version identifies the declarative language version.

For V1:

~~~text
version = 1
~~~

The value MUST be an integer.

SchemaDocument itself MAY enforce basic type validity.

Version support policy belongs to the validator/compiler boundary.

---

# 11. SchemaDocument.schemas

schemas is an ordered tuple of SchemaDefinition values.

The tuple preserves declaration order.

Conceptually:

~~~python
SchemaDocument(
    version=1,
    schemas=(
        SchemaDefinition(name="customers", ...),
        SchemaDefinition(name="orders", ...),
    ),
)
~~~

Duplicate schema names are invalid.

Whether the dataclass constructor rejects duplicates directly or the validator owns
that diagnostic is an implementation choice.

The public invariant is that validated SchemaDocument values have unique schema
names.

---

# 12. Single-schema normalization

A YAML document such as:

~~~yaml
version: 1

schema:
  name: customers
  fields: []
~~~

normalizes to:

~~~python
SchemaDocument(
    version=1,
    schemas=(
        SchemaDefinition(
            name="customers",
            fields=(),
        ),
    ),
)
~~~

No SingleSchemaDocument class is required.

---

# 13. Multi-schema normalization

A YAML document such as:

~~~yaml
version: 1

schemas:
  customers:
    fields: []

  orders:
    fields: []
~~~

normalizes to:

~~~python
SchemaDocument(
    version=1,
    schemas=(
        SchemaDefinition("customers", ()),
        SchemaDefinition("orders", ()),
    ),
)
~~~

The authoring distinction disappears after decoding.

---

# 14. SchemaDefinition

SchemaDefinition represents one named declarative schema.

Proposed definition:

~~~python
@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    name: str
    fields: tuple[FieldDefinition, ...]
~~~

Its name is declaration identity.

It is not part of canonical Schema state.

---

# 15. SchemaDefinition.name

name is REQUIRED.

It MUST:

- be a string;
- contain non-whitespace content;
- preserve exact case;
- remain stable across normalization.

The declarative name is used to address schemas in multi-schema results.

Example:

~~~python
compiled["customers"]
~~~

The compiler MUST NOT inject name into canonical Schema through hidden metadata.

---

# 16. SchemaDefinition.fields

fields is an ordered tuple.

Field order is semantically significant.

Example:

~~~python
SchemaDefinition(
    name="customers",
    fields=(
        FieldDefinition(...),
        FieldDefinition(...),
    ),
)
~~~

Validated definitions MUST not contain duplicate field names.

---

# 17. SchemaDefinition metadata boundary

Declarative V1 SchemaDefinition intentionally does NOT contain:

~~~text
description
metadata
owner
tags
quality rules
source
target
~~~

This avoids representing state that canonical Schema cannot preserve.

A future version MAY introduce a higher-level contract object.

---

# 18. FieldDefinition

FieldDefinition mirrors the canonical state that current Field can preserve.

Proposed definition:

~~~python
@dataclass(frozen=True, slots=True)
class FieldDefinition:
    name: str
    data_type: TypeDefinition
    nullable: bool = True
    description: str | None = None
~~~

Note the internal Python attribute SHOULD be called data_type rather than type.

This avoids shadowing Python's built-in type symbol and aligns with canonical Field.

YAML still uses:

~~~yaml
type: string
~~~

---

# 19. FieldDefinition.name

name MUST be a non-empty string.

Whitespace-only names are invalid.

The exact string is preserved.

The compiler maps:

~~~text
FieldDefinition.name
        ↓
Field.name
~~~

without normalization.

---

# 20. FieldDefinition.data_type

data_type MUST be a TypeDefinition.

The compiler resolves it recursively:

~~~text
FieldDefinition.data_type
        ↓
DeclarativeTypeResolver
        ↓
DataType
~~~

Raw strings such as:

~~~python
data_type="string"
~~~

SHOULD NOT be permitted in normalized definition objects.

The parser/decoder is responsible for converting author syntax into TypeDefinition.

---

# 21. FieldDefinition.nullable

nullable is a boolean.

Default:

~~~text
True
~~~

It maps directly to:

~~~text
Field.nullable
~~~

No coercion occurs at definition-model construction.

---

# 22. FieldDefinition.description

description is:

~~~text
str | None
~~~

When present, it MUST contain non-whitespace content.

It maps directly to:

~~~text
Field.description
~~~

The declarative YAML grammar represents absence through omission.

The normalized model represents absence as None.

This is one deliberate place where YAML omission and internal representation differ.

---

# 23. FieldDefinition to Field mapping

Canonical compilation is:

~~~python
Field(
    name=definition.name,
    data_type=type_resolver.resolve(definition.data_type),
    nullable=definition.nullable,
    description=definition.description,
)
~~~

The compiler MUST NOT add undeclared state.

---

# 24. TypeDefinition abstraction

TypeDefinition is the root abstraction for declarative logical type intent.

Conceptually:

~~~python
class TypeDefinition:
    ...
~~~

It SHOULD be a closed hierarchy.

Its variants correspond exactly to declarative V1 type semantics.

---

# 25. TypeDefinition design options

Two implementation strategies are acceptable.

## Option A — inheritance hierarchy

~~~text
TypeDefinition
├── StringTypeDefinition
├── IntegerTypeDefinition
└── ...
~~~

## Option B — tagged immutable values

~~~text
TypeDefinition(
    kind=...
    parameters=...
)
~~~

The preferred architecture is Option A because:

- constructors become explicit;
- impossible parameter combinations are harder to represent;
- pattern matching is clearer;
- static typing is stronger;
- recursive nested structures are easier to reason about.

---

# 26. Marker TypeDefinition

The preferred base type is a marker abstraction with no runtime behavior.

Conceptually:

~~~python
class TypeDefinition:
    __slots__ = ()
~~~

It MUST NOT expose engine behavior.

It MUST NOT resolve itself into DataType.

Resolution belongs to DeclarativeTypeResolver.

---

# 27. StringTypeDefinition

Proposed form:

~~~python
@dataclass(frozen=True, slots=True)
class StringTypeDefinition(TypeDefinition):
    pass
~~~

Maps to:

~~~python
StringType()
~~~

No parameters.

---

# 28. BooleanTypeDefinition

~~~python
@dataclass(frozen=True, slots=True)
class BooleanTypeDefinition(TypeDefinition):
    pass
~~~

Maps to:

~~~python
BooleanType()
~~~

---

# 29. IntegerTypeDefinition

Normalized integer definitions SHOULD store semantic parameters rather than author
alias text.

Proposed form:

~~~python
@dataclass(frozen=True, slots=True)
class IntegerTypeDefinition(TypeDefinition):
    bits: int = 64
    signed: bool = True
~~~

Examples:

~~~text
int8
  → IntegerTypeDefinition(bits=8, signed=True)

uint32
  → IntegerTypeDefinition(bits=32, signed=False)

integer alias
  → IntegerTypeDefinition(bits=64, signed=True)
~~~

The definition model therefore forgets which author alias was used.

This is intentional.

---

# 30. FloatTypeDefinition

Proposed:

~~~python
@dataclass(frozen=True, slots=True)
class FloatTypeDefinition(TypeDefinition):
    bits: int = 64
~~~

Examples:

~~~text
float32
  → FloatTypeDefinition(bits=32)

float64
  → FloatTypeDefinition(bits=64)

float alias
  → FloatTypeDefinition(bits=64)
~~~

Alias spelling is not retained.

---

# 31. DecimalTypeDefinition

Proposed:

~~~python
@dataclass(frozen=True, slots=True)
class DecimalTypeDefinition(TypeDefinition):
    precision: int
    scale: int
~~~

It MUST preserve both values exactly.

It maps to:

~~~python
DecimalType(
    precision=precision,
    scale=scale,
)
~~~

---

# 32. BinaryTypeDefinition

~~~python
@dataclass(frozen=True, slots=True)
class BinaryTypeDefinition(TypeDefinition):
    pass
~~~

Maps to BinaryType.

---

# 33. DateTypeDefinition

~~~python
@dataclass(frozen=True, slots=True)
class DateTypeDefinition(TypeDefinition):
    pass
~~~

Maps to DateType.

---

# 34. TimeTypeDefinition

Proposed:

~~~python
@dataclass(frozen=True, slots=True)
class TimeTypeDefinition(TypeDefinition):
    unit: str = "us"
~~~

Short-form YAML:

~~~yaml
type: time
~~~

and structured YAML:

~~~yaml
type:
  time:
    unit: us
~~~

normalize to the same value.

---

# 35. TimestampTypeDefinition

Proposed:

~~~python
@dataclass(frozen=True, slots=True)
class TimestampTypeDefinition(TypeDefinition):
    unit: str = "us"
    timezone: str | None = None
~~~

Examples:

~~~text
timestamp
  → TimestampTypeDefinition(unit="us", timezone=None)

timestamp { unit: ns }
  → TimestampTypeDefinition(unit="ns", timezone=None)

timestamp { unit: us, timezone: UTC }
  → TimestampTypeDefinition(unit="us", timezone="UTC")
~~~

---

# 36. DurationTypeDefinition

Proposed:

~~~python
@dataclass(frozen=True, slots=True)
class DurationTypeDefinition(TypeDefinition):
    unit: str = "us"
~~~

Maps directly to DurationType.

---

# 37. UnknownTypeDefinition

~~~python
@dataclass(frozen=True, slots=True)
class UnknownTypeDefinition(TypeDefinition):
    pass
~~~

It represents intentional unknown type semantics.

It MUST NOT represent parse failure.

---

# 38. ListTypeDefinition

Proposed:

~~~python
@dataclass(frozen=True, slots=True)
class ListTypeDefinition(TypeDefinition):
    element_type: TypeDefinition
    element_nullable: bool = True
~~~

YAML:

~~~yaml
type:
  list:
    element:
      type: string
    element_nullable: false
~~~

normalizes to:

~~~python
ListTypeDefinition(
    element_type=StringTypeDefinition(),
    element_nullable=False,
)
~~~

---

# 39. ListTypeDefinition naming

The internal attribute SHOULD be:

~~~text
element_type
~~~

rather than:

~~~text
element
~~~

because it represents semantic content after parsing.

YAML-specific naming belongs to the decoder/emitter.

---

# 40. StructFieldDefinition

Nested struct fields require their own definition value because canonical StructField
differs from top-level Field.

Proposed:

~~~python
@dataclass(frozen=True, slots=True)
class StructFieldDefinition:
    name: str
    data_type: TypeDefinition
    nullable: bool = True
~~~

It intentionally has no description.

---

# 41. Why StructFieldDefinition is separate

Top-level FieldDefinition contains:

~~~text
name
data_type
nullable
description
~~~

StructFieldDefinition contains:

~~~text
name
data_type
nullable
~~~

Using FieldDefinition for nested struct fields would falsely imply support for nested
descriptions that canonical StructField cannot preserve.

Separate types make the round-trip constraint visible in the model.

---

# 42. StructTypeDefinition

Proposed:

~~~python
@dataclass(frozen=True, slots=True)
class StructTypeDefinition(TypeDefinition):
    fields: tuple[StructFieldDefinition, ...]
~~~

Field order MUST be preserved.

Validated instances MUST have unique field names.

---

# 43. MapTypeDefinition

Proposed:

~~~python
@dataclass(frozen=True, slots=True)
class MapTypeDefinition(TypeDefinition):
    key_type: TypeDefinition
    value_type: TypeDefinition
    value_nullable: bool = True
~~~

YAML names:

~~~text
key
value
value_nullable
~~~

normalize to semantic attributes:

~~~text
key_type
value_type
value_nullable
~~~

---

# 44. Complete proposed Python model

The target model can be expressed conceptually as:

~~~python
from dataclasses import dataclass


class TypeDefinition:
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class StringTypeDefinition(TypeDefinition):
    pass


@dataclass(frozen=True, slots=True)
class BooleanTypeDefinition(TypeDefinition):
    pass


@dataclass(frozen=True, slots=True)
class IntegerTypeDefinition(TypeDefinition):
    bits: int = 64
    signed: bool = True


@dataclass(frozen=True, slots=True)
class FloatTypeDefinition(TypeDefinition):
    bits: int = 64


@dataclass(frozen=True, slots=True)
class DecimalTypeDefinition(TypeDefinition):
    precision: int
    scale: int


@dataclass(frozen=True, slots=True)
class BinaryTypeDefinition(TypeDefinition):
    pass


@dataclass(frozen=True, slots=True)
class DateTypeDefinition(TypeDefinition):
    pass


@dataclass(frozen=True, slots=True)
class TimeTypeDefinition(TypeDefinition):
    unit: str = "us"


@dataclass(frozen=True, slots=True)
class TimestampTypeDefinition(TypeDefinition):
    unit: str = "us"
    timezone: str | None = None


@dataclass(frozen=True, slots=True)
class DurationTypeDefinition(TypeDefinition):
    unit: str = "us"


@dataclass(frozen=True, slots=True)
class UnknownTypeDefinition(TypeDefinition):
    pass


@dataclass(frozen=True, slots=True)
class ListTypeDefinition(TypeDefinition):
    element_type: TypeDefinition
    element_nullable: bool = True


@dataclass(frozen=True, slots=True)
class StructFieldDefinition:
    name: str
    data_type: TypeDefinition
    nullable: bool = True


@dataclass(frozen=True, slots=True)
class StructTypeDefinition(TypeDefinition):
    fields: tuple[StructFieldDefinition, ...]


@dataclass(frozen=True, slots=True)
class MapTypeDefinition(TypeDefinition):
    key_type: TypeDefinition
    value_type: TypeDefinition
    value_nullable: bool = True


@dataclass(frozen=True, slots=True)
class FieldDefinition:
    name: str
    data_type: TypeDefinition
    nullable: bool = True
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    name: str
    fields: tuple[FieldDefinition, ...]


@dataclass(frozen=True, slots=True)
class SchemaDocument:
    version: int
    schemas: tuple[SchemaDefinition, ...]
~~~

This code is illustrative but strongly recommended.

---

# 45. Constructor validation philosophy

Definition constructors MAY enforce low-level impossible-state checks.

Examples:

~~~text
name must be str
tuple fields must contain correct definition type
nullable must be bool
bits must be an allowed width
unit must be a supported unit
~~~

However, source-aware user diagnostics belong to SchemaDefinitionValidator.

The model should not become overloaded with formatting-oriented error logic.

---

# 46. Validation ownership

The preferred split is:

~~~text
DEFINITION CONSTRUCTORS
    enforce local Python invariants

DECLARATIVE VALIDATOR
    enforce document semantic rules
    produce rich source-aware diagnostics

DOMAIN CONSTRUCTORS
    enforce canonical PyTransformKit invariants
~~~

This three-level defense is intentional.

---

# 47. Local invariants

The definition model SHOULD reject impossible values when constructed directly.

Examples:

IntegerTypeDefinition:

~~~text
bits ∈ {8,16,32,64}
signed is bool
~~~

FloatTypeDefinition:

~~~text
bits ∈ {32,64}
~~~

Temporal definitions:

~~~text
unit ∈ {s,ms,us,ns}
~~~

DecimalTypeDefinition:

~~~text
precision > 0
scale >= 0
scale <= precision
~~~

---

# 48. Naming invariants

FieldDefinition and StructFieldDefinition names MUST be non-empty.

SchemaDefinition names MUST be non-empty.

Whitespace-only names MUST fail.

Duplicate names are collection-level invariants and SHOULD be diagnosed by the
validator.

---

# 49. Tuple invariants

Collections SHOULD be tuples, matching canonical Domain design.

The model MUST NOT silently convert arbitrary iterables inside constructors unless
that convention is consistently adopted.

Preferred use:

~~~python
fields=(
    FieldDefinition(...),
    FieldDefinition(...),
)
~~~

This mirrors Schema.fields.

---

# 50. Equality semantics

Dataclass value equality is preferred.

Therefore:

~~~python
IntegerTypeDefinition(bits=64, signed=True)
==
IntegerTypeDefinition(bits=64, signed=True)
~~~

and:

~~~python
SchemaDefinition(...)
==
SchemaDefinition(...)
~~~

when all values match.

Object identity MUST NOT participate in declarative semantics.

---

# 51. Hashability

Frozen definition values MAY be hashable where all contained values are hashable.

Hashability is useful for:

- testing;
- caching;
- future fingerprint preparation.

Public semantic fingerprints MUST NOT simply expose Python hash values because
Python hash values are not a stable cross-process contract.

---

# 52. Source information boundary

Source diagnostics SHOULD NOT be embedded directly into semantic definition equality.

For example, these two declarations:

~~~text
customers.yml → SchemaDefinition("customers", ...)
generated text → SchemaDefinition("customers", ...)
~~~

should be semantically equal when their declarations are equal.

Therefore source information should be modeled separately.

---

# 53. SourceContext

A separate diagnostic value is recommended.

Conceptually:

~~~python
@dataclass(frozen=True, slots=True)
class SourceContext:
    source: str | None = None
    line: int | None = None
    column: int | None = None
    object_path: str | None = None
~~~

This object provides diagnostics but does not alter schema semantics.

---

# 54. SourceContext is not Domain state

SourceContext MUST NOT be compiled into:

~~~text
Schema
Field
DataType
~~~

It MUST NOT affect Domain equality.

It MUST NOT affect canonical Schema fingerprints.

---

# 55. DefinitionLocation strategy

If precise source locations are needed per definition object, the architecture MAY
use a side mapping:

~~~text
DefinitionLocationIndex

definition identity/path
      ↓
SourceContext
~~~

rather than putting line and column on every semantic dataclass.

This avoids polluting value equality.

---

# 56. Object path

Every definition SHOULD have a deterministic logical path available to diagnostics.

Examples:

~~~text
schema
schema.fields[0]
schema.fields[0].type
schema.fields[2].type.decimal.precision
schemas.customers.fields[1]
~~~

The path is diagnostic metadata, not semantic state.

---

# 57. No YAML node retention

Definition objects MUST NOT retain objects such as:

~~~text
MappingNode
ScalarNode
SequenceNode
CommentedMap
CommentedSeq
parser event
token
anchor object
~~~

The parser adapter must translate them into format-neutral definition values.

---

# 58. No parser dependency

The following import direction is prohibited:

~~~text
application/declarative/model.py
        ↓
yaml
~~~

The model must remain usable independently of YAML.

This keeps future JSON/TOML authoring adapters possible.

---

# 59. No filesystem dependency

The model MUST NOT accept Path as semantic state merely because YAML was loaded from
a file.

Filesystem origin belongs to SourceContext.

---

# 60. No engine dependency

The model MUST NOT import:

~~~text
pandas
polars
pyarrow
duckdb
~~~

No TypeDefinition may wrap an engine-native dtype.

---

# 61. No canonical wire coupling

Definition objects are not canonical serialization contracts.

They SHOULD NOT receive existing wire contract IDs.

They MAY later receive their own serialization if there is a demonstrated need.

---

# 62. Definition model lifecycle

The expected lifecycle is short:

~~~text
parse
 ↓
SchemaDocument
 ↓
validate
 ↓
compile
 ↓
Schema
~~~

Definition objects may also appear during export:

~~~text
Schema
 ↓
export definition
 ↓
SchemaDocument
 ↓
emit YAML
~~~

They are not runtime execution state.

---

# 63. Validated-definition concept

The architecture MAY choose one of two strategies.

## Strategy A — one model + validator

~~~text
SchemaDefinition
      ↓ validate
same SchemaDefinition
~~~

## Strategy B — raw and validated types

~~~text
RawSchemaDefinition
      ↓ validate
ValidatedSchemaDefinition
~~~

V1 SHOULD prefer Strategy A unless static guarantees justify the additional model
complexity.

The strict decoder already prevents many malformed states.

---

# 64. No RawYamlDefinition model

The architecture SHOULD NOT create a large hierarchy mirroring raw YAML nodes.

The pipeline should remain:

~~~text
YAML parser values
      ↓ strict decoder
SchemaDocument
~~~

not:

~~~text
YAML
 ↓
RawYamlDocument
 ↓
RawYamlSchema
 ↓
RawYamlField
 ↓
...
~~~

unless implementation evidence shows it is necessary.

---

# 65. Compiler boundary

Only the compiler maps definition values into canonical Domain objects.

Conceptually:

~~~text
SchemaDefinitionCompiler
├── DeclarativeTypeResolver
└── Field construction
~~~

No TypeDefinition should expose:

~~~python
to_domain()
~~~

as a required method.

This preserves separation of data and application service behavior.

---

# 66. Why no to_domain methods

This design is discouraged:

~~~python
definition.to_domain()
~~~

because it distributes compilation responsibility across every definition class.

Preferred:

~~~python
compiler.compile(definition)
~~~

and:

~~~python
type_resolver.resolve(type_definition)
~~~

Benefits:

- centralized mapping policy;
- easier testing;
- easier diagnostics;
- cleaner immutable value objects;
- no hidden dependency on Domain constructors from every definition class.

---

# 67. Export boundary

The reverse conversion is also service-owned.

Preferred:

~~~python
type_exporter.export(data_type)
schema_exporter.export(schema, name="customers")
~~~

not:

~~~python
schema.to_declarative()
data_type.to_yaml()
~~~

---

# 68. Normalization boundary

Authoring aliases are normalized before or during definition construction.

For example:

~~~yaml
type: integer
~~~

and:

~~~yaml
type: int64
~~~

both become:

~~~python
IntegerTypeDefinition(
    bits=64,
    signed=True,
)
~~~

Therefore alias choice does not survive into semantic definition equality.

---

# 69. Short-form normalization

These:

~~~yaml
type: timestamp
~~~

and:

~~~yaml
type:
  timestamp:
    unit: us
~~~

normalize to:

~~~python
TimestampTypeDefinition(
    unit="us",
    timezone=None,
)
~~~

if the structured form is accepted with default-equivalent parameters.

Canonical emission chooses the short form.

---

# 70. Nullability normalization

Omitted top-level nullable:

~~~yaml
- name: email
  type: string
~~~

normalizes to:

~~~python
FieldDefinition(
    name="email",
    data_type=StringTypeDefinition(),
    nullable=True,
)
~~~

The definition model contains the semantic default explicitly.

---

# 71. Description normalization

Omitted description normalizes to:

~~~text
description = None
~~~

Explicit YAML null remains invalid at grammar level.

This means:

~~~text
omission in authoring
!=
explicit null in syntax
~~~

while normalized semantic state uses None.

---

# 72. Schema order semantics

SchemaDocument preserves schema declaration order.

However, compiled multi-schema lookup may expose a Mapping[str, Schema].

The mapping implementation SHOULD preserve deterministic order.

A standard insertion-ordered dict is acceptable.

---

# 73. Field order semantics

SchemaDefinition.fields preserves field order exactly.

No validator, compiler or exporter may alphabetically reorder fields.

---

# 74. Struct field order semantics

StructTypeDefinition.fields also preserves order exactly.

No recursive operation may reorder nested fields.

---

# 75. Conversion table

| Definition model | Canonical Domain |
| --- | --- |
| SchemaDefinition | Schema |
| FieldDefinition | Field |
| StringTypeDefinition | StringType |
| BooleanTypeDefinition | BooleanType |
| IntegerTypeDefinition | IntegerType |
| FloatTypeDefinition | FloatType |
| DecimalTypeDefinition | DecimalType |
| BinaryTypeDefinition | BinaryType |
| DateTypeDefinition | DateType |
| TimeTypeDefinition | TimeType |
| TimestampTypeDefinition | TimestampType |
| DurationTypeDefinition | DurationType |
| UnknownTypeDefinition | UnknownType |
| ListTypeDefinition | ListType |
| StructTypeDefinition | StructType |
| StructFieldDefinition | StructField |
| MapTypeDefinition | MapType |
| SchemaDocument | no direct canonical Domain equivalent |

---

# 76. SchemaDocument has no Domain counterpart

SchemaDocument is a declarative authoring envelope.

It contains:

~~~text
language version
one or more named schema definitions
~~~

The canonical Domain has no equivalent object because Schema itself is independent of
authoring-document concerns.

This difference is intentional.

---

# 77. Schema name has no Domain counterpart

SchemaDefinition.name is consumed as declaration identity.

Example compilation result:

~~~python
{
    "customers": Schema(...),
    "orders": Schema(...),
}
~~~

The name remains in the surrounding mapping.

It is not stored inside Schema.

---

# 78. Round-trip implications

Exporting a canonical Schema requires an explicit name:

~~~python
exporter.export(
    schema,
    name="customers",
)
~~~

This produces:

~~~python
SchemaDefinition(
    name="customers",
    fields=...,
)
~~~

Without an explicit name, the exporter cannot reconstruct one from Schema.

---

# 79. No hidden metadata channel

The implementation MUST NOT attach declaration name through:

- private Schema attributes;
- object annotations;
- global registries;
- weak references;
- hidden metadata dicts;
- process-local caches.

Name ownership remains explicit.

---

# 80. Future extensibility

A future higher-level object could represent:

~~~text
SchemaResource
├── name
├── schema
├── description
├── metadata
└── governance information
~~~

If introduced, that would be a separate architectural decision.

Declarative V1 does not anticipate it through hidden fields.

---

# 81. Definition model extensibility

The model can evolve by adding new TypeDefinition variants when canonical Domain
types evolve.

However, adding semantic properties to existing definitions requires declarative
language compatibility analysis.

For example, adding:

~~~text
FieldDefinition.metadata
~~~

would be invalid unless canonical Field or another explicit contract can preserve it.

---

# 82. Exhaustiveness checks

Type resolver and exporter implementations SHOULD enforce exhaustiveness.

If a new TypeDefinition subclass exists but the resolver does not handle it, tests
must fail.

If a new canonical DataType subclass exists but the exporter does not handle it,
export must fail explicitly.

Silent fallback is prohibited.

---

# 83. Pattern matching

Python structural pattern matching MAY be used internally.

Conceptually:

~~~python
match definition:
    case StringTypeDefinition():
        ...
    case IntegerTypeDefinition(bits=bits, signed=signed):
        ...
    case DecimalTypeDefinition(precision=precision, scale=scale):
        ...
~~~

The exact implementation is not normative.

Exhaustive explicit dispatch is the goal.

---

# 84. Definition factory helpers

Internal factories MAY improve decoder readability.

Examples:

~~~text
parse_scalar_type(...)
parse_structured_type(...)
build_field_definition(...)
build_schema_definition(...)
~~~

Factories MUST return normalized definition values.

They MUST NOT return canonical Domain objects.

---

# 85. Public exposure

Definition classes SHOULD NOT automatically be exported from the PyTransformKit
package root.

Their public status will be decided in document 38.

Likely policy:

~~~text
high-level declarative API        public
definition model                 advanced/provisional or internal
compiler internals               internal
YAML adapter internals           internal
~~~

---

# 86. Why not expose parser-native dictionaries

Returning plain dictionaries from the parser would create weak contracts.

For example:

~~~python
{
    "name": "customers",
    "fields": [...]
}
~~~

does not provide:

- static semantics;
- immutable value guarantees;
- exhaustive type modeling;
- clear resolver boundaries;
- strong validation ownership.

Typed definition values are therefore preferred.

---

# 87. Why not compile directly from dictionaries

This shortcut:

~~~text
YAML
 ↓
dict
 ↓
Schema
~~~

would combine:

- parsing;
- validation;
- type resolution;
- Domain construction.

That makes diagnostics and future format support harder.

The explicit definition model keeps these concerns separated.

---

# 88. Model acceptance criteria

The declarative definition model is acceptable when:

1. no model class imports YAML;
2. no model class imports physical engines;
3. all values are immutable;
4. collection order is preserved;
5. aliases normalize to one semantic state;
6. definition equality is value-based;
7. source location does not affect semantic equality;
8. every V1 type maps to one TypeDefinition variant;
9. every TypeDefinition variant maps to a canonical DataType;
10. nested structures are recursively representable;
11. no unsupported metadata can be silently represented and lost;
12. SchemaDefinition.name remains outside canonical Schema state;
13. StructFieldDefinition does not pretend to support description;
14. definition values contain no parser-native nodes;
15. the compiler is the explicit Domain conversion boundary.

---

# 89. Suggested tests

Tests SHOULD verify:

~~~text
SchemaDocument immutability
SchemaDefinition immutability
FieldDefinition immutability
all TypeDefinition immutability
tuple enforcement
value equality
field ordering
struct field ordering
duplicate-validation integration
invalid bits rejection
invalid temporal unit rejection
invalid decimal rejection
alias normalization
nested definition equality
source context excluded from semantics
compiler mapping equality
exporter inverse mapping equality
~~~

---

# 90. Architecture invariant

The intended dependency direction remains:

~~~text
YAML adapter
    ↓
SchemaDocument / definitions
    ↓
validator / resolver / compiler
    ↓
canonical Domain
~~~

Never:

~~~text
canonical Domain
    ↓
SchemaDefinition
    ↓
YAML
~~~

as a Domain dependency.

Reverse export is implemented by Application services, not by Domain imports.

---

# 91. Decisions frozen by this document

## DEC-MODEL-01

SchemaDocument is the normalized declarative document root.

## DEC-MODEL-02

Single- and multi-schema authoring normalize to the same SchemaDocument.

## DEC-MODEL-03

SchemaDefinition has name and ordered fields only in V1.

## DEC-MODEL-04

FieldDefinition mirrors canonical Field state.

## DEC-MODEL-05

StructFieldDefinition is separate from FieldDefinition.

## DEC-MODEL-06

TypeDefinition is a closed application-layer hierarchy.

## DEC-MODEL-07

Definition objects are immutable value objects.

## DEC-MODEL-08

Source diagnostics are separate from semantic equality.

## DEC-MODEL-09

Aliases are normalized away before semantic compilation.

## DEC-MODEL-10

Definition objects contain no YAML/parser-specific nodes.

## DEC-MODEL-11

Definition objects expose no engine-native values.

## DEC-MODEL-12

Compilation behavior lives in services, not on definition values.

## DEC-MODEL-13

SchemaDefinition.name is not injected into Schema.

## DEC-MODEL-14

No hidden metadata channel is allowed.

---

# 92. Relationship with canonical Domain

The relationship can be summarized as:

~~~text
DECLARATIVE MODEL                  CANONICAL DOMAIN

SchemaDocument
   │
   └── SchemaDefinition ─────────────→ Schema
          │
          └── FieldDefinition ───────→ Field
                 │
                 └── TypeDefinition ─→ DataType
                        │
                        └── StructFieldDefinition
                                      ↓
                                  StructField
~~~

The declarative model exists before compilation.

The canonical Domain exists after compilation.

---

# 93. Next document

The next document specifies the services that operate on this model:

~~~text
34_PYTRANSFORMKIT_SCHEMA_LOADER_COMPILER_AND_EXPORTER_SPEC.md
~~~

It must freeze:

~~~text
SchemaDocumentParser port
YamlSchemaParser adapter
SchemaDefinitionValidator
DeclarativeTypeResolver
SchemaDefinitionCompiler
DeclarativeTypeExporter
SchemaDefinitionExporter
YamlSchemaEmitter
load_schema / load_schemas flow
dump_schema / dumps_schema flow
filesystem and in-memory boundaries
~~~

---

# 94. Final summary

The declarative definition model is intentionally small and explicit.

It is neither raw YAML nor canonical Domain.

It sits between the two:

~~~text
YAML
 ↓
strict decoding
 ↓
SchemaDocument
 ↓
SchemaDefinition
 ↓
FieldDefinition
 ↓
TypeDefinition
 ↓
compiler
 ↓
Schema / Field / DataType
~~~

Its purpose is to provide a stable place for authoring semantics, validation and
diagnostics without contaminating the canonical Domain.

The governing rule is:

> **Definitions describe the Domain; they do not become the Domain.**
