# 35 — PyTransformKit Declarative Schema — Validation and Error Model

> **Document status:** DRAFT NORMATIVE SPECIFICATION  
> **Depends on:** 31_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SPECIFICATION.md  
> **Depends on:** 32_PYTRANSFORMKIT_DECLARATIVE_TYPE_SYSTEM_MAPPING.md  
> **Depends on:** 33_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_DOMAIN_MODEL.md  
> **Depends on:** 34_PYTRANSFORMKIT_SCHEMA_LOADER_COMPILER_AND_EXPORTER_SPEC.md  
> **Scope:** Validation semantics, diagnostics, exception hierarchy and stable error codes  
> **Declarative language version:** 1

---

# 1. Purpose

This document defines the normative validation and error model for PyTransformKit declarative schemas.

It freezes:

- validation stages;
- failure ownership;
- public exception hierarchy;
- machine-readable PTK error codes;
- source-location semantics;
- declarative object paths;
- parser-error translation;
- duplicate-key behavior;
- unknown-property behavior;
- unknown-type behavior;
- duplicate schema and field behavior;
- cardinality errors;
- optional-dependency errors;
- filesystem errors;
- export errors;
- resource-limit errors;
- exception chaining;
- interaction with existing SchemaError contracts.

The central objective is:

> **Every invalid declarative contract must fail explicitly, deterministically and with enough context to fix the declaration.**

---

# 2. Existing V1 error-contract baseline

PyTransformKit 1.0.0 already freezes public error identities and machine-readable codes through:

~~~text
contracts/error_codes_v1.json
~~~

Existing schema codes are:

~~~text
PTK-SCHEMA-000  SchemaError
PTK-SCHEMA-001  FieldNotFoundError
PTK-SCHEMA-002  DuplicateFieldError
PTK-SCHEMA-003  FieldCollisionError
~~~

These codes describe canonical Domain failures.

Declarative authoring errors MUST NOT reuse or redefine them.

---

# 3. Declarative error namespace

Declarative schema authoring SHALL use a dedicated machine-readable error namespace:

~~~text
PTK-DECL-*
~~~

This separates:

~~~text
authoring / parsing / declarative validation
                from
canonical Schema / Field Domain invariants
~~~

---

# 4. Root declarative exception

The root exception SHOULD be:

~~~python
class DeclarativeSchemaError(PyTransformKitError):
    error_code = ErrorCode("PTK-DECL-000")
~~~

It represents expected failures in declarative schema authoring.

It SHOULD inherit directly from PyTransformKitError rather than SchemaError.

Rationale:

- YAML parsing is not a canonical Schema failure;
- optional-dependency errors are not Schema failures;
- filesystem loading errors are not Schema failures;
- cardinality errors concern authoring documents;
- export errors concern authoring representation.

---

# 5. Proposed public hierarchy

~~~text
PyTransformKitError
└── DeclarativeSchemaError                    PTK-DECL-000
    ├── DeclarativeSchemaParseError           PTK-DECL-001
    │   └── DeclarativeSchemaDuplicateKeyError PTK-DECL-006
    ├── DeclarativeSchemaVersionError         PTK-DECL-002
    ├── DeclarativeSchemaValidationError      PTK-DECL-003
    │   ├── DeclarativeSchemaUnknownPropertyError PTK-DECL-004
    │   ├── DeclarativeSchemaTypeError        PTK-DECL-005
    │   ├── DeclarativeSchemaDuplicateFieldError PTK-DECL-007
    │   └── DeclarativeSchemaDuplicateSchemaError PTK-DECL-008
    ├── DeclarativeSchemaCardinalityError     PTK-DECL-009
    ├── DeclarativeSchemaDependencyError      PTK-DECL-010
    ├── DeclarativeSchemaIOError              PTK-DECL-011
    ├── DeclarativeSchemaExportError          PTK-DECL-012
    └── DeclarativeSchemaLimitError           PTK-DECL-013
~~~

Exact implementation may use additional internal exceptions, but public failures MUST map to this stable hierarchy.

---

# 6. Error-code allocation

| Exception | Code | Parent |
| --- | --- | --- |
| DeclarativeSchemaError | PTK-DECL-000 | PyTransformKitError |
| DeclarativeSchemaParseError | PTK-DECL-001 | DeclarativeSchemaError |
| DeclarativeSchemaVersionError | PTK-DECL-002 | DeclarativeSchemaError |
| DeclarativeSchemaValidationError | PTK-DECL-003 | DeclarativeSchemaError |
| DeclarativeSchemaUnknownPropertyError | PTK-DECL-004 | DeclarativeSchemaValidationError |
| DeclarativeSchemaTypeError | PTK-DECL-005 | DeclarativeSchemaValidationError |
| DeclarativeSchemaDuplicateKeyError | PTK-DECL-006 | DeclarativeSchemaParseError |
| DeclarativeSchemaDuplicateFieldError | PTK-DECL-007 | DeclarativeSchemaValidationError |
| DeclarativeSchemaDuplicateSchemaError | PTK-DECL-008 | DeclarativeSchemaValidationError |
| DeclarativeSchemaCardinalityError | PTK-DECL-009 | DeclarativeSchemaError |
| DeclarativeSchemaDependencyError | PTK-DECL-010 | DeclarativeSchemaError |
| DeclarativeSchemaIOError | PTK-DECL-011 | DeclarativeSchemaError |
| DeclarativeSchemaExportError | PTK-DECL-012 | DeclarativeSchemaError |
| DeclarativeSchemaLimitError | PTK-DECL-013 | DeclarativeSchemaError |

These codes are reserved by this design.

They SHOULD be added to the machine-readable public error catalogue only when the implementation becomes part of a released public API.

---

# 7. Additive compatibility rule

Adding PTK-DECL-* errors after PyTransformKit 1.0.0 is an additive compatibility change.

The implementation MUST NOT:

- renumber existing PTK-SCHEMA-* codes;
- change existing exception parent relationships;
- reuse an existing code;
- modify the meaning of existing V1 exceptions.

---

# 8. Validation stages

Declarative validation occurs in explicit stages:

~~~text
STAGE 1  input/resource checks
STAGE 2  YAML lexical/syntactic parse
STAGE 3  YAML safety/feature checks
STAGE 4  declarative structural decoding
STAGE 5  declarative semantic validation
STAGE 6  type resolution
STAGE 7  canonical Domain construction
STAGE 8  export validation
~~~

Every stage owns a defined failure family.

---

# 9. Stage ownership table

| Stage | Typical failures | Public error family |
| --- | --- | --- |
| Input/resource | missing file, read failure | DeclarativeSchemaIOError |
| YAML parse | malformed YAML | DeclarativeSchemaParseError |
| YAML safety | duplicate key, forbidden tag/alias | ParseError / DuplicateKeyError |
| Structural decode | wrong root, unknown property | ValidationError / UnknownPropertyError |
| Semantic validation | duplicates, invalid parameters | ValidationError subclasses |
| Type resolution | unknown/unsupported type | DeclarativeSchemaTypeError |
| Domain construction | canonical invariant violation | translated declarative validation error with cause |
| Export | unsupported custom DataType, invalid name | DeclarativeSchemaExportError |
| Resource limits | size/depth/count exceeded | DeclarativeSchemaLimitError |

---

# 10. Error context model

Declarative failures SHOULD carry structured diagnostic context.

Recommended immutable value:

~~~python
@dataclass(frozen=True, slots=True)
class DeclarativeErrorContext:
    source: str | None = None
    line: int | None = None
    column: int | None = None
    object_path: str | None = None
~~~

This context is diagnostic state, not canonical Schema state.

---

# 11. Context invariants

source SHOULD identify the caller-visible source when known.

Examples:

~~~text
schemas/customers.yml
<memory>
generated-config
~~~

line and column SHOULD be one-based in user-facing diagnostics.

object_path SHOULD use the deterministic declarative path syntax defined below.

---

# 12. Error instance attributes

Public declarative exceptions SHOULD expose stable attributes where applicable:

~~~text
context
source
line
column
object_path
~~~

Specific subclasses MAY expose additional structured attributes such as:

~~~text
property_name
type_name
field_name
schema_name
expected
actual
supported_versions
required_count
actual_count
dependency_name
path
limit_name
limit
actual_size
~~~

These attributes SHOULD be more stable than parsing human-readable message text.

---

# 13. Human-readable message contract

Error messages SHOULD answer three questions:

1. what failed;
2. where it failed;
3. what was expected.

Example:

~~~text
Unknown declarative type 'intger' at schema.fields[0].type.
Expected one of: string, boolean, int8, int16, int32, int64, ...
~~~

Messages SHOULD remain concise and actionable.

---

# 14. Message stability

Machine consumers MUST use exception type, error code and structured attributes.

Exact punctuation and prose of error messages are NOT a stable compatibility contract unless explicitly frozen by tests.

This permits wording improvements without breaking consumers.

---

# 15. Declarative object-path syntax

Object paths SHOULD use a deterministic dotted/indexed notation.

Examples:

~~~text
version
schema
schema.name
schema.fields[0]
schema.fields[0].type
schema.fields[2].type.decimal.precision
schemas.customers
schemas.customers.fields[1]
schemas.customers.fields[1].type.list.element.type
~~~

---

# 16. Path semantics

Object paths describe declarative semantic position, not YAML parser-node identity.

They MUST remain useful even when line/column information is unavailable.

They SHOULD be format-neutral enough to survive future non-YAML adapters.

---

# 17. Source location

When parser support allows it, parse/decode errors SHOULD carry line and column.

Example rendered diagnostic:

~~~text
schemas/customers.yml:14:11 [PTK-DECL-005]
Unknown declarative type 'intger'
at schema.fields[2].type.
~~~

---

# 18. Source location fallback

When line and column cannot be recovered, the error MUST still contain:

- error type;
- machine-readable code;
- object path when known;
- actionable message.

Lack of line/column MUST NOT cause the underlying validation failure to be lost.

---

# 19. DeclarativeSchemaParseError — PTK-DECL-001

This error represents malformed YAML or syntax-level parsing failures that prevent safe structural decoding.

Examples:

~~~text
invalid indentation
unterminated quoted scalar
malformed flow mapping
unexpected document token
invalid YAML syntax
~~~

Underlying parser exceptions SHOULD be chained.

---

# 20. Parser exception translation

Raw parser exceptions MUST NOT cross the public API boundary as the primary exception contract.

Required pattern:

~~~python
try:
    ...
except YamlLibraryError as exc:
    raise DeclarativeSchemaParseError(...) from exc
~~~

This preserves implementation independence.

---

# 21. DeclarativeSchemaDuplicateKeyError — PTK-DECL-006

Duplicate YAML mapping keys require a dedicated parse failure because last-value-wins behavior is forbidden.

Invalid:

~~~yaml
nullable: true
nullable: false
~~~

The error SHOULD expose:

~~~text
key
context
~~~

and SHOULD identify both locations when the parser makes them available.

---

# 22. Duplicate keys vs duplicate fields

These are distinct failures.

Duplicate YAML key:

~~~yaml
nullable: true
nullable: false
~~~

is PTK-DECL-006.

Duplicate declarative field names:

~~~yaml
fields:
  - name: id
    type: int64
  - name: id
    type: string
~~~

is PTK-DECL-007.

---

# 23. DeclarativeSchemaVersionError — PTK-DECL-002

This error represents an unsupported or invalid declarative-language version.

Examples:

~~~yaml
version: 2
~~~

~~~yaml
version: "1"
~~~

The exception SHOULD expose:

~~~text
actual_version
supported_versions
context
~~~

---

# 24. Missing version

A missing required version is a declarative validation failure.

It MAY be represented by DeclarativeSchemaVersionError because the semantic problem is specifically document versioning.

Preferred policy:

~~~text
missing version            → PTK-DECL-002
unsupported version        → PTK-DECL-002
wrong version scalar type  → PTK-DECL-002
~~~

---

# 25. DeclarativeSchemaValidationError — PTK-DECL-003

This is the general semantic/structural validation failure.

It covers invalid declarative input that does not require a more specific public subclass.

Examples include:

~~~text
wrong root shape
schema and schemas both present
neither schema nor schemas present
missing required fields property
invalid scalar type
blank schema name
blank field name
invalid nested holder shape
invalid temporal unit
invalid decimal constraints
~~~

---

# 26. DeclarativeSchemaUnknownPropertyError — PTK-DECL-004

Unknown properties MUST fail closed.

Invalid:

~~~yaml
- name: customer_id
  type: int64
  nulable: false
~~~

The exception SHOULD expose:

~~~text
property_name
allowed_properties
context
~~~

Example message:

~~~text
Unknown property 'nulable' at schema.fields[0].
Expected one of: name, type, nullable, description.
~~~

---

# 27. Unknown root property

Example:

~~~yaml
version: 1
schema: ...
owner: data-team
~~~

must raise PTK-DECL-004.

Unknown-property rejection applies recursively at every grammar level.

---

# 28. DeclarativeSchemaTypeError — PTK-DECL-005

This error represents failures in declarative logical type syntax or semantics.

It includes:

- unknown type name;
- malformed structured type;
- unsupported type parameters;
- invalid integer width after normalized construction;
- invalid float width;
- invalid decimal parameters;
- invalid temporal unit;
- blank timestamp timezone;
- malformed list/struct/map type definitions.

---

# 29. Unknown type

Invalid:

~~~yaml
type: intger
~~~

must raise PTK-DECL-005.

It MUST NOT produce UnknownType.

The exception SHOULD expose:

~~~text
type_name
expected_type_names
context
~~~

---

# 30. Intentional UnknownType

This is valid:

~~~yaml
type: unknown
~~~

It compiles to canonical UnknownType.

The distinction is mandatory:

~~~text
unknown      = valid intentional logical type
intger       = invalid unknown declaration
~~~

---

# 31. Invalid decimal

Example:

~~~yaml
type:
  decimal:
    precision: 10
    scale: 11
~~~

must raise PTK-DECL-005.

The diagnostic SHOULD point to:

~~~text
schema.fields[N].type.decimal.scale
~~~

and explain that scale must not exceed precision.

---

# 32. Invalid temporal unit

Example:

~~~yaml
type:
  timestamp:
    unit: microseconds
~~~

must raise PTK-DECL-005.

Expected units:

~~~text
s
ms
us
ns
~~~

---

# 33. DeclarativeSchemaDuplicateFieldError — PTK-DECL-007

This error represents duplicate logical field names within one declarative schema or nested struct.

The exception SHOULD expose:

~~~text
field_name
context
first_context when available
~~~

---

# 34. Top-level duplicate field

Invalid:

~~~yaml
fields:
  - name: customer_id
    type: int64
  - name: customer_id
    type: string
~~~

must raise PTK-DECL-007 before canonical Schema construction.

---

# 35. Nested duplicate field

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

also raises PTK-DECL-007.

The object path MUST identify the nested struct context.

---

# 36. Relationship with DuplicateFieldError

Canonical Domain DuplicateFieldError remains:

~~~text
PTK-SCHEMA-002
~~~

Declarative validation SHOULD detect duplicates earlier and raise:

~~~text
PTK-DECL-007
~~~

If canonical construction unexpectedly raises DuplicateFieldError, the compiler MAY translate it into DeclarativeSchemaDuplicateFieldError while preserving the original exception as the cause.

---

# 37. DeclarativeSchemaDuplicateSchemaError — PTK-DECL-008

This error represents duplicate schema identities in one normalized SchemaDocument.

The exception SHOULD expose:

~~~text
schema_name
context
first_context when available
~~~

Duplicate YAML mapping keys may be caught earlier as PTK-DECL-006.

PTK-DECL-008 remains useful for programmatically constructed SchemaDocument values or non-YAML future adapters.

---

# 38. DeclarativeSchemaCardinalityError — PTK-DECL-009

This error represents a mismatch between the helper contract and number of schemas in a document.

Primary case:

~~~text
loads_schema / load_schema
requires exactly one schema
~~~

but the document contains zero or multiple schemas.

The exception SHOULD expose:

~~~text
required_count
actual_count
context
~~~

---

# 39. Cardinality example

Given a two-schema document, this call:

~~~python
load_schema("schemas.yml")
~~~

must raise PTK-DECL-009.

The message SHOULD direct the user toward load_schemas.

---

# 40. DeclarativeSchemaDependencyError — PTK-DECL-010

This error represents unavailable optional declarative-schema dependencies.

Primary case:

~~~text
YAML capability invoked
but selected YAML parser is not installed
~~~

The exception SHOULD expose:

~~~text
dependency_name
extra_name
~~~

Recommended message:

~~~text
YAML declarative schema support requires the optional 'yaml' extra.
Install with: pip install "pytransformkit[yaml]"
~~~

---

# 41. Dependency error import boundary

Missing YAML support MUST NOT cause:

~~~python
import pytransformkit
~~~

to fail.

PTK-DECL-010 is raised only when YAML-specific functionality is invoked.

---

# 42. DeclarativeSchemaIOError — PTK-DECL-011

This error represents filesystem failures in declarative load/dump helpers.

Examples:

- file not found;
- permission denied;
- path is a directory when file expected;
- UTF-8 decode failure;
- write failure.

The exception SHOULD expose:

~~~text
path
operation
context
~~~

---

# 43. I/O error cause

Underlying OSError, UnicodeError or related exceptions SHOULD be chained.

Example:

~~~python
raise DeclarativeSchemaIOError(...) from exc
~~~

The public API does not require consumers to depend on operating-system-specific exception classes.

---

# 44. DeclarativeSchemaExportError — PTK-DECL-012

This error represents failures while converting canonical Domain state into declarative schema V1.

Examples:

- unsupported custom DataType subclass;
- missing or blank required declarative schema name;
- canonical state not representable by declarative V1;
- internal exporter exhaustiveness failure.

---

# 45. Unsupported custom type export

Given:

~~~python
class MyCustomType(DataType):
    ...
~~~

attempting declarative export MUST raise PTK-DECL-012.

The exporter MUST NOT emit repr or Python-qualified class names.

---

# 46. DeclarativeSchemaLimitError — PTK-DECL-013

This error represents defensive resource-limit violations.

Potential limits include:

~~~text
document bytes
nesting depth
schema count
fields per schema
total field count
alias count if aliases ever become supported
~~~

The exception SHOULD expose:

~~~text
limit_name
limit
actual
context
~~~

---

# 47. Limit errors are not parse errors

A syntactically valid document may still exceed configured safe bounds.

Therefore resource-limit failures use PTK-DECL-013 rather than PTK-DECL-001.

This distinction makes operational policy explicit.

---

# 48. Strict boolean validation

Valid:

~~~yaml
nullable: false
~~~

Invalid:

~~~yaml
nullable: "false"
~~~

The invalid form raises PTK-DECL-003.

No string-to-boolean coercion is allowed.

---

# 49. Strict integer validation

Valid:

~~~yaml
precision: 18
~~~

Invalid:

~~~yaml
precision: "18"
~~~

The invalid form raises PTK-DECL-005 when inside a type parameter.

---

# 50. Explicit null validation

Declarative V1 uses omission rather than explicit null for optional authoring properties.

Invalid:

~~~yaml
description: null
~~~

Invalid:

~~~yaml
timezone: null
~~~

These failures SHOULD map to PTK-DECL-003 or PTK-DECL-005 according to the property owner.

---

# 51. Root-shape validation

A non-mapping root raises PTK-DECL-003.

Invalid:

~~~yaml
- version: 1
- schema: customers
~~~

The object path may be represented as:

~~~text
$
~~~

or another documented root marker.

---

# 52. schema vs schemas exclusivity

Invalid:

~~~yaml
version: 1
schema:
  name: customers
  fields: []
schemas:
  orders:
    fields: []
~~~

must raise PTK-DECL-003.

Exactly one of schema or schemas is required.

---

# 53. Required property validation

Missing required properties raise PTK-DECL-003 unless a more specific error family applies.

Examples:

~~~text
schema.name missing
schema.fields missing
field.name missing
field.type missing
list.element missing
map.key missing
map.value missing
decimal.precision missing
decimal.scale missing
~~~

---

# 54. Unsupported YAML features

Declarative V1 rejects:

~~~text
anchors
aliases
merge keys
custom tags
multi-document streams
~~~

These SHOULD normally raise PTK-DECL-001 because they are rejected at the YAML adapter boundary.

A duplicate key uses the dedicated PTK-DECL-006 subtype.

---

# 55. Templating and interpolation

Jinja and environment interpolation are not evaluated.

If such syntax parses as an ordinary string but violates the declarative grammar, the resulting error is a validation/type error, not a template-engine error.

No template engine is invoked.

---

# 56. Validation ordering

When multiple independent errors exist, V1 SHOULD report the first deterministic failure according to document traversal order.

Recommended order:

~~~text
root/version
schema declaration order
field order
nested type depth-first order
~~~

This avoids nondeterministic error selection.

---

# 57. Single-error vs aggregate validation

Declarative V1 SHOULD use fail-fast single-error exceptions.

Rationale:

- simpler public contract;
- deterministic source location;
- no aggregate-error schema required;
- easier compatibility management.

A future lint API MAY collect multiple diagnostics separately.

---

# 58. Future linting boundary

A future non-throwing API could return:

~~~text
tuple[DeclarativeDiagnostic, ...]
~~~

for editor/CI linting.

This is separate from load_schema semantics.

Normal load functions remain fail-closed.

---

# 59. Domain-construction failure translation

Declarative validation should catch user-facing problems before Domain construction.

However, canonical constructors remain authoritative.

If a canonical constructor raises a known Domain error during compilation, the compiler SHOULD:

1. preserve the original exception as cause;
2. translate to the closest declarative error when authoring context exists;
3. never suppress the invariant failure.

---

# 60. ValueError translation

Current DataType constructors may use ValueError for local invariant failures.

Such ValueError instances MUST NOT leak from high-level declarative load APIs when they result from authored declarative input.

They SHOULD be translated to PTK-DECL-005 or PTK-DECL-003 with exception chaining.

---

# 61. TypeError translation

Unexpected Python TypeError caused by invalid declarative values SHOULD similarly be translated when the failure can be attributed to user input.

Programming bugs inside PyTransformKit SHOULD NOT be indiscriminately swallowed or reclassified.

Translation must remain narrow and intentional.

---

# 62. Internal bugs

The error model MUST NOT turn every implementation bug into DeclarativeSchemaValidationError.

For example, an unexpected AttributeError caused by a coding defect SHOULD propagate during development/testing unless a deliberate translation boundary applies.

This preserves debuggability.

---

# 63. Error wrapping rule

Only expected external/input failures are translated into public declarative errors.

Unexpected internal failures are not silently normalized.

Rule:

~~~text
known input failure      → public PTK-DECL-* error
known dependency failure → public PTK-DECL-* error
known I/O failure        → public PTK-DECL-* error
unexpected code defect   → do not disguise
~~~

---

# 64. Exception chaining rule

Whenever a declarative error wraps another exception:

~~~python
raise PublicDeclarativeError(...) from exc
~~~

SHOULD be used.

This retains root-cause evidence in __cause__.

---

# 65. Security-sensitive messages

Errors MUST NOT leak secrets or arbitrary environment contents.

Messages MAY contain:

- explicit caller-provided path;
- schema/field/type names;
- bounded snippets if safe.

They SHOULD NOT dump the entire source document on failure.

---

# 66. Source-snippet policy

Source snippets MAY be included in diagnostics, but they are not required.

If included, they SHOULD be:

- bounded in length;
- limited to relevant lines;
- safely escaped;
- omitted from machine-readable exception identity.

---

# 67. Error rendering

A human-readable renderer MAY format:

~~~text
[PTK-DECL-005] schemas/customers.yml:18:9
Unknown declarative type 'intger'
at schema.fields[2].type.
Expected one of: int8, int16, int32, int64, ...
~~~

Rendering is separate from exception identity.

---

# 68. Public exception constructors

Public exception constructors SHOULD prefer structured arguments over preformatted free text.

Example:

~~~python
DeclarativeSchemaTypeError(
    type_name="intger",
    expected_type_names=("int8", "int16", "int32", "int64", ...),
    context=context,
)
~~~

The exception constructs its own user-facing message.

---

# 69. Error context convenience properties

If exceptions store context as one object, convenience properties MAY expose:

~~~python
error.source
error.line
error.column
error.object_path
~~~

These SHOULD delegate to the immutable context.

---

# 70. Proposed base exception shape

Conceptually:

~~~python
class DeclarativeSchemaError(PyTransformKitError):
    error_code = ErrorCode("PTK-DECL-000")

    def __init__(
        self,
        message: str,
        *,
        context: DeclarativeErrorContext | None = None,
    ) -> None:
        self.context = context
        super().__init__(message)
~~~

Exact constructor signatures are frozen later with the public API.

---

# 71. Proposed TypeError shape

Conceptually:

~~~python
class DeclarativeSchemaTypeError(DeclarativeSchemaValidationError):
    error_code = ErrorCode("PTK-DECL-005")

    def __init__(
        self,
        type_name: str | None = None,
        *,
        expected_type_names: tuple[str, ...] = (),
        context: DeclarativeErrorContext | None = None,
        message: str | None = None,
    ) -> None:
        ...
~~~

The public API specification will decide how much constructor surface becomes stable.

---

# 72. Public catalogue integration

When implementation lands, every public PTK-DECL-* exception MUST be added to the repository's machine-readable error-code contract.

The compatibility gate MUST verify:

~~~text
unique code
public exception name
parent hierarchy
machine-readable code
~~~

as it already does for existing errors.

---

# 73. Root export policy

Declarative errors SHOULD be exported through:

~~~python
from pytransformkit.errors import DeclarativeSchemaError
~~~

if document 38 classifies them as stable public errors.

They SHOULD NOT be added to the pytransformkit package root merely for convenience.

---

# 74. Existing SchemaError compatibility

Existing code such as:

~~~python
except SchemaError:
    ...
~~~

does not automatically catch declarative parser errors.

This is intentional.

A declarative YAML syntax failure is not the same semantic category as a canonical Schema failure.

---

# 75. Catching all declarative failures

Users SHOULD be able to write:

~~~python
try:
    schema = load_schema("customers.yml")
except DeclarativeSchemaError as exc:
    ...
~~~

to catch all expected declarative-schema failures.

---

# 76. Catching all PyTransformKit failures

Existing broad handling remains valid:

~~~python
except PyTransformKitError:
    ...
~~~

because DeclarativeSchemaError inherits from PyTransformKitError.

---

# 77. Validation examples matrix

| Invalid input | Error | Code |
| --- | --- | --- |
| malformed YAML | DeclarativeSchemaParseError | PTK-DECL-001 |
| unsupported version | DeclarativeSchemaVersionError | PTK-DECL-002 |
| wrong root shape | DeclarativeSchemaValidationError | PTK-DECL-003 |
| unknown property | DeclarativeSchemaUnknownPropertyError | PTK-DECL-004 |
| unknown type | DeclarativeSchemaTypeError | PTK-DECL-005 |
| duplicate YAML key | DeclarativeSchemaDuplicateKeyError | PTK-DECL-006 |
| duplicate field name | DeclarativeSchemaDuplicateFieldError | PTK-DECL-007 |
| duplicate schema name | DeclarativeSchemaDuplicateSchemaError | PTK-DECL-008 |
| single helper + multi document | DeclarativeSchemaCardinalityError | PTK-DECL-009 |
| YAML dependency missing | DeclarativeSchemaDependencyError | PTK-DECL-010 |
| file read/write failure | DeclarativeSchemaIOError | PTK-DECL-011 |
| unexportable DataType | DeclarativeSchemaExportError | PTK-DECL-012 |
| resource bound exceeded | DeclarativeSchemaLimitError | PTK-DECL-013 |

---

# 78. Positive validation baseline

A document is valid only after all relevant stages succeed:

~~~text
safe YAML parse
      +
supported feature subset
      +
strict structural decode
      +
semantic validation
      +
type resolution
      +
canonical Domain construction
~~~

No individual successful stage is enough by itself.

---

# 79. Validation of generated documents

Exporter-generated SchemaDocument values SHOULD pass the same validator used for parsed documents.

If exporter output fails validation, this is an implementation defect or unsupported Domain state and SHOULD surface as PTK-DECL-012 with a chained cause where appropriate.

---

# 80. Round-trip error behavior

During:

~~~text
Schema
 ↓ export
YAML
 ↓ parse
Schema'
~~~

any inability to represent canonical state MUST fail at export.

The emitter MUST NOT silently degrade the schema to make round-trip succeed.

---

# 81. Test requirements — hierarchy

Tests MUST verify:

~~~text
every public exception inherits PyTransformKitError
every PTK-DECL subclass inherits DeclarativeSchemaError
specific parent relationships match the frozen catalogue
all public error codes are unique
all error codes match PTK-DECL-NNN
~~~

---

# 82. Test requirements — parsing

Tests MUST cover:

~~~text
malformed YAML
duplicate keys
custom tags
anchors
aliases
merge keys
multi-document streams
controlled scalar parsing
~~~

Parser-specific exceptions MUST remain chained, not primary.

---

# 83. Test requirements — validation

Tests MUST cover:

~~~text
missing version
unsupported version
schema + schemas
missing schema/schemas
unknown root property
unknown field property
blank names
duplicate schemas
duplicate fields
nested duplicates
wrong nullable scalar type
invalid decimal
invalid temporal unit
invalid list/map/struct shape
~~~

---

# 84. Test requirements — diagnostics

Tests SHOULD verify:

~~~text
source path
line
column
object_path
structured subclass attributes
exception chaining
stable error code
~~~

Exact full prose SHOULD be tested sparingly.

---

# 85. Test requirements — dependency and I/O

Tests MUST cover:

~~~text
core import without YAML extra
YAML call without YAML extra
missing file
permission/read failure where portable
invalid UTF-8 input
write failure where portable
~~~

---

# 86. Test requirements — cardinality

Tests MUST cover:

~~~text
load_schema with exactly one schema → success
load_schema with multiple schemas   → PTK-DECL-009
load_schemas with one schema        → success
load_schemas with many schemas      → success
~~~

---

# 87. Test requirements — Domain translation

Tests SHOULD intentionally exercise a path where canonical construction fails despite declarative pre-validation.

The resulting public declarative error MUST retain the original Domain exception as __cause__.

---

# 88. Error-catalogue qualification

When implementation becomes release-candidate quality, CI SHOULD verify:

~~~text
contracts/error_codes_v1.json or successor
        ↓
public exception hierarchy
        ↓
exact codes
        ↓
unique identities
        ↓
PASS / FAIL
~~~

If a post-1.0 successor catalogue is introduced, it must preserve all V1 entries unchanged.

---

# 89. Decisions frozen by this document

## DEC-ERR-01

Declarative authoring uses a dedicated PTK-DECL-* namespace.

## DEC-ERR-02

DeclarativeSchemaError inherits directly from PyTransformKitError.

## DEC-ERR-03

Existing PTK-SCHEMA-* codes are not reused.

## DEC-ERR-04

Parser-library exceptions do not cross the public boundary as primary errors.

## DEC-ERR-05

Unknown properties fail closed.

## DEC-ERR-06

Unknown type names raise PTK-DECL-005 and never become UnknownType.

## DEC-ERR-07

Duplicate YAML keys and duplicate logical fields are distinct errors.

## DEC-ERR-08

Single-schema cardinality mismatch has a dedicated error.

## DEC-ERR-09

Optional dependency failure has a dedicated error.

## DEC-ERR-10

I/O failures are wrapped while preserving the cause.

## DEC-ERR-11

Unsupported export state fails explicitly.

## DEC-ERR-12

Resource-limit violations have a dedicated error.

## DEC-ERR-13

Source context is diagnostic, not semantic Domain state.

## DEC-ERR-14

Normal loading is fail-fast rather than aggregate-error.

## DEC-ERR-15

Expected wrapped failures use Python exception chaining.

---

# 90. Acceptance criteria

The validation/error model is complete when:

1. every invalid declarative category maps deterministically to one public error family;
2. every public declarative error has a unique PTK-DECL-* code;
3. no existing V1 error code changes meaning;
4. parser-specific exceptions are wrapped;
5. source and object path can be carried when available;
6. unknown properties fail;
7. unknown types fail;
8. duplicate YAML keys fail before last-value-wins behavior;
9. duplicate fields fail before canonical Schema construction;
10. cardinality mismatch is explicit;
11. missing YAML dependency does not break core import;
12. I/O failures retain root causes;
13. export cannot silently lose semantics;
14. resource limits fail with a distinct error;
15. expected Domain-construction failures can be translated with cause preservation;
16. unexpected internal programming defects are not indiscriminately disguised;
17. error catalogue compatibility can be enforced by CI.

---

# 91. Next document

The next document freezes the security and concrete parsing policy:

~~~text
36_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SECURITY_AND_PARSING_POLICY.md
~~~

It must decide:

~~~text
YAML parser dependency
safe loader mode
duplicate-key enforcement
custom-tag rejection
anchor/alias rejection
merge-key rejection
scalar resolver behavior
document byte limit
nesting-depth limit
schema/field count limits
DoS resistance
optional extra packaging
parser hardening tests
~~~

---

# 92. Final summary

The declarative error system creates a dedicated authoring boundary:

~~~text
YAML / filesystem / declarative authoring
              ↓
         PTK-DECL-*
              ↓
SchemaDefinitionCompiler
              ↓
canonical Domain
              ↓
         PTK-SCHEMA-*
~~~

The two families are intentionally related but not conflated.

The governing rule is:

> **Authoring failures identify the declaration that is wrong; Domain failures protect the canonical model that must never become wrong.**