# 30 — PyTransformKit Declarative Schema — Architecture

> **Document status:** DRAFT  
> **Depends on:** 28_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_EXPRESSION_DU_BESOIN.md  
> **Depends on:** 29_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_REQUIREMENTS_ANALYSIS.md  
> **Architectural baseline:** PyTransformKit V1 Target Architecture  
> **Scope:** Declarative schema authoring  
> **Primary format:** YAML  
> **Canonical Domain model:** Schema / Field / DataType  
> **Primary objective:** Add declarative authoring without creating a second schema semantics

---

# 1. Purpose

This document defines the target architecture for declarative schema authoring in
PyTransformKit.

It answers the central architectural question:

> Where should YAML parsing, declarative definitions, validation, type resolution,
> compilation and export live without contaminating the stable V1 Domain?

The architecture MUST preserve the existing PyTransformKit dependency direction:

~~~text
AUTHORING
    ↓
APPLICATION
    ↓
DOMAIN

INFRASTRUCTURE
    ────────┘
    depends inward
~~~

The Domain remains engine-neutral and format-neutral.

YAML is treated as an infrastructure concern.

---

# 2. Existing V1 architecture

PyTransformKit V1 already separates:

~~~text
AUTHORING
    user-facing construction and ergonomics

DOMAIN
    immutable engine-neutral semantic model

APPLICATION / PLANNING
    validation, compilation, optimization, capability analysis

RUNTIME
    execution identity, bindings, engine coordination, results

INFRASTRUCTURE / ADAPTERS
    engines, physical I/O, plugins and telemetry sinks
~~~

Declarative schema support MUST integrate into this model rather than introduce a
parallel architecture.

The existing canonical schema objects live under:

~~~text
src/pytransformkit/domain/data/
├── schema.py
├── field.py
├── data_types.py
└── ...
~~~

and currently expose the following essential semantics:

~~~text
Schema
└── fields: tuple[Field, ...]

Field
├── name: str
├── data_type: DataType
├── nullable: bool
└── description: str | None
~~~

The DataType hierarchy already owns primitive, parameterized and nested logical
types.

---

# 3. Architectural decision

The declarative-schema architecture SHALL use a four-stage pipeline:

~~~text
SOURCE TEXT
    ↓
FORMAT ADAPTER
    ↓
DECLARATIVE DEFINITION MODEL
    ↓
VALIDATION + TYPE RESOLUTION
    ↓
COMPILER
    ↓
CANONICAL DOMAIN SCHEMA
~~~

For YAML:

~~~text
customers.yml
    ↓
YamlSchemaParser
    ↓
SchemaDocument
    ↓
SchemaDefinitionValidator
    ↓
SchemaDefinitionCompiler
    ↓
Schema
~~~

The reverse direction is:

~~~text
Schema
    ↓
SchemaDefinitionExporter
    ↓
SchemaDocument
    ↓
YamlSchemaEmitter
    ↓
YAML text
~~~

This separation is normative.

---

# 4. Core architectural invariant

The entire feature is governed by one invariant:

~~~text
One schema semantics
Multiple authoring surfaces
~~~

Python authoring and YAML authoring converge on the same Domain:

~~~text
Python API ───────────────────────┐
                                 │
YAML                             │
 ↓                               │
SchemaDocument                   │
 ↓                               │
SchemaDefinitionCompiler         │
 └───────────────────────────────┤
                                 ▼
                              Schema
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
             Planning         Runtime         Engines
~~~

There is no YAML-specific runtime schema.

---

# 5. Layer ownership

The architecture assigns responsibilities as follows.

| Concern | Layer |
| --- | --- |
| Schema / Field / DataType | Domain |
| SchemaDocument | Application / declarative |
| SchemaDefinition | Application / declarative |
| FieldDefinition | Application / declarative |
| TypeDefinition | Application / declarative |
| Structural validation | Application / declarative |
| Type resolution | Application / declarative |
| Definition → Schema compilation | Application / declarative |
| Schema → definition export | Application / declarative |
| YAML parsing | Infrastructure |
| YAML emission | Infrastructure |
| Filesystem loading | Infrastructure / facade |
| Public convenience API | Authoring facade |
| Engine dtype conversion | Existing engine adapters |
| Canonical wire serialization | Existing serialization package |

---

# 6. Target package structure

The recommended target structure is:

~~~text
src/pytransformkit/
├── declarative/
│   ├── __init__.py
│   └── api.py
│
├── application/
│   ├── declarative/
│   │   ├── __init__.py
│   │   ├── model.py
│   │   ├── validation.py
│   │   ├── type_resolution.py
│   │   ├── compiler.py
│   │   └── exporter.py
│   │
│   └── ports/
│       └── declarative.py
│
├── domain/
│   └── data/
│       ├── schema.py
│       ├── field.py
│       └── data_types.py
│
├── infrastructure/
│   └── declarative/
│       ├── __init__.py
│       └── yaml.py
│
├── errors/
│   └── declarative.py
│
└── serialization/
    └── existing V1 codecs unchanged
~~~

Exact filenames MAY change during implementation.

The responsibility boundaries MUST NOT.

---

# 7. Why a dedicated declarative namespace

The public capability SHOULD be discoverable without expanding the package root.

Preferred direction:

~~~python
from pytransformkit.declarative import load_schema
~~~

rather than adding every loader and exporter to:

~~~python
from pytransformkit import ...
~~~

The root V1 API remains curated.

The declarative feature is an authoring capability, not a new foundational Domain
primitive.

---

# 8. Definition model

The declarative layer requires an intermediate representation.

Candidate objects are:

~~~text
SchemaDocument
SchemaDefinition
FieldDefinition
TypeDefinition
PrimitiveTypeDefinition
ParameterizedTypeDefinition
ListTypeDefinition
StructTypeDefinition
MapTypeDefinition
~~~

These objects exist to represent author intent before Domain compilation.

They are NOT:

- runtime objects;
- wire contracts;
- physical engine schemas;
- replacements for Schema;
- replacements for DataType.

---

# 9. SchemaDocument

SchemaDocument is the root of one parsed declarative document.

Conceptually:

~~~python
@dataclass(frozen=True, slots=True)
class SchemaDocument:
    version: int
    schemas: tuple[SchemaDefinition, ...]
~~~

Its responsibilities are limited to:

- document language version;
- ordered schema definitions;
- source-independent declarative structure.

It MUST NOT contain YAML parser nodes.

It MUST NOT expose PyYAML-specific objects.

It MUST NOT execute compilation automatically.

---

# 10. SchemaDefinition

SchemaDefinition represents one named declarative schema before compilation.

Conceptually:

~~~python
@dataclass(frozen=True, slots=True)
class SchemaDefinition:
    name: str
    fields: tuple[FieldDefinition, ...]
~~~

A name exists at the declaration layer because multi-schema documents require an
identity.

The existing Domain Schema has no name property.

Therefore:

~~~text
declaration identity != Domain Schema state
~~~

The schema name is used to select and address compiled schemas:

~~~python
schemas["customers"]
~~~

It is not injected into Schema through an undocumented side channel.

---

# 11. Schema-level description decision

The current Domain Schema contains only ordered fields.

It does not expose:

~~~text
name
description
metadata
~~~

Adding such attributes would alter the stable Schema contract.

Therefore the first declarative implementation MUST NOT silently pretend that
schema-level descriptions can round-trip through Schema.

The initial architecture makes the following decision:

> Schema-level descriptive metadata is not part of the first canonical
> declarative-to-Schema round-trip contract.

Possible future solutions include:

1. a versioned Domain extension;
2. a separate dataset/catalog metadata model;
3. a higher-level schema resource wrapper.

Until one is deliberately selected, general schema-level metadata MUST NOT be
silently discarded.

The normative YAML specification MUST either reject such properties or explicitly
classify them as non-compilable definition metadata outside the canonical
round-trip path.

---

# 12. FieldDefinition

FieldDefinition mirrors only authoring semantics that can be compiled safely.

Conceptually:

~~~python
@dataclass(frozen=True, slots=True)
class FieldDefinition:
    name: str
    type: TypeDefinition
    nullable: bool = True
    description: str | None = None
~~~

This aligns directly with the existing Domain Field:

~~~text
Field
├── name
├── data_type
├── nullable
└── description
~~~

No general metadata mapping is assumed because the current Field Domain object does
not expose arbitrary metadata.

---

# 13. General field metadata decision

The current Domain Field does not contain a generic metadata mapping.

Therefore a YAML declaration such as:

~~~yaml
metadata:
  classification: pii
~~~

cannot currently be guaranteed to survive:

~~~text
YAML → Schema → YAML
~~~

without modifying the Domain or introducing a sidecar contract.

The initial architecture therefore MUST NOT silently drop generic field metadata.

The first implementation SHOULD restrict the canonical round-trip to properties the
Domain can actually preserve:

~~~text
name
type
nullable
description
~~~

General governance metadata belongs to a later explicitly versioned extension.

---

# 14. TypeDefinition

TypeDefinition is an authoring representation of logical type intent.

It exists because raw YAML structures are not appropriate inputs to the Domain.

Conceptually:

~~~text
TypeDefinition
├── PrimitiveTypeDefinition
├── IntegerTypeDefinition
├── FloatTypeDefinition
├── DecimalTypeDefinition
├── TimeTypeDefinition
├── TimestampTypeDefinition
├── DurationTypeDefinition
├── ListTypeDefinition
├── StructTypeDefinition
├── MapTypeDefinition
└── UnknownTypeDefinition
~~~

TypeDefinition is not a second logical type system.

Its only valid destination is the existing DataType hierarchy.

---

# 15. Type resolution

A dedicated resolver converts TypeDefinition to DataType.

~~~text
TypeDefinition
      ↓
DeclarativeTypeResolver
      ↓
DataType
~~~

The resolver owns the closed mapping between authoring vocabulary and Domain types.

Example:

~~~text
"string"     → StringType()
"boolean"    → BooleanType()
"integer"    → IntegerType(...)
"decimal"    → DecimalType(...)
"timestamp"  → TimestampType(...)
"list"       → ListType(...)
"struct"     → StructType(...)
"map"        → MapType(...)
"unknown"    → UnknownType()
~~~

The exact vocabulary is frozen by document 32.

---

# 16. Closed type registry

The type resolver MUST be closed-world.

It MAY internally use a mapping such as:

~~~python
TYPE_FACTORIES = {
    "string": ...,
    "boolean": ...,
    "integer": ...,
    "float": ...,
    "decimal": ...,
    "date": ...,
    "time": ...,
    "timestamp": ...,
    "duration": ...,
    "binary": ...,
    "list": ...,
    "struct": ...,
    "map": ...,
    "unknown": ...,
}
~~~

It MUST NOT perform:

~~~python
importlib.import_module(user_value)
eval(user_value)
exec(user_value)
~~~

Type resolution is semantic mapping, not dynamic Python loading.

---

# 17. SchemaDefinitionValidator

Validation belongs before Domain construction.

The validator receives definition objects:

~~~text
SchemaDocument
      ↓
SchemaDefinitionValidator
      ↓
validated definition model
~~~

It checks declarative semantics that should not be delegated to the Domain.

Examples include:

- supported document version;
- unique schema names;
- unique field names;
- strict scalar types;
- known properties;
- valid type-definition shape;
- nested-type consistency;
- declaration-level naming rules.

The Domain remains the final invariant boundary for Domain rules.

---

# 18. Two validation boundaries

Validation intentionally occurs twice.

~~~text
Declarative validation
        ↓
Domain construction
        ↓
Domain invariant validation
~~~

Declarative validation provides:

- source-aware diagnostics;
- object paths;
- user-friendly error messages;
- grammar validation.

Domain validation provides:

- canonical invariant enforcement;
- protection for all construction paths, including direct Python use.

The declarative layer MUST NOT weaken or bypass Domain validation.

---

# 19. SchemaDefinitionCompiler

SchemaDefinitionCompiler is the main application service connecting declarative
authoring to the Domain.

Conceptually:

~~~python
class SchemaDefinitionCompiler:
    def compile(
        self,
        definition: SchemaDefinition,
    ) -> Schema:
        ...
~~~

Its responsibilities are:

1. receive a validated SchemaDefinition;
2. resolve every TypeDefinition;
3. construct canonical Field values;
4. construct the canonical Schema;
5. translate unexpected construction failures into declarative diagnostics when
   appropriate.

It MUST NOT:

- parse YAML;
- access files;
- access the network;
- inspect physical engines;
- activate plugins;
- serialize runtime contracts.

---

# 20. Multi-schema compilation

A document compiler or facade MAY compile a full document:

~~~text
SchemaDocument
      ↓
compile_document(...)
      ↓
Mapping[str, Schema]
~~~

Example result:

~~~python
{
    "customers": Schema(...),
    "orders": Schema(...),
}
~~~

The mapping key preserves declaration identity.

Schema itself remains unchanged.

---

# 21. Declarative parser port

The Application layer SHOULD define a small format-neutral port.

Conceptually:

~~~python
class SchemaDocumentParser(Protocol):
    def parse(self, text: str, *, source: str | None = None) -> SchemaDocument:
        ...
~~~

A corresponding emitter port MAY be defined:

~~~python
class SchemaDocumentEmitter(Protocol):
    def emit(self, document: SchemaDocument) -> str:
        ...
~~~

These Protocols MUST NOT mention PyYAML.

---

# 22. YAML infrastructure adapter

YamlSchemaParser belongs to Infrastructure.

Its responsibility is:

~~~text
YAML text
    ↓
safe YAML parsing
    ↓
strict structural decoding
    ↓
SchemaDocument
~~~

It MAY depend on an optional YAML package.

It MUST NOT be imported by Domain modules.

It MUST NOT construct engine-native types.

---

# 23. Parser decomposition

The YAML adapter SHOULD conceptually separate:

~~~text
raw YAML text
     ↓
safe parser
     ↓
plain Python values
     ↓
strict document decoder
     ↓
SchemaDocument
~~~

This allows security policy to be enforced before semantic compilation.

Only safe built-in values should cross from raw parsing into decoding:

~~~text
dict
list
str
int
float
bool
None
~~~

Custom Python object constructors are forbidden.

---

# 24. YAML emitter

YamlSchemaEmitter performs the reverse format-specific transformation:

~~~text
SchemaDocument
      ↓
YamlSchemaEmitter
      ↓
YAML text
~~~

It owns:

- YAML formatting;
- indentation;
- scalar emission;
- key ordering policy;
- deterministic output conventions.

It does NOT own Domain semantics.

---

# 25. SchemaDefinitionExporter

A separate application service converts canonical Domain values into declarative
definitions.

~~~text
Schema
    ↓
SchemaDefinitionExporter
    ↓
SchemaDefinition
~~~

Conceptually:

~~~python
class SchemaDefinitionExporter:
    def export(
        self,
        schema: Schema,
        *,
        name: str,
    ) -> SchemaDefinition:
        ...
~~~

The name must be supplied because Domain Schema does not contain one.

This is an important boundary.

---

# 26. Full import flow

The complete loading path is:

~~~text
Path / text
    ↓
Declarative public facade
    ↓
YamlSchemaParser
    ↓
SchemaDocument
    ↓
SchemaDefinitionValidator
    ↓
SchemaDefinitionCompiler
    ↓
Schema / Mapping[str, Schema]
~~~

The Domain never sees YAML.

---

# 27. Full export flow

The complete export path is:

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
YAML text / file
~~~

The emitter never receives a Pandas, Polars, Arrow or DuckDB object.

---

# 28. Public facade

The public authoring facade SHOULD hide internal orchestration.

Candidate usage:

~~~python
from pytransformkit.declarative import load_schema

schema = load_schema("schemas/customers.yml")
~~~

For multi-schema documents:

~~~python
from pytransformkit.declarative import load_schemas

schemas = load_schemas("schemas/domain.yml")
~~~

For export:

~~~python
from pytransformkit.declarative import dump_schema

dump_schema(
    schema,
    "schemas/customers.yml",
    name="customers",
)
~~~

These names are illustrative until document 38 freezes the API.

---

# 29. In-memory API

The architecture MUST permit non-filesystem use.

Conceptually:

~~~python
schema = loads_schema(yaml_text)
~~~

and:

~~~python
yaml_text = dumps_schema(
    schema,
    name="customers",
)
~~~

Filesystem helpers should be thin wrappers around text-based primitives.

Preferred layering:

~~~text
load_schema(path)
    ↓ read text
loads_schema(text)
    ↓ parse/compile
Schema
~~~

and:

~~~text
dump_schema(path)
    ↓
dumps_schema(...)
    ↓
write text
~~~

---

# 30. Filesystem boundary

Filesystem access belongs outside the Domain and compiler.

The public facade MAY perform explicit file reads and writes.

The path is caller-supplied.

The implementation MUST NOT automatically scan project directories.

There is no implicit convention such as:

~~~text
./schemas/**
~~~

unless a future higher-level project feature explicitly introduces one.

---

# 31. Optional dependency architecture

YAML support SHOULD be packaged as an optional capability.

Recommended packaging direction:

~~~toml
[project.optional-dependencies]
yaml = [
    "<selected-yaml-parser>",
]
~~~

User installation:

~~~text
pip install "pytransformkit[yaml]"
~~~

Core import remains valid:

~~~python
import pytransformkit
~~~

without the YAML dependency installed.

This preserves PyTransformKit's lightweight engine-independent core.

---

# 32. Missing YAML dependency behavior

Importing the core MUST NOT import the YAML parser.

The YAML dependency should only be required when YAML-specific functionality is
invoked.

Conceptually:

~~~python
from pytransformkit.declarative import load_schema

load_schema("customers.yml")
~~~

without the optional parser installed should raise a controlled PyTransformKit
capability/dependency error.

It should not fail during:

~~~python
import pytransformkit
~~~

---

# 33. Dependency direction

The target dependency graph is:

~~~text
pytransformkit.declarative
      │
      ├───────────────┐
      ▼               ▼
application        infrastructure
declarative         declarative/yaml
      │               │
      └───────┬───────┘
              ▼
          domain/data
~~~

More precisely:

~~~text
Domain
  ↑
Application declarative
  ↑
Public authoring facade

Application ports
  ↑
Infrastructure YAML adapter
~~~

Infrastructure may depend on Application and Domain abstractions.

Domain MUST NOT depend on either.

---

# 34. Forbidden dependency graph

The following is prohibited:

~~~text
domain/data/schema.py
        ↓
PyYAML
        ↓
filesystem
~~~

Also prohibited:

~~~text
Schema.from_yaml(...)
    ↓
imports infrastructure YAML parser
~~~

if implementing that convenience method requires a Domain-to-Infrastructure
dependency.

---

# 35. Why Schema.from_yaml is not the primary API

A method such as:

~~~python
Schema.from_yaml("customers.yml")
~~~

looks convenient but places format knowledge on the Domain object.

That creates pressure toward:

~~~text
Schema.from_yaml
Schema.from_json
Schema.from_toml
Schema.to_yaml
Schema.to_json
...
~~~

and reverses the intended dependency direction.

The preferred model is:

~~~python
load_schema(...)
dump_schema(...)
~~~

or dedicated loader/exporter objects.

---

# 36. Relationship with existing serialization

PyTransformKit already has:

~~~text
src/pytransformkit/serialization/
├── canonical.py
├── codec.py
├── codecs.py
├── migrations.py
└── registry.py
~~~

The declarative-schema feature MUST NOT be implemented as an accidental extension
of the canonical wire codec system.

These concerns differ:

| Concern | Declarative schema | Canonical serialization |
| --- | --- | --- |
| Primary consumer | human author | software |
| Primary format | YAML | canonical versioned payload |
| Goal | authoring | interchange |
| Formatting | readability | deterministic contract |
| Comments | allowed but non-semantic | not relevant |
| Domain input | Schema | portable contract object |
| Version | declarative-language version | wire contract version |

The two systems MAY share semantic helpers.

They MUST NOT share contract identity accidentally.

---

# 37. Relationship with engine adapters

Declarative schemas stop at Domain DataType.

They MUST NOT map YAML directly to physical engine dtypes.

Forbidden:

~~~text
YAML "integer"
    ↓
pandas.Int64Dtype
~~~

Required:

~~~text
YAML "integer"
    ↓
IntegerType
    ↓
Pandas adapter / Polars adapter / Arrow adapter / DuckDB adapter
~~~

This preserves engine neutrality.

---

# 38. Relationship with Dataset

The initial feature compiles declarative schema definitions to Schema.

It does not automatically construct Dataset.

Future dataset declarations MAY reference schemas, but that is a separate feature.

The first implementation MUST NOT silently introduce:

~~~yaml
dataset:
  source: ...
  destination: ...
  refresh: ...
~~~

because those concerns cross into ingestion and orchestration boundaries.

---

# 39. Relationship with quality

Nullability is part of schema semantics and remains in scope.

General quality rules are not automatically part of declarative schema architecture.

This:

~~~yaml
nullable: false
~~~

is schema semantics.

This:

~~~yaml
tests:
  - unique
  - accepted_values:
      - active
      - inactive
~~~

is quality semantics and requires a separate explicit design decision.

The architecture reserves room for future composition but does not merge the
bounded contexts.

---

# 40. Relationship with governance metadata

The declarative authoring layer MAY eventually become useful for governance
metadata.

However, the current Domain cannot preserve arbitrary field metadata or
schema-level metadata.

Therefore governance enrichment MUST NOT be smuggled into V1 declarative schema
files with silent loss.

A future extension may introduce:

~~~text
SchemaResource
SchemaContract
DatasetContract
GovernanceMetadata
~~~

but these concepts are outside this initial architecture.

---

# 41. Error architecture

Declarative errors SHOULD live in a dedicated error module.

Recommended direction:

~~~text
errors/
├── schema.py
└── declarative.py
~~~

Potential hierarchy:

~~~text
PyTransformKitError
└── DeclarativeSchemaError
    ├── DeclarativeSchemaParseError
    ├── DeclarativeSchemaValidationError
    ├── DeclarativeSchemaVersionError
    ├── DeclarativeSchemaTypeError
    └── DeclarativeSchemaDependencyError
~~~

Exact names and PTK error codes are frozen in document 35.

---

# 42. Source diagnostics

Source identity is an Application-level diagnostic concern.

The parser/validator SHOULD be able to attach:

~~~text
source
line
column
object path
~~~

Example:

~~~text
schemas/customers.yml:14:9
schemas.customers.fields[2].type.decimal.precision
~~~

These details belong to diagnostics.

They MUST NOT be stored in canonical Schema semantics.

---

# 43. Strictness boundary

Strictness is distributed intentionally:

~~~text
YAML parser
    rejects unsafe YAML constructs

Document decoder
    rejects unknown keys and invalid shapes

Definition validator
    rejects declarative semantic violations

Type resolver
    rejects unknown/invalid type declarations

Domain constructors
    enforce canonical invariants
~~~

No layer assumes the next layer will repair malformed input.

---

# 44. Unknown keys

Unknown declarative properties MUST be rejected at the definition-decoding boundary.

Example:

~~~yaml
name: customer_id
type: integer
nulable: false
~~~

The decoder should report the unknown key before Schema construction.

This avoids typo-driven configuration drift.

---

# 45. Duplicate YAML keys

Duplicate YAML mapping keys MUST be rejected by the YAML infrastructure adapter.

Example:

~~~yaml
nullable: true
nullable: false
~~~

must never resolve through a last-value-wins parser policy.

This check occurs before definition compilation.

---

# 46. YAML feature subset

The architecture intentionally allows PyTransformKit to support a strict YAML
subset rather than every YAML feature.

The security policy will decide treatment of:

~~~text
anchors
aliases
merge keys
custom tags
multi-document streams
implicit timestamp scalars
implicit booleans
~~~

The application model MUST NOT depend on these YAML-specific features.

---

# 47. Document version routing

Document version selection occurs before semantic compilation.

~~~text
raw document
    ↓
version detection
    ↓
version-specific decoder
    ↓
SchemaDocument
~~~

Future support may look like:

~~~text
v1 decoder
v2 decoder
...
~~~

The compiler consumes normalized definition objects rather than branching
throughout the Domain by YAML version.

---

# 48. Version independence

Three version domains remain separate:

~~~text
PyTransformKit package version
Declarative schema document version
Canonical serialization contract version
~~~

Example:

~~~text
PyTransformKit package        1.4.0
Declarative schema language   1
Schema wire contract          1
~~~

No numeric equality is required between them.

---

# 49. Canonical export strategy

The exporter SHOULD generate one preferred declaration form.

Even if a parser later accepts aliases such as:

~~~yaml
type: int64
~~~

and:

~~~yaml
type:
  integer:
    bits: 64
    signed: true
~~~

the exporter should select one canonical authoring representation.

This improves:

- deterministic diffs;
- documentation consistency;
- round-trip tests;
- generated files.

---

# 50. Semantic round-trip architecture

The guaranteed round-trip is:

~~~text
Schema
  ↓
SchemaDefinitionExporter
  ↓
SchemaDefinition
  ↓
YamlSchemaEmitter
  ↓
YAML
  ↓
YamlSchemaParser
  ↓
SchemaDefinition
  ↓
SchemaDefinitionCompiler
  ↓
Schema'
~~~

Required invariant:

~~~text
semantic(Schema) == semantic(Schema')
~~~

Textual YAML equality is not required.

---

# 51. What round-trip cannot currently preserve

Because the Domain is the canonical source for export, only state stored by the
Domain can be guaranteed to survive.

Today this includes for Field:

~~~text
name
data_type
nullable
description
~~~

and for Schema:

~~~text
ordered fields
~~~

It does not currently include arbitrary:

~~~text
schema description
schema metadata
field metadata
governance annotations
source comments
YAML formatting
~~~

The declarative specification MUST reflect this reality.

---

# 52. Immutability

Definition objects SHOULD be immutable dataclasses with slots.

This aligns with the Domain style:

~~~python
@dataclass(frozen=True, slots=True)
~~~

Benefits include:

- deterministic validation;
- simpler reasoning;
- safer compiler behavior;
- compatibility with caching/fingerprinting later;
- resistance to accidental mutation between validation and compilation.

---

# 53. No global mutable registry

Declarative type resolution MUST NOT depend on an implicitly mutable global registry
that plugins may modify at import time.

The initial type resolver should use a fixed built-in mapping.

If extensibility is introduced later, activation MUST be explicit and governed by
the existing plugin architecture.

---

# 54. Plugin boundary

The first declarative schema version SHOULD NOT expose custom YAML-defined Python
types through plugins.

A future plugin extension could provide controlled type aliases or codecs, but only
with:

- explicit activation;
- protocol versioning;
- compatibility checks;
- security review;
- deterministic serialization behavior.

No such extension is required initially.

---

# 55. Resource and network isolation

Loading declarative schemas MUST NOT implicitly resolve external resources.

This is intentionally unsupported:

~~~yaml
include: https://example.com/schema.yml
~~~

or:

~~~yaml
include: s3://bucket/schema.yml
~~~

unless a future explicit resource-loader layer is designed.

Initial loaders operate on caller-provided text or explicit local paths.

---

# 56. Includes and inheritance

Schema includes, extends, inheritance and templating are OUT OF SCOPE for the first
architecture.

Examples not initially supported:

~~~yaml
extends: base_customer
~~~

~~~yaml
include: common_fields.yml
~~~

~~~yaml
fields:
  - *common_fields
~~~

These features create composition, resolution and trust semantics that require
separate design.

---

# 57. Environment-variable interpolation

Implicit environment-variable interpolation is prohibited in the initial
architecture.

Example:

~~~yaml
type: ${FIELD_TYPE}
~~~

MUST NOT be resolved automatically.

The schema language describes logical schema semantics, not deployment
configuration.

---

# 58. Templating boundary

Jinja-style templating is OUT OF SCOPE.

The declarative layer MUST NOT initially execute:

~~~text
{{ ... }}
{% ... %}
~~~

This avoids turning schema declaration into an executable DSL.

---

# 59. Architecture testing

Architecture tests SHOULD enforce dependency rules.

Examples:

~~~text
domain/data
    MUST NOT import yaml parser

domain
    MUST NOT import declarative infrastructure

application/declarative
    MUST NOT import pandas/polars/pyarrow/duckdb

infrastructure/declarative
    MAY import optional YAML parser

declarative public facade
    MAY orchestrate application + infrastructure
~~~

---

# 60. Package import behavior

The following MUST work without YAML extras:

~~~python
import pytransformkit
from pytransformkit import Schema, Field
~~~

Preferably the declarative namespace itself may also import without YAML installed,
as long as YAML-specific invocation fails lazily and clearly.

This permits API discoverability without contaminating core imports.

---

# 61. Candidate sequence diagram — load

~~~text
User
 │
 │ load_schema("customers.yml")
 ▼
DeclarativeFacade
 │
 │ read text
 ▼
YamlSchemaParser
 │
 │ safe parse + decode
 ▼
SchemaDocument
 │
 ▼
SchemaDefinitionValidator
 │
 ▼
SchemaDefinitionCompiler
 │
 ├── DeclarativeTypeResolver
 │          │
 │          ▼
 │       DataType
 │
 ▼
Field
 │
 ▼
Schema
 │
 ▼
User
~~~

---

# 62. Candidate sequence diagram — export

~~~text
User
 │
 │ dump_schema(schema, name="customers")
 ▼
DeclarativeFacade
 │
 ▼
SchemaDefinitionExporter
 │
 ▼
SchemaDefinition
 │
 ▼
SchemaDocument
 │
 ▼
YamlSchemaEmitter
 │
 ▼
YAML text
 │
 ▼
filesystem
~~~

---

# 63. Architecture for single-schema documents

A single-schema document may be normalized internally to the same SchemaDocument
representation used for multi-schema input.

Example:

~~~text
single YAML schema
      ↓
SchemaDocument(
    schemas=(SchemaDefinition(...),)
)
~~~

This avoids maintaining separate compilers.

---

# 64. Architecture for multi-schema documents

A multi-schema YAML document uses the same pipeline:

~~~text
YAML
 ↓
SchemaDocument
 ├── SchemaDefinition("customers")
 ├── SchemaDefinition("orders")
 └── SchemaDefinition("payments")
 ↓
compile
 ↓
Mapping[str, Schema]
~~~

Compilation order MUST be deterministic.

The schemas are independent unless a future explicit reference model is introduced.

---

# 65. Cross-schema references

Cross-schema inheritance or type references are OUT OF SCOPE initially.

The first version SHOULD compile each SchemaDefinition independently.

This avoids introducing symbol-resolution semantics before they are necessary.

---

# 66. Caching

Parser or compiler caching is not required initially.

If added later, cache keys MUST be based on deterministic content fingerprints, not
object identity.

Caching MUST NOT change semantics.

---

# 67. Fingerprinting

The declarative layer MAY eventually expose a document fingerprint.

However:

~~~text
declarative document fingerprint
!=
Schema fingerprint
!=
wire payload fingerprint
~~~

Each fingerprint has a distinct semantic scope.

No new public fingerprint is required in the initial implementation.

---

# 68. Observability

Declarative loading is an authoring/configuration operation.

It MAY emit diagnostics.

It SHOULD NOT require telemetry infrastructure.

Parsing a local schema file MUST work with no observability backend.

---

# 69. Performance expectations

The architecture favors correctness, diagnostics and determinism over micro-
optimization.

Schema compilation should remain linear or near-linear in the number of fields for
ordinary definitions.

Nested type traversal should scale with the size of the type tree.

No engine should be initialized during this process.

---

# 70. Thread safety

Definition objects and canonical Domain objects are immutable.

Stateless parsers, validators, resolvers and compilers SHOULD be reusable safely
across independent calls.

No global mutable compilation state should be required.

---

# 71. Proposed dependency extra

The architectural preference is:

~~~text
pytransformkit[yaml]
~~~

rather than making YAML a mandatory core dependency.

Rationale:

1. core Schema construction does not require YAML;
2. users may use only Python authoring;
3. the current project deliberately isolates optional capabilities;
4. YAML belongs to an authoring adapter;
5. dependency isolation remains easy to test.

The exact parser package is frozen in the security/parsing document.

---

# 72. Compatibility with V1 API freeze

The initial declarative implementation SHOULD require no changes to the constructor
signatures of:

~~~text
Schema
Field
DataType subclasses
~~~

This protects the existing V1 public API hashes.

The feature should be additive through new namespaces and modules.

---

# 73. Compatibility with V1 error catalogue

New declarative errors may extend the public error catalogue.

They MUST NOT change the meaning of existing codes:

~~~text
PTK-SCHEMA-000
PTK-SCHEMA-001
PTK-SCHEMA-002
PTK-SCHEMA-003
~~~

New codes should be allocated deliberately and frozen through the normal public
contract process.

---

# 74. Compatibility with serialization

The existing SchemaCodec and DataType serialization semantics remain authoritative
for canonical wire interchange.

Declarative YAML is not assigned existing wire contract IDs merely because it can
represent similar information.

---

# 75. Architecture decision records

The following decisions are frozen by this document.

## ADR-DS-01 — Schema remains canonical

YAML compiles to the existing Schema.

No parallel runtime schema model is introduced.

## ADR-DS-02 — Definition model lives outside Domain

SchemaDocument, SchemaDefinition, FieldDefinition and TypeDefinition belong to the
Application/declarative boundary.

## ADR-DS-03 — YAML is Infrastructure

The YAML parser/emitter belongs to infrastructure/declarative.

## ADR-DS-04 — Compiler is Application

SchemaDefinitionCompiler belongs to application/declarative and depends on Domain.

## ADR-DS-05 — Exporter is Application

SchemaDefinitionExporter converts Domain values into format-neutral definitions.

## ADR-DS-06 — Public facade is additive

A dedicated declarative authoring namespace is preferred.

## ADR-DS-07 — No Schema.from_yaml dependency inversion

Domain objects do not import YAML infrastructure.

## ADR-DS-08 — YAML is optional

The preferred packaging model is pytransformkit[yaml].

## ADR-DS-09 — No engine coupling

Declarative compilation stops at canonical DataType.

## ADR-DS-10 — No general metadata loss

Properties that cannot survive Domain round-trip are not silently discarded.

## ADR-DS-11 — No templating

Jinja, eval, environment interpolation and executable configuration are outside the
initial feature.

## ADR-DS-12 — No implicit includes

Local or remote includes require a future explicit design.

---

# 76. Proposed internal package graph

~~~text
pytransformkit.declarative
        │
        ├─────────────────────────────────────┐
        │                                     │
        ▼                                     ▼
application.declarative                infrastructure.declarative
        │                                     │
        │                                     ├── optional YAML dependency
        │                                     │
        ▼                                     │
application.ports  ◄──────────────────────────┘
        │
        ▼
domain.data
        │
        ├── Schema
        ├── Field
        └── DataType
~~~

Serialization remains adjacent, not underneath declarative authoring:

~~~text
domain.data
    ↑                ↑
declarative      serialization
authoring        wire contracts
~~~

---

# 77. Proposed module responsibilities

| Module | Responsibility |
| --- | --- |
| declarative/api.py | public convenience orchestration |
| application/declarative/model.py | format-neutral definition values |
| application/declarative/validation.py | declarative semantic validation |
| application/declarative/type_resolution.py | TypeDefinition → DataType |
| application/declarative/compiler.py | SchemaDefinition → Schema |
| application/declarative/exporter.py | Schema → SchemaDefinition |
| application/ports/declarative.py | parser/emitter Protocols |
| infrastructure/declarative/yaml.py | safe YAML parse/emit |
| errors/declarative.py | stable declarative error hierarchy |

---

# 78. Implementation boundary for first release

The first declarative-schema release SHOULD include:

~~~text
SchemaDocument
SchemaDefinition
FieldDefinition
TypeDefinition hierarchy
strict YAML parser
definition validator
type resolver
compiler
exporter
single-schema loading
multi-schema loading
in-memory loading
filesystem loading
in-memory export
filesystem export
semantic round-trip tests
security tests
architecture tests
~~~

It SHOULD NOT include:

~~~text
templating
Jinja
environment interpolation
remote includes
local includes
schema inheritance
cross-schema references
governance metadata DSL
quality-test DSL
Dataset declaration
TransformationPlan declaration
workflow declaration
engine-native dtype declarations
custom Python type imports
~~~

---

# 79. Architecture acceptance criteria

The architecture is acceptable only if all of the following can be demonstrated:

1. Schema, Field and DataType require no YAML import;
2. direct Python schema construction remains unchanged;
3. YAML support can be absent from a core installation;
4. YAML input produces canonical Schema objects;
5. engine packages are not required for schema loading;
6. unknown YAML properties fail;
7. unknown types fail;
8. duplicate YAML keys fail;
9. duplicate fields fail;
10. nested types compile recursively;
11. Domain invariant checks still execute;
12. Schema export/import is semantically stable;
13. canonical serialization contracts remain unchanged;
14. no arbitrary Python execution is possible through YAML;
15. no metadata is silently lost through a claimed round-trip.

---

# 80. Consequences

## Positive consequences

The architecture provides:

- concise schema authoring;
- clear separation of concerns;
- no Domain contamination;
- engine neutrality;
- future format extensibility;
- deterministic validation;
- security boundaries;
- easier data-contract review;
- stable Python compatibility.

## Costs

The architecture introduces:

- an intermediate definition model;
- parser and emitter abstractions;
- additional error types;
- extra test surface;
- optional dependency management;
- explicit compilation/export steps.

These costs are intentional.

They prevent the simpler-looking but structurally harmful design:

~~~text
Schema.from_yaml()
    + YAML logic inside Domain
~~~

---

# 81. Future extensibility

Once the architecture is established, additional authoring formats could be added:

~~~text
YAML ─────┐
JSON ─────┼──> SchemaDocument ──> Schema
TOML ─────┘
~~~

without modifying the Domain.

This is an architectural capability, not a commitment to implement those formats.

---

# 82. Next documents

This architecture must now be refined by:

~~~text
31_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SPECIFICATION.md
32_PYTRANSFORMKIT_DECLARATIVE_TYPE_SYSTEM_MAPPING.md
33_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_DOMAIN_MODEL.md
34_PYTRANSFORMKIT_SCHEMA_LOADER_COMPILER_AND_EXPORTER_SPEC.md
35_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_VALIDATION_AND_ERROR_MODEL.md
36_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SECURITY_AND_PARSING_POLICY.md
37_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ROUNDTRIP_AND_SERIALIZATION_MODEL.md
38_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_PUBLIC_API_SPEC.md
39_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_TEST_MATRIX_AND_ACCEPTANCE_CRITERIA.md
40_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_IMPLEMENTATION_ROADMAP.md
~~~

The immediate next step is to freeze the declarative document grammar.

---

# 83. Final architecture

The target design can be summarized as:

~~~text
                        AUTHORING

              Python                 YAML
                │                     │
                │              YamlSchemaParser
                │                     │
                │               SchemaDocument
                │                     │
                │         SchemaDefinitionValidator
                │                     │
                │         SchemaDefinitionCompiler
                │                     │
                └──────────┬──────────┘
                           ▼

                         DOMAIN

                         Schema
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                  Field        DataType
                    │
                    ▼

                    APPLICATION / RUNTIME
                           │
                           ▼

                         ENGINES
~~~

and in the reverse direction:

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

The architectural rule remains:

> **YAML describes a Schema. YAML is not the Schema.**

That rule preserves PyTransformKit's V1 Domain while enabling a substantially more
ergonomic declarative authoring experience.
