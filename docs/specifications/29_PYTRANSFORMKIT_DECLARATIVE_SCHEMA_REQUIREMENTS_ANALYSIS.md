# 29 — PyTransformKit Declarative Schema — Requirements Analysis

> **Document status:** DRAFT  
> **Depends on:** `28_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_EXPRESSION_DU_BESOIN.md`  
> **Scope:** Declarative schema authoring for PyTransformKit  
> **Primary candidate format:** YAML  
> **Canonical domain model:** `Schema` / `Field` / `DataType`  
> **Purpose:** Transform the expression of need into explicit, testable requirements

---

## 1. Purpose

This document converts the declarative-schema expression of need into a normative
requirements baseline.

It defines:

- functional requirements;
- non-functional requirements;
- compatibility constraints;
- security requirements;
- parsing requirements;
- type-system requirements;
- packaging requirements;
- public-API requirements;
- diagnostics requirements;
- round-trip requirements;
- testability requirements;
- acceptance criteria.

This document does **not** define the final YAML grammar.

The normative grammar will be specified in:

~~~text
31_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SPECIFICATION.md
~~~

The architecture satisfying these requirements will be defined in:

~~~text
30_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ARCHITECTURE.md
~~~

---

## 2. Normative language

The keywords used in this document have the following meaning:

| Keyword | Meaning |
| --- | --- |
| MUST | mandatory requirement |
| MUST NOT | prohibited behavior |
| SHOULD | recommended unless a documented reason justifies otherwise |
| SHOULD NOT | discouraged unless a documented reason justifies otherwise |
| MAY | optional capability |

These terms are requirements language, not implementation suggestions.

---

## 3. Architectural invariants inherited from document 28

The following invariants are already established and are therefore requirements.

### INV-01 — Single canonical schema model

`Schema` MUST remain the canonical in-memory schema representation.

A YAML document MUST NOT become a second runtime schema model.

### INV-02 — Declarative layer is an authoring layer

The declarative representation MUST be interpreted as an input format.

~~~text
YAML
  ↓
definition model
  ↓
compiler
  ↓
Schema
~~~

### INV-03 — Domain independence

The Domain MUST NOT import:

- a YAML parser;
- filesystem-specific loaders;
- serialization adapters;
- optional infrastructure packages.

### INV-04 — Python API continuity

The existing programmatic Python schema API MUST remain valid.

A user MUST be able to use PyTransformKit without using YAML.

### INV-05 — Canonical serialization independence

The declarative YAML representation MUST NOT replace the existing versioned
serialization contracts.

### INV-06 — Fail-closed behavior

Unknown, malformed or ambiguous declarations MUST fail explicitly.

The loader MUST NOT silently repair semantic errors.

### INV-07 — No arbitrary execution

The declarative layer MUST NOT execute arbitrary Python code.

---

## 4. Requirement categories

Requirements are organized into the following categories:

~~~text
DS-FR    Functional requirements
DS-DOC   Document model requirements
DS-TYPE  Type-system requirements
DS-VAL   Validation requirements
DS-ERR   Error and diagnostic requirements
DS-SEC   Security requirements
DS-COMP  Compatibility requirements
DS-PKG   Packaging and dependency requirements
DS-API   Public API requirements
DS-RT    Round-trip requirements
DS-NFR   Non-functional requirements
DS-TEST  Testing requirements
DS-ACC   Acceptance requirements
~~~

---

# 5. Functional requirements

## DS-FR-001 — Load one schema

The system MUST support loading one declarative schema document and producing one
canonical `Schema`.

Conceptually:

~~~python
schema = load_schema("customers.yml")
~~~

The final public API name is not frozen by this document.

---

## DS-FR-002 — Load multiple schemas

The system MUST support a document containing multiple named schema definitions.

Conceptually:

~~~python
schemas = load_schemas("domain.yml")
customers = schemas["customers"]
orders = schemas["orders"]
~~~

The resulting mapping MUST preserve schema identity by name.

---

## DS-FR-003 — Preserve field order

The order of fields declared by the author MUST be preserved in the resulting
`Schema`.

Example:

~~~yaml
fields:
  - name: customer_id
  - name: email
  - name: status
~~~

MUST produce fields in the same semantic order.

---

## DS-FR-004 — Support required and nullable fields

The declarative model MUST represent field nullability.

The resulting `Field.nullable` semantics MUST be equivalent to the Python API.

---

## DS-FR-005 — Support field metadata

The declarative representation MUST support portable field metadata where such
metadata can be represented by the canonical Domain model.

Metadata MUST remain data.

Metadata MUST NOT cause execution behavior during parsing.

---

## DS-FR-006 — Support schema metadata

The declarative representation SHOULD support schema-level descriptive metadata,
including at minimum a human-readable description.

If the canonical `Schema` model cannot retain a given authoring-only property,
the architecture document MUST explicitly decide whether that property belongs to:

- a definition-layer object;
- a sidecar document;
- a future Domain extension.

It MUST NOT be silently dropped.

---

## DS-FR-007 — Export canonical schemas

The system MUST provide a supported path to export a canonical `Schema` into the
declarative representation.

Conceptually:

~~~python
dump_schema(schema, "customers.yml")
~~~

The final function name is not frozen by this document.

---

## DS-FR-008 — In-memory loading

The implementation SHOULD support parsing from an in-memory string or byte-safe
text abstraction in addition to filesystem paths.

This improves:

- testing;
- web-service integration;
- notebook use;
- generated configuration scenarios.

The filesystem MUST NOT be the only possible source.

---

## DS-FR-009 — In-memory export

The implementation SHOULD support exporting a declarative document to a string in
addition to writing directly to a file.

---

## DS-FR-010 — Explicit document version

Every declarative document MUST carry an explicit schema-language version.

Example:

~~~yaml
version: 1
~~~

A document with no version MUST fail unless a future specification explicitly
defines a safe defaulting rule.

The V1 design SHOULD require an explicit version.

---

# 6. Declarative document model requirements

## DS-DOC-001 — Root object

A declarative schema document MUST have a mapping/object as its root value.

Scalar or list roots MUST fail.

---

## DS-DOC-002 — Single-schema and multi-schema forms

The declarative language MAY support both:

~~~yaml
schema:
  ...
~~~

and:

~~~yaml
schemas:
  customers:
    ...
  orders:
    ...
~~~

If both forms are supported, the normative grammar MUST define whether they are
mutually exclusive.

The preferred behavior is fail-closed mutual exclusion.

---

## DS-DOC-003 — Stable schema identity

Named schemas MUST have a stable textual identity.

The identifier rules MUST be documented.

At minimum, the language MUST reject:

- empty names;
- duplicate names;
- names that cannot be represented deterministically.

---

## DS-DOC-004 — Stable field identity

Every field MUST have a non-empty field name.

Duplicate field names within one schema MUST fail.

---

## DS-DOC-005 — Unknown properties

Unknown properties MUST be rejected by default.

Example:

~~~yaml
name: customer_id
type: integer
nulable: false
~~~

MUST fail because `nulable` is not a recognized property.

This requirement prevents silent configuration drift.

---

## DS-DOC-006 — Deterministic defaults

Every optional property with a default MUST have a single documented default.

Defaulting behavior MUST NOT depend on:

- parser implementation;
- operating system;
- locale;
- installed engine;
- environment variables.

---

## DS-DOC-007 — Comments

YAML comments MAY be used by authors.

Semantic round-trip guarantees MUST NOT depend on preserving comments.

---

## DS-DOC-008 — Anchors and aliases

YAML anchors and aliases MUST NOT be assumed to be supported.

Their support status MUST be explicitly decided by the security/parsing policy.

If unsupported, they MUST fail clearly or be rejected before Domain compilation.

---

# 7. Type-system requirements

## DS-TYPE-001 — Domain type ownership

The declarative type vocabulary MUST map to canonical PyTransformKit `DataType`
objects.

The declarative layer MUST NOT introduce an independent logical type system.

---

## DS-TYPE-002 — Primitive types

The declarative format MUST support every stable primitive logical type exposed by
the canonical PyTransformKit type system.

At minimum, the requirements analysis anticipates support for concepts such as:

~~~text
string
boolean
integer
float
date
time
timestamp
binary
~~~

The exact normative vocabulary MUST be derived from the implementation's actual
public `DataType` set.

---

## DS-TYPE-003 — Parameterized types

Parameterized logical types MUST have an explicit structured representation.

For example, a decimal SHOULD be expressible conceptually as:

~~~yaml
type:
  decimal:
    precision: 18
    scale: 2
~~~

Parameters MUST be validated before Domain object creation.

---

## DS-TYPE-004 — Nested types

If the canonical type system exposes nested types, the declarative layer MUST be
able to represent them without using Python expressions.

This includes, where supported by the Domain:

- list/array types;
- map types;
- struct/record types.

---

## DS-TYPE-005 — Recursive type representation

Nested type declarations MUST be recursively validated.

Malformed child types MUST report the exact nested path.

---

## DS-TYPE-006 — Closed type registry

Type names MUST be resolved through a closed registry or equivalent controlled
mapping.

The implementation MUST NOT resolve a type by dynamically importing a user-supplied
Python path.

Forbidden pattern:

~~~yaml
type: my_package.types.CustomType
~~~

if resolution requires arbitrary import and instantiation.

---

## DS-TYPE-007 — Unknown type handling

A misspelled or unrecognized type MUST fail.

Example:

~~~yaml
type: intger
~~~

MUST NOT silently produce `UnknownType`.

---

## DS-TYPE-008 — Explicit Unknown semantics

If PyTransformKit intentionally supports `UnknownType`, the declarative syntax for
requesting it MUST be explicit and normative.

Unknown-by-error and intentionally-unknown MUST remain distinct concepts.

---

## DS-TYPE-009 — Type aliases

Human-friendly aliases MAY exist.

If aliases exist:

- they MUST be explicitly listed;
- they MUST map deterministically to one canonical type;
- aliases MUST NOT create engine-specific semantics.

---

## DS-TYPE-010 — Engine neutrality

Declarative types MUST describe logical PyTransformKit types, not Pandas, Polars,
Arrow or DuckDB physical dtypes.

The following conceptual dependency is required:

~~~text
YAML logical type
      ↓
PyTransformKit DataType
      ↓
engine adapter
      ↓
physical dtype
~~~

---

# 8. Validation requirements

## DS-VAL-001 — Structural validation before compilation

The document MUST be structurally validated before canonical Domain objects are
constructed.

---

## DS-VAL-002 — Strict booleans

Boolean properties SHOULD require boolean YAML values.

Example:

~~~yaml
nullable: false
~~~

is valid.

The string:

~~~yaml
nullable: "false"
~~~

SHOULD be rejected rather than coerced.

---

## DS-VAL-003 — Strict integers

Integer parameters such as decimal precision or scale MUST reject incompatible
scalar types.

---

## DS-VAL-004 — Parameter constraints

Type-specific parameter constraints MUST be validated.

Examples include:

- precision boundaries;
- scale boundaries;
- scale <= precision;
- non-empty nested field sets where required;
- valid map key type constraints if imposed by the Domain.

---

## DS-VAL-005 — Duplicate fields

Duplicate field names MUST fail before runtime execution.

---

## DS-VAL-006 — Duplicate schemas

Duplicate schema identities MUST fail.

---

## DS-VAL-007 — Missing required properties

A missing required property MUST produce a deterministic validation error.

---

## DS-VAL-008 — Mutually exclusive properties

Where grammar properties are mutually exclusive, using both MUST fail.

---

## DS-VAL-009 — No silent property dropping

Recognized but unsupported properties MUST NOT be silently ignored.

---

## DS-VAL-010 — Validation path

Every validation failure SHOULD carry a structural location.

Example:

~~~text
schemas.customers.fields[2].type.decimal.precision
~~~

---

# 9. Error and diagnostic requirements

## DS-ERR-001 — Structured exception hierarchy

Declarative-schema errors MUST integrate with the existing PyTransformKit exception
hierarchy.

They MUST NOT surface only as raw parser exceptions.

---

## DS-ERR-002 — Stable public error codes

Any new public exception contract SHOULD receive a stable machine-readable
`PTK-*` error code consistent with the V1 error catalogue policy.

---

## DS-ERR-003 — Parser error wrapping

Parser-specific exceptions MUST be wrapped or translated into PyTransformKit
diagnostics before crossing the public API boundary.

---

## DS-ERR-004 — Source location

When the parser exposes source location, errors SHOULD include:

- source name/path;
- line;
- column;
- declarative object path.

---

## DS-ERR-005 — Actionable messages

Messages SHOULD identify:

- what is wrong;
- where it is wrong;
- what was expected.

Example:

~~~text
Unknown schema type 'intger' at
schemas.customers.fields[0].type.

Expected one of: integer, string, boolean, ...
~~~

A suggestion such as "Did you mean integer?" MAY be provided when deterministic.

---

## DS-ERR-006 — No parser leakage

Users SHOULD NOT need knowledge of the selected YAML parser to understand common
errors.

---

# 10. Security requirements

## DS-SEC-001 — Safe parsing

The YAML parser MUST operate in a safe mode that cannot instantiate arbitrary
Python objects.

---

## DS-SEC-002 — No eval

The declarative pipeline MUST NOT use `eval`.

---

## DS-SEC-003 — No exec

The declarative pipeline MUST NOT use `exec`.

---

## DS-SEC-004 — No dynamic code imports from declarations

A declaration MUST NOT be able to request arbitrary Python imports.

---

## DS-SEC-005 — Resource limits

The parser/loader SHOULD support defensive limits for potentially hostile
documents.

The security specification MUST consider:

- maximum document size;
- maximum nesting depth;
- maximum number of schemas;
- maximum fields per schema;
- alias expansion behavior.

---

## DS-SEC-006 — YAML alias expansion

The implementation MUST explicitly defend against pathological alias expansion if
aliases are supported by the parser.

---

## DS-SEC-007 — Metadata safety

Metadata MUST be treated as data.

Metadata MUST NOT implicitly cause:

- imports;
- filesystem reads;
- network calls;
- plugin activation;
- engine loading.

---

## DS-SEC-008 — Trust boundary

Declarative files MUST be treated as external input until fully parsed and
validated.

---

# 11. Compatibility requirements

## DS-COMP-001 — No V1 Domain break

Introducing declarative schemas MUST NOT require breaking changes to the stable V1
`Schema`, `Field` or `DataType` APIs.

---

## DS-COMP-002 — Existing Python construction remains valid

Existing code such as:

~~~python
Schema(
    fields=(
        Field("id", IntegerType(), nullable=False),
    )
)
~~~

MUST continue to work unchanged.

---

## DS-COMP-003 — Core import remains lightweight

Importing `pytransformkit` MUST NOT require the YAML capability unless YAML is
made an intentional core dependency by a documented architectural decision.

---

## DS-COMP-004 — Engine independence

Loading and compiling a schema MUST NOT require Pandas, Polars, PyArrow or DuckDB.

---

## DS-COMP-005 — Serialization freeze isolation

Declarative-schema support MUST NOT silently alter existing V1 wire-contract
identifiers or semantics.

Any future serialization change MUST follow the established contract-versioning
rules independently.

---

## DS-COMP-006 — Document version compatibility

The declarative document version MUST be separate from the package version.

Example:

~~~text
PyTransformKit 1.4.0
can still support
declarative schema version 1
~~~

---

# 12. Packaging and dependency requirements

## DS-PKG-001 — Dependency isolation

The YAML parser dependency MUST NOT enter unrelated engine extras.

---

## DS-PKG-002 — Optional-extra decision

The architecture document MUST explicitly decide whether YAML support is:

~~~text
core dependency
~~~

or:

~~~text
optional extra: pytransformkit[yaml]
~~~

No accidental dependency introduction is acceptable.

---

## DS-PKG-003 — Missing optional dependency

If YAML support is optional, invoking YAML-specific APIs without the parser installed
MUST raise a clear capability/dependency error.

Importing unrelated core APIs MUST continue to succeed.

---

## DS-PKG-004 — Version range

Any YAML dependency MUST use a bounded and supportable package-version range.

---

## DS-PKG-005 — No runtime engine dependency

Declarative-schema support MUST NOT pull physical data engines into the core
dependency graph.

---

# 13. Public API requirements

## DS-API-001 — Dedicated namespace

Declarative schema APIs SHOULD live in a dedicated namespace rather than expanding
the root package indiscriminately.

A candidate namespace may resemble:

~~~text
pytransformkit.schema_io
~~~

or:

~~~text
pytransformkit.declarative
~~~

The final namespace will be frozen in the public API specification.

---

## DS-API-002 — Domain objects remain canonical outputs

Public loading APIs MUST return canonical Domain objects or collections thereof.

They MUST NOT expose parser-native YAML nodes as the normal public result.

---

## DS-API-003 — Loader abstraction

The design SHOULD expose an abstraction that allows format-specific loading without
coupling Domain types to YAML.

Conceptually:

~~~text
SchemaDefinitionLoader
        │
        ├── YAML
        └── future format
~~~

---

## DS-API-004 — Compiler separation

Parsing and compilation SHOULD be distinguishable responsibilities.

Conceptually:

~~~text
text
 ↓
loader/parser
 ↓
SchemaDefinition
 ↓
compiler
 ↓
Schema
~~~

---

## DS-API-005 — Exporter abstraction

Exporting SHOULD be separated from Domain objects.

Preferred direction:

~~~python
exporter.dump(schema)
~~~

rather than making `Schema` know about YAML.

---

## DS-API-006 — No Schema.from_yaml dependency inversion

A convenience API MAY eventually exist, but the architecture MUST NOT require the
Domain class itself to import YAML infrastructure.

---

# 14. Round-trip requirements

## DS-RT-001 — Semantic round-trip

The following MUST preserve schema semantics:

~~~text
Schema
  ↓ export
YAML
  ↓ load
Schema'
~~~

where `Schema'` is semantically equivalent to the original.

---

## DS-RT-002 — Textual round-trip not required

The following are not required to be preserved:

- comments;
- indentation;
- quote style;
- key formatting;
- whitespace;
- author-specific YAML layout.

---

## DS-RT-003 — Deterministic export

Given the same canonical `Schema`, exporter output SHOULD be deterministic.

---

## DS-RT-004 — Canonical authoring form

The exporter SHOULD emit one preferred declarative shape even if the parser accepts
multiple equivalent input forms.

---

## DS-RT-005 — Metadata preservation

Supported metadata MUST survive a semantic round-trip.

Unsupported metadata MUST fail or be explicitly documented as authoring-only.

It MUST NOT disappear silently.

---

# 15. Non-functional requirements

## DS-NFR-001 — Determinism

The same valid document MUST produce the same canonical schema semantics.

---

## DS-NFR-002 — Performance

Declarative parsing is an authoring/configuration concern and SHOULD remain
lightweight relative to data execution.

The implementation MUST avoid algorithmic behavior that becomes pathological for
ordinary schema sizes.

---

## DS-NFR-003 — Scalability

The design SHOULD comfortably support:

- hundreds of schemas per repository;
- hundreds of fields per schema;
- nested type definitions.

The exact supported safety limits will be defined separately.

---

## DS-NFR-004 — Readability

The declarative syntax SHOULD optimize for human readability over minimal byte size.

---

## DS-NFR-005 — Diff friendliness

The preferred exported form SHOULD produce stable Git diffs.

---

## DS-NFR-006 — Testability

Parsing, validation and compilation MUST be testable without physical data engines.

---

## DS-NFR-007 — Extensibility

The definition layer SHOULD permit future authoring formats without modifying the
Domain model.

Example:

~~~text
YAML ──┐
JSON ──┼──> SchemaDefinition ──> Schema
TOML ──┘
~~~

This does not imply those formats must be implemented.

---

## DS-NFR-008 — Python support matrix

The declarative feature MUST respect PyTransformKit's supported Python versions.

For the current stable line, qualification must account for Python 3.11 through
3.14 unless the supported matrix changes through normal release policy.

---

## DS-NFR-009 — Documentation

Public declarative APIs MUST be documented with:

- minimal example;
- multi-schema example;
- nested-type example;
- validation-error example;
- migration/equivalence example from Python construction.

---

# 16. YAML-specific requirements

## DS-YAML-001 — Safe loader

A general-purpose unsafe YAML object loader MUST NOT be used.

---

## DS-YAML-002 — YAML feature subset

PyTransformKit MAY intentionally support only a strict subset of YAML.

The supported subset MUST be documented.

---

## DS-YAML-003 — Scalar normalization

YAML scalar interpretation MUST be controlled so that values are not unexpectedly
coerced into unintended logical values.

The implementation MUST investigate parser behavior around values such as:

~~~text
yes
no
on
off
null
2026-10-01
00123
~~~

before freezing the grammar.

---

## DS-YAML-004 — Duplicate mapping keys

Duplicate mapping keys MUST be rejected.

A "last value wins" policy is not acceptable for schema contracts.

---

## DS-YAML-005 — Multi-document YAML

Support for YAML streams containing multiple documents separated by `---` MUST be
explicitly decided.

The default V1 declarative design SHOULD prefer one logical schema document per YAML
document unless there is a demonstrated requirement otherwise.

---

# 17. Definition-layer model requirements

## DS-DEF-001 — Definition objects are not Domain objects

`SchemaDefinition`, `FieldDefinition` and type-definition structures, if
introduced, MUST be authoring/intermediate representations only.

---

## DS-DEF-002 — No engine behavior

Definition objects MUST NOT contain physical engine execution behavior.

---

## DS-DEF-003 — Immutable or controlled representation

Definition objects SHOULD be immutable value objects or otherwise protected from
unexpected mutation during compilation.

---

## DS-DEF-004 — Explicit compiler boundary

There MUST be one clearly defined operation that converts validated definition
objects into canonical Domain objects.

---

## DS-DEF-005 — No hidden compiler side effects

Compilation MUST NOT:

- access the network;
- inspect external engines;
- activate plugins;
- mutate global registries unexpectedly;
- depend on process locale.

---

# 18. Metadata and documentation requirements

## DS-META-001 — Description

Field descriptions SHOULD be supported.

Schema descriptions SHOULD be supported.

---

## DS-META-002 — Portable metadata

Metadata SHOULD be representable as structured values compatible with the Domain's
metadata semantics.

---

## DS-META-003 — No executable metadata

Metadata MUST NOT become an escape hatch for executable configuration.

---

## DS-META-004 — Classification extensibility

The design SHOULD allow governance metadata such as:

~~~yaml
metadata:
  classification: pii
~~~

without baking a mandatory governance taxonomy into the core parser.

---

# 19. Quality-rule boundary

Declarative schemas may eventually coexist with quality rules.

However, V1 declarative-schema support MUST distinguish structural schema definition
from data-quality execution.

The following concern is in scope:

~~~text
field is nullable / non-nullable
~~~

A future concern such as:

~~~yaml
tests:
  - unique
  - accepted_values: [...]
~~~

MUST NOT be assumed to belong to the first implementation unless explicitly added
by the later specification and roadmap.

This prevents accidental recreation of an unrestricted dbt-style DSL.

---

# 20. Source and path requirements

## DS-SRC-001 — Source abstraction

The loader SHOULD be able to identify the source for diagnostics.

Examples:

~~~text
schemas/customers.yml
<memory>
generated-config
~~~

---

## DS-SRC-002 — Filesystem behavior

Filesystem loading MUST use explicit paths supplied by the caller.

The loader MUST NOT scan arbitrary directories by default.

---

## DS-SRC-003 — No implicit network loading

A schema path MUST NOT trigger HTTP/S3/cloud retrieval implicitly.

Remote loading, if ever added, must belong to an explicit integration layer.

---

# 21. Testing requirements

## DS-TEST-001 — Primitive type coverage

Every supported primitive declarative type MUST have positive tests.

---

## DS-TEST-002 — Parameterized type coverage

Every parameterized type MUST have:

- valid examples;
- boundary examples;
- invalid parameter examples.

---

## DS-TEST-003 — Nested type coverage

Nested types MUST be tested recursively.

---

## DS-TEST-004 — Malformed YAML

Malformed YAML MUST produce controlled PyTransformKit errors.

---

## DS-TEST-005 — Security fixtures

Tests MUST cover malicious or dangerous YAML constructs relevant to the selected
parser.

---

## DS-TEST-006 — Unknown properties

Unknown-property rejection MUST be tested.

---

## DS-TEST-007 — Duplicate keys

Duplicate-key rejection MUST be tested.

---

## DS-TEST-008 — Duplicate fields

Duplicate-field rejection MUST be tested.

---

## DS-TEST-009 — Python/YAML equivalence

Reference fixtures MUST prove that equivalent Python and YAML declarations compile
to semantically equivalent `Schema` objects.

---

## DS-TEST-010 — Round-trip

Representative canonical schemas MUST pass semantic export/import round-trip tests.

---

## DS-TEST-011 — Optional dependency isolation

If YAML is optional, CI MUST prove:

~~~text
pip install pytransformkit
import pytransformkit
~~~

works without the YAML dependency.

A separate test MUST prove the YAML feature works when its extra is installed.

---

## DS-TEST-012 — Supported Python matrix

Declarative-schema tests MUST run against the supported Python matrix.

---

# 22. Acceptance scenarios

## DS-ACC-001 — Basic customer schema

Given:

~~~yaml
version: 1

schema:
  name: customers
  fields:
    - name: customer_id
      type: integer
      nullable: false

    - name: email
      type: string
      nullable: true
~~~

the loader/compiler MUST return a canonical `Schema` equivalent to direct Python
construction.

---

## DS-ACC-002 — Invalid type

Given:

~~~yaml
type: intger
~~~

the system MUST reject the document before runtime execution.

---

## DS-ACC-003 — Typo in property

Given:

~~~yaml
nulable: false
~~~

the system MUST reject the field definition.

---

## DS-ACC-004 — Duplicate field

Given two fields named `customer_id` in the same schema, compilation MUST fail.

---

## DS-ACC-005 — Multi-schema document

A valid multi-schema document MUST produce independently addressable canonical
schemas.

---

## DS-ACC-006 — Nested type

A supported nested declarative type MUST compile into the corresponding canonical
nested `DataType`.

---

## DS-ACC-007 — No YAML dependency in Domain

Architecture tests MUST prove that Domain modules do not import the selected YAML
library.

---

## DS-ACC-008 — Round-trip

A representative canonical `Schema` MUST satisfy:

~~~text
schema
  ↓ export
yaml
  ↓ load
schema'
~~~

with semantic equivalence.

---

## DS-ACC-009 — No engine dependency

Loading a schema in an environment without Pandas, Polars, PyArrow and DuckDB MUST
still work.

---

## DS-ACC-010 — Safe parser

A YAML payload attempting Python object construction MUST be rejected and MUST NOT
execute code.

---

# 23. Requirement traceability to the expression of need

| Need from document 28 | Requirement groups |
| --- | --- |
| Reduce authoring verbosity | DS-FR, DS-DOC |
| Keep Schema canonical | INV, DS-COMP, DS-DEF |
| Support logical types | DS-TYPE |
| Strict validation | DS-VAL |
| Actionable errors | DS-ERR |
| Secure parsing | DS-SEC, DS-YAML |
| Keep Python API | DS-COMP |
| Optional YAML capability | DS-PKG |
| Export and round-trip | DS-RT |
| Engine independence | DS-TYPE, DS-COMP |
| Human-readable contracts | DS-NFR, DS-META |
| Avoid DSL sprawl | Quality-rule boundary |

---

# 24. Decisions still open

The following points are deliberately not frozen by this requirements document:

1. exact public namespace;
2. exact YAML library;
3. core dependency vs optional `yaml` extra;
4. exact mono-schema grammar;
5. exact multi-schema grammar;
6. exact logical type names;
7. exact nested-type syntax;
8. whether anchors and aliases are allowed;
9. whether multi-document YAML streams are allowed;
10. exact document size/depth limits;
11. exact exception classes and codes;
12. exact API names;
13. exact exporter canonical formatting;
14. whether schema-level descriptions require Domain evolution;
15. whether quality constraints belong to the first release.

These decisions belong to documents 30 through 40.

---

# 25. Requirements baseline

The first implementation MUST satisfy the following minimum baseline:

~~~text
Declarative YAML
      ↓
safe parse
      ↓
strict structural validation
      ↓
validated SchemaDefinition
      ↓
closed DataType resolution
      ↓
SchemaDefinitionCompiler
      ↓
canonical Schema
~~~

with all of the following properties:

~~~text
Python API preserved                MUST
Domain remains YAML-independent     MUST
Unknown keys rejected               MUST
Unknown types rejected              MUST
Duplicate fields rejected           MUST
Field order preserved               MUST
Nested types supported              MUST, when present in Domain
Parameterized types supported       MUST
Engine independence                 MUST
No arbitrary code execution         MUST
Semantic round-trip                 MUST
Deterministic export                SHOULD
Optional YAML dependency            TO BE DECIDED
Quality-rule DSL                    OUT OF INITIAL SCOPE
~~~

---

# 26. Exit criteria for requirements phase

This requirements phase is complete when:

- every mandatory need from document 28 maps to at least one requirement;
- no requirement requires YAML knowledge inside the Domain;
- the type-system requirements can be mapped to existing canonical types;
- validation behavior is fail-closed;
- security expectations are explicit;
- round-trip expectations are explicit;
- compatibility with the stable V1 public API is explicit;
- packaging choices that remain open are identified;
- architecture can be designed without unresolved ambiguity about responsibility
  boundaries.

---

# 27. Next document

The next document MUST define the architecture satisfying this requirement set:

~~~text
30_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ARCHITECTURE.md
~~~

Its primary responsibility will be to place:

~~~text
SchemaDocument
SchemaDefinition
FieldDefinition
TypeDefinition
YamlSchemaLoader
SchemaDefinitionValidator
SchemaDefinitionCompiler
YamlSchemaExporter
~~~

into the existing PyTransformKit architecture without violating the V1 Domain,
serialization, engine or dependency boundaries.

---

# 28. Summary

The declarative-schema feature is not a replacement for the Python schema API.

It is a controlled authoring layer around the existing Domain.

The requirements baseline is therefore:

~~~text
human-friendly declaration
          +
strict parsing
          +
closed validation
          +
safe type resolution
          +
explicit compilation
          ↓
canonical PyTransformKit Schema
~~~

The core architectural objective remains simple:

> **One schema semantics, multiple authoring surfaces.**

Python remains the programmable authoring surface.

YAML becomes the declarative authoring surface.

Both must converge on the same canonical `Schema` model.
