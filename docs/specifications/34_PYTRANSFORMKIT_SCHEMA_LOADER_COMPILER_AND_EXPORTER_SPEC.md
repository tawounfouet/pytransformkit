# 34 — PyTransformKit Schema Loader, Compiler and Exporter Specification

> **Document status:** DRAFT NORMATIVE SPECIFICATION  
> **Depends on:** 30_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ARCHITECTURE.md  
> **Depends on:** 31_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SPECIFICATION.md  
> **Depends on:** 32_PYTRANSFORMKIT_DECLARATIVE_TYPE_SYSTEM_MAPPING.md  
> **Depends on:** 33_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_DOMAIN_MODEL.md  
> **Scope:** Declarative loading, validation, compilation, export and YAML emission  
> **Declarative language version:** 1

---

# 1. Purpose

This document specifies the services and orchestration required to convert declarative schema documents into canonical PyTransformKit Schema objects and back again.

It freezes the responsibilities and interaction contracts of:

- SchemaDocumentParser;
- YamlSchemaParser;
- SchemaDefinitionValidator;
- DeclarativeTypeResolver;
- SchemaDefinitionCompiler;
- DeclarativeTypeExporter;
- SchemaDefinitionExporter;
- SchemaDocumentEmitter;
- YamlSchemaEmitter;
- filesystem helpers;
- in-memory helpers;
- single-schema loading;
- multi-schema loading;
- single-schema export;
- multi-schema export.

The complete target flow is:

~~~text
YAML / text / path
      ↓
SchemaDocumentParser
      ↓
SchemaDocument
      ↓
SchemaDefinitionValidator
      ↓
SchemaDefinitionCompiler
      ↓
Schema
~~~

and in reverse:

~~~text
Schema
      ↓
SchemaDefinitionExporter
      ↓
SchemaDocument
      ↓
SchemaDocumentEmitter
      ↓
YAML / text / path
~~~

---

# 2. Architectural principle

The implementation MUST keep parsing, validation, compilation and emission as distinct responsibilities.

The architecture MUST NOT collapse into:

~~~text
YAML
 ↓
one giant function
 ↓
Schema
~~~

The preferred decomposition is:

~~~text
PARSE
  ↓
DECODE
  ↓
VALIDATE
  ↓
RESOLVE TYPES
  ↓
COMPILE
  ↓
DOMAIN
~~~

This separation enables strong diagnostics, independent unit testing, format extensibility, clean dependency direction, deterministic behavior and security isolation.

---

# 3. Service inventory

Declarative schema V1 SHOULD provide these logical services:

~~~text
SchemaDocumentParser
YamlSchemaParser
SchemaDefinitionValidator
DeclarativeTypeResolver
SchemaDefinitionCompiler
DeclarativeTypeExporter
SchemaDefinitionExporter
SchemaDocumentEmitter
YamlSchemaEmitter
DeclarativeSchemaService / facade
~~~

Exact implementation class names MAY evolve. Responsibilities defined here MUST remain distinct.

---

# 4. SchemaDocumentParser port

The Application layer SHOULD expose a format-neutral parser port.

~~~python
from typing import Protocol

class SchemaDocumentParser(Protocol):
    def parse(
        self,
        text: str,
        *,
        source: str | None = None,
    ) -> SchemaDocument:
        ...
~~~

The port MUST accept text already loaded by the caller or facade, return a normalized SchemaDocument, remain format-neutral, and expose no YAML-specific type in its signature.

---

# 5. Parser output contract

A successful parser call MUST return SchemaDocument.

It MUST NOT return raw dict/list structures, YAML nodes, parser events, AST tokens, engine objects or canonical Schema objects.

The parser boundary ends at the definition model.

---

# 6. YamlSchemaParser

YamlSchemaParser is the YAML-specific Infrastructure adapter.

~~~python
class YamlSchemaParser:
    def parse(
        self,
        text: str,
        *,
        source: str | None = None,
    ) -> SchemaDocument:
        ...
~~~

Its responsibilities are:

1. enforce safe YAML parsing;
2. reject unsupported YAML features;
3. reject duplicate mapping keys;
4. control scalar interpretation;
5. decode the plain parsed structure;
6. normalize short and structured type forms;
7. construct immutable definition objects;
8. attach or index source diagnostic information when available.

It MUST NOT compile canonical Schema objects.

---

# 7. YAML parsing stages

YamlSchemaParser SHOULD internally follow:

~~~text
raw text
  ↓
safe YAML loader
  ↓
plain values
  ↓
strict declarative decoder
  ↓
SchemaDocument
~~~

Only safe plain values should cross the raw parser boundary: dict, list, str, int, float, bool and None.

Custom Python objects constructed by YAML tags are forbidden.

---

# 8. Strict declarative decoder

The decoder maps plain values to normalized definition values.

It owns root shape, version, schema versus schemas, field shape, allowed keys, strict scalar types, type discriminators, defaults, alias normalization and nested type recursion.

The decoder MUST reject unknown properties.

---

# 9. Decoder and validator distinction

The decoder answers:

> Is this structure valid declarative V1 syntax?

The validator answers:

> Is this normalized definition semantically valid as a declarative schema?

Some checks MAY technically occur in either layer, but public behavior MUST remain deterministic.

---

# 10. SchemaDefinitionValidator

SchemaDefinitionValidator validates normalized definition objects.

~~~python
class SchemaDefinitionValidator:
    def validate_document(
        self,
        document: SchemaDocument,
    ) -> None:
        ...
~~~

The validator MUST NOT mutate definitions.

It SHOULD cover supported document version, unique schema names, non-empty schema names, unique field names, recursive nested uniqueness, integer/float widths, decimal constraints, temporal units, timezone validity, nested type completeness and collection invariants.

---

# 11. Validation result model

V1 SHOULD use exception-based failure for invalid declarative input.

A successful validation call may return None or the same immutable document.

The validator SHOULD NOT create a second validated-model hierarchy unless implementation evidence justifies it.

---

# 12. Source-aware validation

When source context exists, validation errors SHOULD include:

~~~text
source
line
column
object path
~~~

Example:

~~~text
schemas/customers.yml:18:9
schema.fields[2].type.decimal.scale
~~~

Source context MUST NOT become canonical Domain state.

---

# 13. DeclarativeTypeResolver

DeclarativeTypeResolver converts TypeDefinition to canonical DataType.

~~~python
class DeclarativeTypeResolver:
    def resolve(
        self,
        definition: TypeDefinition,
    ) -> DataType:
        ...
~~~

The resolver MUST be deterministic and side-effect free.

---

# 14. Resolver responsibilities

~~~text
StringTypeDefinition      → StringType
BooleanTypeDefinition     → BooleanType
IntegerTypeDefinition     → IntegerType
FloatTypeDefinition       → FloatType
DecimalTypeDefinition     → DecimalType
BinaryTypeDefinition      → BinaryType
DateTypeDefinition        → DateType
TimeTypeDefinition        → TimeType
TimestampTypeDefinition   → TimestampType
DurationTypeDefinition    → DurationType
UnknownTypeDefinition     → UnknownType
ListTypeDefinition        → ListType
StructTypeDefinition      → StructType
MapTypeDefinition         → MapType
~~~

Nested definitions are resolved recursively.

---

# 15. Resolver purity

DeclarativeTypeResolver MUST NOT access files or network, import engines, inspect environment variables, activate plugins, parse YAML, emit YAML or depend on runtime execution state.

Its contract is:

~~~text
TypeDefinition → DataType
~~~

---

# 16. Nested resolution

For ListTypeDefinition, element_type is recursively resolved before ListType construction.

For StructTypeDefinition, every StructFieldDefinition.data_type is recursively resolved before StructField and StructType construction.

For MapTypeDefinition, key_type and value_type are recursively resolved before MapType construction.

If the resolver receives an unsupported TypeDefinition subclass, it MUST fail explicitly.

It MUST NOT return UnknownType as a fallback.

---

# 17. SchemaDefinitionCompiler

SchemaDefinitionCompiler converts one validated SchemaDefinition into canonical Schema.

~~~python
class SchemaDefinitionCompiler:
    def __init__(
        self,
        type_resolver: DeclarativeTypeResolver,
    ) -> None:
        ...

    def compile(
        self,
        definition: SchemaDefinition,
    ) -> Schema:
        ...
~~~

---

# 18. Compiler responsibilities

The compiler MUST:

1. preserve field order;
2. resolve every FieldDefinition.data_type;
3. construct canonical Field objects;
4. preserve nullable;
5. preserve description;
6. construct canonical Schema;
7. allow canonical Domain invariants to execute.

The compiler MUST NOT parse YAML, read files, attach schema names into Schema, convert to engine dtypes, access network or perform runtime execution.

---

# 19. Field compilation

Canonical field compilation is:

~~~python
Field(
    name=field_definition.name,
    data_type=type_resolver.resolve(
        field_definition.data_type,
    ),
    nullable=field_definition.nullable,
    description=field_definition.description,
)
~~~

No additional state is introduced.

---

# 20. Schema compilation

Canonical schema compilation is:

~~~python
Schema(
    fields=tuple(compiled_fields),
)
~~~

The compiler MUST preserve author order.

---

# 21. Document compilation

A higher-level compiler method MAY compile an entire document.

~~~python
class SchemaDocumentCompiler:
    def compile(
        self,
        document: SchemaDocument,
    ) -> dict[str, Schema]:
        ...
~~~

or this orchestration MAY live in the public facade.

The result MUST preserve schema declaration order.

---

# 22. Multi-schema output

Recommended result:

~~~python
{
    "customers": Schema(...),
    "orders": Schema(...),
}
~~~

A standard insertion-ordered dict is sufficient.

The schema name is represented by the mapping key and is never injected into Schema.

---

# 23. Single-schema extraction

A single-schema helper MUST enforce cardinality.

~~~python
def compile_single_schema(
    document: SchemaDocument,
) -> Schema:
    ...
~~~

It MUST fail when len(document.schemas) is not exactly 1.

It MUST NOT silently select the first schema from a multi-schema document.

---

# 24. DeclarativeTypeExporter

DeclarativeTypeExporter performs the reverse mapping:

~~~text
DataType → TypeDefinition
~~~

~~~python
class DeclarativeTypeExporter:
    def export(
        self,
        data_type: DataType,
    ) -> TypeDefinition:
        ...
~~~

It MUST implement the exhaustive mapping defined in document 32.

---

# 25. Type exporter responsibilities

The exporter MUST preserve integer bits and signedness, float width, decimal precision and scale, temporal units, timestamp timezone, list element nullability, struct field order/nullability, and map key/value types plus value nullability.

Unknown DataType subclasses MUST fail export explicitly.

---

# 26. SchemaDefinitionExporter

SchemaDefinitionExporter converts canonical Schema to declarative SchemaDefinition.

~~~python
class SchemaDefinitionExporter:
    def __init__(
        self,
        type_exporter: DeclarativeTypeExporter,
    ) -> None:
        ...

    def export(
        self,
        schema: Schema,
        *,
        name: str,
    ) -> SchemaDefinition:
        ...
~~~

The explicit name argument is REQUIRED because canonical Schema has no name.

---

# 27. Schema export responsibilities

SchemaDefinitionExporter MUST:

1. require a non-empty declarative name;
2. preserve Schema field order;
3. convert every Field.data_type;
4. preserve Field.nullable;
5. preserve Field.description;
6. create immutable FieldDefinition objects;
7. create SchemaDefinition.

---

# 28. Schema exporter cannot invent names

The exporter MUST NOT infer a name from Python variable names, repr, filesystem paths, global registries or hidden metadata.

The caller supplies declaration identity explicitly.

---

# 29. SchemaDocumentEmitter port

The Application layer SHOULD define a format-neutral emitter port.

~~~python
class SchemaDocumentEmitter(Protocol):
    def emit(
        self,
        document: SchemaDocument,
    ) -> str:
        ...
~~~

This port MUST NOT mention YAML-specific library types.

---

# 30. YamlSchemaEmitter

YamlSchemaEmitter implements declarative schema V1 YAML emission.

~~~python
class YamlSchemaEmitter:
    def emit(
        self,
        document: SchemaDocument,
    ) -> str:
        ...
~~~

Its responsibilities are to transform definition objects to canonical YAML-ready values, apply canonical property ordering, apply canonical type short/structured forms, emit deterministic YAML text and avoid unsupported YAML features.

---

# 31. Emitter input contract

YamlSchemaEmitter receives only normalized, validated definition values.

It MUST NOT receive canonical Schema directly.

The path remains:

~~~text
Schema
 ↓
SchemaDefinitionExporter
 ↓
SchemaDocument
 ↓
YamlSchemaEmitter
~~~

---

# 32. Canonical emission form

The emitter MUST follow document 31.

It SHOULD emit version first, schema/schemas second, preserve all ordering, emit nullable explicitly, emit descriptions only when present, use canonical type names, never emit aliases, and use short forms only for canonical default temporal values.

---

# 33. Deterministic YAML output

Given the same SchemaDocument, the emitter SHOULD produce byte-stable UTF-8 text under the same PyTransformKit version.

It MUST preserve canonical key ordering, schema order, field order, nested field order and canonical type spelling.

---

# 34. Unsupported YAML emission

YamlSchemaEmitter MUST NOT emit anchors, aliases, merge keys, custom tags, multi-document streams, Python object tags or executable templating.

---

# 35. In-memory loading API

Candidate single-schema helper:

~~~python
loads_schema(
    text: str,
    *,
    source: str | None = None,
) -> Schema
~~~

Flow:

~~~text
text
 ↓
parser.parse
 ↓
validate
 ↓
compile single schema
 ↓
Schema
~~~

---

# 36. In-memory multi-schema loading API

Candidate:

~~~python
loads_schemas(
    text: str,
    *,
    source: str | None = None,
) -> dict[str, Schema]
~~~

Flow:

~~~text
text
 ↓
parse
 ↓
validate
 ↓
compile all
 ↓
dict[str, Schema]
~~~

---

# 37. Filesystem loading API

Candidate:

~~~python
load_schema(
    path: str | Path,
) -> Schema
~~~

Recommended implementation:

~~~text
read UTF-8 text
 ↓
loads_schema(text, source=str(path))
~~~

Filesystem helpers SHOULD be thin wrappers around in-memory helpers.

---

# 38. Multi-schema filesystem loading

Candidate:

~~~python
load_schemas(
    path: str | Path,
) -> dict[str, Schema]
~~~

No directory scanning occurs implicitly.

---

# 39. Single-schema cardinality rule

load_schema and loads_schema MUST accept only documents containing exactly one schema.

If a document contains multiple schemas, the helper MUST fail with an actionable error instructing the caller to use load_schemas or loads_schemas.

It MUST NOT silently choose the first schema.

---

# 40. Multi-schema helper behavior

load_schemas and loads_schemas MAY accept a one-schema document.

The result is a one-entry mapping.

This keeps the multi-schema API general.

---

# 41. In-memory export API

Candidate:

~~~python
dumps_schema(
    schema: Schema,
    *,
    name: str,
) -> str
~~~

Flow:

~~~text
Schema
 ↓
SchemaDefinitionExporter
 ↓
SchemaDocument(version=1, one schema)
 ↓
YamlSchemaEmitter
 ↓
str
~~~

---

# 42. Filesystem export API

Candidate:

~~~python
dump_schema(
    schema: Schema,
    path: str | Path,
    *,
    name: str,
) -> None
~~~

Recommended implementation:

~~~text
dumps_schema(...)
 ↓
write UTF-8 text
~~~

The emitter does not write files itself.

---

# 43. Multi-schema export API

Candidate in-memory helper:

~~~python
dumps_schemas(
    schemas: Mapping[str, Schema],
) -> str
~~~

Candidate filesystem helper:

~~~python
dump_schemas(
    schemas: Mapping[str, Schema],
    path: str | Path,
) -> None
~~~

The mapping keys become declarative schema names.

---

# 44. Multi-schema export order

The exporter SHOULD preserve input Mapping iteration order.

The implementation MUST NOT arbitrarily sort schema names unless a future canonical policy explicitly chooses sorting.

Preferred policy: preserve caller order.

---

# 45. Public facade orchestration

A high-level facade MAY encapsulate service wiring.

~~~python
class DeclarativeSchemaService:
    def loads_schema(...): ...
    def loads_schemas(...): ...
    def dumps_schema(...): ...
    def dumps_schemas(...): ...
~~~

However, the user-facing API SHOULD remain simple functions unless object configuration is needed.

---

# 46. Service wiring

Default orchestration conceptually wires:

~~~text
YamlSchemaParser
SchemaDefinitionValidator
DeclarativeTypeResolver
SchemaDefinitionCompiler
DeclarativeTypeExporter
SchemaDefinitionExporter
YamlSchemaEmitter
~~~

Wiring MAY be lazy.

YAML-specific dependency import SHOULD occur only when the capability is invoked.

---

# 47. Optional YAML dependency behavior

If the YAML parser package is optional, import pytransformkit MUST continue to work without it.

Calling a YAML-specific API without the extra installed MUST raise a controlled dependency or capability error.

---

# 48. Lazy dependency import

Preferred sequence:

~~~text
public declarative API imported
      ↓
no YAML dependency imported yet
      ↓
load_schema called
      ↓
attempt YAML adapter import
~~~

This protects lightweight core imports.

---

# 49. File encoding

Filesystem load helpers MUST read declarative YAML as UTF-8.

Filesystem dump helpers MUST write UTF-8.

A final trailing newline SHOULD be emitted.

---

# 50. Filesystem path behavior

Loading helpers MUST operate only on the explicitly supplied path.

They MUST NOT scan parent directories, discover project roots, auto-load sibling schemas, follow includes or fetch remote URLs.

---

# 51. File failures

Missing-file and access failures SHOULD be translated into stable PyTransformKit declarative errors where appropriate.

Raw OSError details MAY be chained for debugging.

Exact exception classes are defined in document 35.

---

# 52. Validation before compilation

The high-level loading flow MUST validate before Domain compilation.

Required sequence:

~~~text
parse
 ↓
validate
 ↓
compile
~~~

The facade MUST NOT skip validation for apparently simple documents.

---

# 53. Validation before emission

Exported definition objects SHOULD also pass declarative validation before YAML emission.

Required flow:

~~~text
Schema
 ↓
export definition
 ↓
validate generated document
 ↓
emit
~~~

This acts as a self-check on exporter correctness.

---

# 54. Domain invariants remain active

Even after declarative validation, compiler-created Domain values MUST invoke normal constructors.

The compiler MUST NOT bypass Field, Schema, DataType or StructType invariants through unsafe construction shortcuts.

---

# 55. Error translation boundary

Low-level parser errors SHOULD be translated at the parser adapter boundary.

Definition validation errors SHOULD be translated at the validator boundary.

Domain construction errors MAY be translated by compiler services when additional source context is available.

The public caller SHOULD receive PyTransformKit-owned errors.

---

# 56. Exception chaining

Implementation SHOULD preserve underlying exceptions using Python exception chaining.

~~~python
raise DeclarativeSchemaParseError(...) from error
~~~

This preserves causality without exposing parser-specific exceptions as the public contract.

---

# 57. No best-effort recovery

The loading pipeline MUST NOT skip invalid fields, drop unknown properties, replace invalid types with UnknownType, ignore duplicate names or continue after malformed nested types.

One invalid contract invalidates the relevant document load.

---

# 58. No partial multi-schema success

For declarative V1, load_schemas SHOULD be atomic at document level.

If one schema in a document is invalid, the call SHOULD fail rather than return only the valid schemas.

This prevents partial contract activation.

---

# 59. Compilation determinism

Given an equal validated SchemaDefinition, compilation MUST produce an equal canonical Schema.

No external state may influence compilation.

---

# 60. Export determinism

Given the same Schema, the same explicit name and the same declarative language version, the exported semantic SchemaDefinition MUST be equal.

YAML text SHOULD also be deterministic under the same emitter version.

---

# 61. Single-schema load sequence

~~~text
User
 │
 │ load_schema(path)
 ▼
read UTF-8
 │
 ▼
loads_schema(text, source=path)
 │
 ▼
YamlSchemaParser.parse
 │
 ▼
SchemaDocument
 │
 ▼
SchemaDefinitionValidator.validate_document
 │
 ▼
cardinality == 1
 │
 ▼
SchemaDefinitionCompiler.compile
 │
 ▼
Schema
 │
 ▼
User
~~~

---

# 62. Multi-schema load sequence

~~~text
User
 │
 │ load_schemas(path)
 ▼
read UTF-8
 │
 ▼
YamlSchemaParser.parse
 │
 ▼
SchemaDocument
 │
 ▼
SchemaDefinitionValidator
 │
 ▼
compile each SchemaDefinition
 │
 ▼
dict[str, Schema]
 │
 ▼
User
~~~

---

# 63. Single-schema dump sequence

~~~text
User
 │
 │ dump_schema(schema, path, name=customers)
 ▼
SchemaDefinitionExporter
 │
 ▼
SchemaDefinition
 │
 ▼
SchemaDocument(version=1)
 │
 ▼
SchemaDefinitionValidator
 │
 ▼
YamlSchemaEmitter
 │
 ▼
UTF-8 text
 │
 ▼
write exact path
~~~

---

# 64. Multi-schema dump sequence

~~~text
Mapping[str, Schema]
 │
 ▼
SchemaDefinitionExporter for each entry
 │
 ▼
SchemaDocument
 │
 ▼
validate
 │
 ▼
YamlSchemaEmitter
 │
 ▼
YAML
~~~

---

# 65. Port and adapter graph

~~~text
APPLICATION PORTS

SchemaDocumentParser
SchemaDocumentEmitter

       ▲                ▲
       │                │

INFRASTRUCTURE ADAPTERS

YamlSchemaParser
YamlSchemaEmitter
~~~

Application services remain independent from the concrete YAML package.

---

# 66. Testing strategy by service

Each service MUST be independently testable.

Parser tests SHOULD cover valid roots, invalid roots, duplicate YAML keys, unknown properties, unsafe tags, anchors, multi-document streams and scalar ambiguity.

Validator tests SHOULD cover duplicate schemas, duplicate fields, nested duplicates, invalid parameters and unsupported versions.

Resolver tests MUST cover all primitive, parameterized and nested types plus unsupported definition subclasses.

Compiler tests MUST cover field ordering, descriptions, nullability, nested type mapping and Domain invariant propagation.

Exporter tests MUST cover every canonical DataType variant, explicit schema naming, ordering and unsupported custom DataType subclasses.

Emitter tests MUST cover canonical key order, canonical spelling, stable formatting, no aliases and parseability.

---

# 67. Integration test — basic load

Given:

~~~yaml
version: 1

schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false

    - name: email
      type: string
      nullable: true
~~~

load_schema MUST produce:

~~~python
Schema(
    fields=(
        Field(
            name="customer_id",
            data_type=IntegerType(bits=64, signed=True),
            nullable=False,
        ),
        Field(
            name="email",
            data_type=StringType(),
            nullable=True,
        ),
    )
)
~~~

---

# 68. Integration test — nested load

A nested list, struct or map declaration MUST compile recursively into equal canonical DataType values.

Tests MUST compare canonical Domain objects, not only string representations.

---

# 69. Integration test — dump and load

Required invariant:

~~~text
Schema
 ↓ dumps_schema(name=customers)
YAML
 ↓ loads_schema
Schema'

Schema == Schema'
~~~

for representative schemas.

---

# 70. Integration test — multi-schema

Required:

~~~text
Mapping[str, Schema]
 ↓ dumps_schemas
YAML
 ↓ loads_schemas
Mapping[str, Schema]'
~~~

with preserved key order and Schema equality.

---

# 71. Integration test — missing YAML extra

In an environment without the YAML extra, core import MUST succeed.

Calling the YAML capability MUST fail with a controlled dependency error.

---

# 72. Integration test — no engines

The complete declarative round-trip MUST work without pandas, polars, pyarrow or duckdb installed.

This proves engine independence.

---

# 73. Performance expectations

For ordinary documents, parsing and compilation SHOULD be approximately linear in the number of declarative nodes.

No engine initialization may occur.

No network calls may occur.

No plugin discovery is required.

---

# 74. Thread-safety expectations

Default services SHOULD be stateless or effectively immutable.

Independent load and export operations SHOULD not share mutable global state.

---

# 75. Extensibility to future formats

The parser and emitter ports make future adapters possible:

~~~text
YamlSchemaParser ──┐
JsonSchemaParser ──┼──> SchemaDocument
TomlSchemaParser ──┘
~~~

and:

~~~text
SchemaDocument
   ├──> YamlSchemaEmitter
   ├──> JsonSchemaEmitter
   └──> TomlSchemaEmitter
~~~

Only YAML is in scope for V1.

---

# 76. Extensibility to future language versions

Version routing MAY later use:

~~~text
parse raw document
 ↓
detect version
 ↓
V1 decoder / V2 decoder
 ↓
normalized definition model
~~~

Compiler services SHOULD remain independent from YAML version details whenever normalized semantics remain compatible.

---

# 77. Service visibility recommendation

Likely visibility:

~~~text
load_schema            public
loads_schema           public
load_schemas           public
loads_schemas          public
dump_schema            public
dumps_schema           public
dump_schemas           public
dumps_schemas          public

SchemaDefinition*      advanced/internal
YamlSchemaParser       internal
YamlSchemaEmitter      internal
compiler services      internal
resolver services      internal
~~~

The final decision belongs to document 38.

---

# 78. Decisions frozen by this document

## DEC-SVC-01

Parsing, validation, type resolution, compilation and emission are separate services.

## DEC-SVC-02

YamlSchemaParser returns SchemaDocument, not Schema.

## DEC-SVC-03

SchemaDefinitionValidator validates normalized definitions.

## DEC-SVC-04

DeclarativeTypeResolver performs TypeDefinition → DataType.

## DEC-SVC-05

SchemaDefinitionCompiler performs SchemaDefinition → Schema.

## DEC-SVC-06

DeclarativeTypeExporter performs DataType → TypeDefinition.

## DEC-SVC-07

SchemaDefinitionExporter requires an explicit schema name.

## DEC-SVC-08

YamlSchemaEmitter receives SchemaDocument, not Schema.

## DEC-SVC-09

Filesystem helpers are thin wrappers around in-memory helpers.

## DEC-SVC-10

Single-schema helpers require exactly one schema.

## DEC-SVC-11

Multi-schema load is document-atomic.

## DEC-SVC-12

Generated definitions are validated before emission.

## DEC-SVC-13

Core import does not eagerly require the YAML dependency.

## DEC-SVC-14

No physical engine participates in declarative compilation.

---

# 79. Acceptance criteria

This service design is considered satisfied when:

1. YAML parsing returns normalized SchemaDocument;
2. parser and compiler are independently testable;
3. validation is explicit;
4. type resolution is recursive and deterministic;
5. field order is preserved;
6. Schema names remain outside canonical Schema;
7. single-schema cardinality is enforced;
8. multi-schema loading preserves declaration order;
9. canonical Schema can be exported with explicit name;
10. emitted YAML is deterministic;
11. emitted YAML is accepted by the parser;
12. round-trip preserves canonical Schema state;
13. parser-specific errors do not leak as the public contract;
14. YAML is optional to core import;
15. no engine dependency is required;
16. invalid documents do not partially compile;
17. no arbitrary code execution path exists.

---

# 80. Next document

The next document freezes validation semantics and public error contracts:

~~~text
35_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_VALIDATION_AND_ERROR_MODEL.md
~~~

It must define:

~~~text
error hierarchy
PTK error codes
parse errors
version errors
unknown properties
unknown types
duplicate keys
duplicate fields
invalid parameters
cardinality errors
dependency errors
source locations
object paths
error wrapping
exception chaining
~~~

---

# 81. Final summary

The declarative-schema execution model is intentionally layered.

The forward path is:

~~~text
YAML
 ↓
YamlSchemaParser
 ↓
SchemaDocument
 ↓
SchemaDefinitionValidator
 ↓
SchemaDefinitionCompiler
 ↓
DeclarativeTypeResolver
 ↓
Schema / Field / DataType
~~~

The reverse path is:

~~~text
Schema / Field / DataType
 ↓
SchemaDefinitionExporter
 ↓
DeclarativeTypeExporter
 ↓
SchemaDocument
 ↓
YamlSchemaEmitter
 ↓
YAML
~~~

The public convenience layer orchestrates these services without merging their responsibilities.

> **Parse declarations, validate intent, compile into the Domain, export from the Domain, and keep each boundary explicit.**