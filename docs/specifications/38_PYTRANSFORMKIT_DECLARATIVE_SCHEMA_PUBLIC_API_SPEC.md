# 38 — PyTransformKit Declarative Schema — Public API Specification

> **Document status:** DRAFT NORMATIVE SPECIFICATION  
> **Depends on:** 30_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ARCHITECTURE.md  
> **Depends on:** 31_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SPECIFICATION.md  
> **Depends on:** 34_PYTRANSFORMKIT_SCHEMA_LOADER_COMPILER_AND_EXPORTER_SPEC.md  
> **Depends on:** 35_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_VALIDATION_AND_ERROR_MODEL.md  
> **Depends on:** 36_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SECURITY_AND_PARSING_POLICY.md  
> **Depends on:** 37_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ROUNDTRIP_AND_SERIALIZATION_MODEL.md  
> **Compatibility baseline:** PyTransformKit 1.0 public API freeze  
> **Declarative language version:** 1  
> **Target release line:** to be finalized by document 40

---

# 1. Purpose

This document freezes the intended public Python API for declarative schema authoring in PyTransformKit.

It decides:

- the stable public namespace;
- the stable loading functions;
- the stable dumping functions;
- exact function semantics;
- public exception exposure;
- optional dependency behavior;
- root-export policy;
- typing expectations;
- file/path behavior;
- ordering behavior;
- naming behavior;
- stability classification;
- compatibility obligations;
- which internal services remain non-public.

The core public design is intentionally small:

~~~python
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
~~~

---

# 2. Public API principle

Declarative schema support SHOULD feel like a small authoring capability around the existing Schema Domain, not like a second framework surface.

The stable API therefore exposes:

~~~text
high-level load/dump functions
public declarative errors
one optional YAML extra
~~~

and keeps parser/compiler implementation details internal.

---

# 3. Public namespace decision

The stable qualified namespace SHALL be:

~~~text
pytransformkit.schema_io
~~~

This name is preferred over a broad pytransformkit.declarative namespace because the capability is intentionally restricted to schema authoring and serialization-like I/O.

It avoids implying that transformations, plans or workflows are also configurable through a general declarative DSL.

---

# 4. Why not pytransformkit.declarative

A namespace named declarative would create unnecessary semantic room for:

~~~text
declarative transformations
declarative pipelines
declarative workflows
declarative runtime configuration
~~~

None of those capabilities is part of this feature.

schema_io keeps the boundary explicit.

---

# 5. Why not Domain methods

The public feature MUST NOT be exposed primarily as:

~~~python
Schema.from_yaml(...)
schema.to_yaml(...)
~~~

because that would make YAML an apparent responsibility of the canonical Domain object.

The Domain remains representation-independent.

---

# 6. Root package policy

No declarative schema function is added to:

~~~python
pytransformkit.__all__
~~~

Therefore this is intentionally NOT canonical usage:

~~~python
from pytransformkit import load_schema
~~~

The existing small stable root remains unchanged.

---

# 7. Root namespace convenience policy

pytransformkit.schema_io MAY be importable as a normal Python submodule:

~~~python
import pytransformkit.schema_io
~~~

but schema_io SHOULD NOT be added as a required convenience symbol in pytransformkit.__all__.

This minimizes additive root-surface growth.

---

# 8. Stable schema_io __all__

The stable namespace SHOULD define exactly these initial public functions:

~~~python
__all__ = [
    "dump_schema",
    "dump_schemas",
    "dumps_schema",
    "dumps_schemas",
    "load_schema",
    "load_schemas",
    "loads_schema",
    "loads_schemas",
]
~~~

Parser/compiler classes are not included.

---

# 9. Stable public functions

The stable function set is:

| Function | Input | Output | Purpose |
| --- | --- | --- | --- |
| load_schema | path | Schema | load exactly one schema |
| loads_schema | text | Schema | parse exactly one schema |
| load_schemas | path | dict[str, Schema] | load one or more named schemas |
| loads_schemas | text | dict[str, Schema] | parse one or more named schemas |
| dump_schema | Schema + path + name | None | write one schema |
| dumps_schema | Schema + name | str | emit one schema |
| dump_schemas | Mapping[str, Schema] + path | None | write named schemas |
| dumps_schemas | Mapping[str, Schema] | str | emit named schemas |

---

# 10. load_schema signature

Normative signature:

~~~python
def load_schema(
    path: str | os.PathLike[str],
) -> Schema:
    ...
~~~

The helper reads one UTF-8 YAML document from the exact supplied path.

It requires the document to contain exactly one declarative schema.

---

# 11. load_schema semantics

load_schema performs:

~~~text
read exact path
 ↓
UTF-8 decode
 ↓
secure YAML parse
 ↓
strict declarative decode
 ↓
validation
 ↓
single-schema cardinality check
 ↓
compile
 ↓
Schema
~~~

The declarative schema name is not injected into the returned Schema.

---

# 12. load_schema cardinality

If the document contains multiple schemas, load_schema MUST raise:

~~~text
DeclarativeSchemaCardinalityError
PTK-DECL-009
~~~

It MUST NOT silently choose the first schema.

---

# 13. loads_schema signature

Normative signature:

~~~python
def loads_schema(
    text: str,
    *,
    source: str | None = None,
) -> Schema:
    ...
~~~

The public in-memory API accepts str, not arbitrary parser-native values.

---

# 14. loads_schema source parameter

source is optional diagnostic context.

Example:

~~~python
schema = loads_schema(
    yaml_text,
    source="generated/customers.yml",
)
~~~

source affects diagnostics only.

It MUST NOT affect Schema equality or fingerprinting.

---

# 15. No public bytes overload

Declarative V1 does NOT freeze a public bytes overload for loads_schema.

Callers with bytes should decode UTF-8 explicitly or use the filesystem helper.

This keeps the stable signature narrow.

---

# 16. load_schemas signature

Normative signature:

~~~python
def load_schemas(
    path: str | os.PathLike[str],
) -> dict[str, Schema]:
    ...
~~~

The result maps declarative schema names to canonical Schema values.

---

# 17. loads_schemas signature

Normative signature:

~~~python
def loads_schemas(
    text: str,
    *,
    source: str | None = None,
) -> dict[str, Schema]:
    ...
~~~

Both one-schema and multi-schema documents are valid for this API.

---

# 18. Multi-schema ordering

The returned dict MUST preserve declarative schema declaration order.

Example:

~~~yaml
schemas:
  customers:
    fields: []
  orders:
    fields: []
~~~

produces iteration order:

~~~text
customers
orders
~~~

---

# 19. Multi-schema atomicity

load_schemas and loads_schemas are document-atomic.

If any schema is invalid, no partial mapping is returned.

---

# 20. dumps_schema signature

Normative signature:

~~~python
def dumps_schema(
    schema: Schema,
    *,
    name: str,
) -> str:
    ...
~~~

name is keyword-only and required.

---

# 21. Explicit schema name

The exporter MUST NOT infer name from:

- a Python variable;
- a filesystem path;
- repr(schema);
- hidden attributes;
- global registries.

This remains explicit:

~~~python
text = dumps_schema(
    schema,
    name="customers",
)
~~~

---

# 22. dumps_schema output

dumps_schema returns canonical declarative YAML text.

The returned str MUST:

- be deterministic under the same emitter version;
- use canonical declarative type names;
- preserve Schema field order;
- include declarative version 1;
- include exactly one schema declaration;
- end with one final newline.

---

# 23. dump_schema signature

Normative signature:

~~~python
def dump_schema(
    schema: Schema,
    path: str | os.PathLike[str],
    *,
    name: str,
) -> None:
    ...
~~~

The function writes UTF-8 YAML to the exact caller-provided path.

---

# 24. dump_schema overwrite behavior

V1 SHALL overwrite the exact target file if it already exists and is writable.

It MUST NOT:

- infer a different output path;
- create backup files implicitly;
- scan directories;
- generate multiple files;
- infer name from path.

Parent directories are not created implicitly.

---

# 25. Atomic-write guarantee

V1 does NOT freeze atomic filesystem replacement as a public semantic guarantee.

The implementation MAY use a safe atomic-write strategy internally.

Callers must not depend on a particular temporary-file algorithm.

---

# 26. dumps_schemas signature

Normative signature:

~~~python
def dumps_schemas(
    schemas: Mapping[str, Schema],
) -> str:
    ...
~~~

Mapping keys become declarative schema names.

---

# 27. dumps_schemas ordering

dumps_schemas MUST preserve input Mapping iteration order.

It MUST NOT alphabetically sort schema names by default.

This supports intentional human ordering and stable Git diffs.

---

# 28. dumps_schemas validation

Every mapping key MUST be a valid non-empty declarative schema name.

Every mapping value MUST be a canonical Schema.

Duplicate names are structurally impossible in a Mapping but programmatically malformed mappings or values still fail validation/export explicitly.

---

# 29. dump_schemas signature

Normative signature:

~~~python
def dump_schemas(
    schemas: Mapping[str, Schema],
    path: str | os.PathLike[str],
) -> None:
    ...
~~~

It writes one declarative YAML document containing the supplied named schemas.

---

# 30. Public API examples

Single schema from file:

~~~python
from pytransformkit.schema_io import load_schema

schema = load_schema("schemas/customers.yml")
~~~

---

# 31. In-memory authoring example

~~~python
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
""",
    source="<example>",
)
~~~

---

# 32. Single-schema export example

~~~python
from pytransformkit.schema_io import dumps_schema

yaml_text = dumps_schema(
    schema,
    name="customers",
)
~~~

---

# 33. Multi-schema example

~~~python
from pytransformkit.schema_io import (
    dumps_schemas,
    loads_schemas,
)

text = dumps_schemas(
    {
        "customers": customer_schema,
        "orders": order_schema,
    }
)

schemas = loads_schemas(text)
~~~

---

# 34. No format parameter in V1

V1 does NOT expose:

~~~python
load_schema(path, format="yaml")
~~~

or:

~~~python
dumps_schema(schema, format="yaml")
~~~

The stable schema_io implementation is YAML-backed in this release.

A future format capability can be added through a separate compatible design.

---

# 35. No parser object parameter

High-level stable functions do NOT accept:

~~~text
loader=
parser=
resolver=
compiler=
emitter=
~~~

Dependency injection remains an internal/advanced implementation concern.

---

# 36. No public limits parameter in initial stable API

High-level V1 functions use the secure defaults frozen in document 36.

They do NOT expose:

~~~python
max_payload_bytes=
max_depth=
max_fields=
~~~

in their initial stable signatures.

This prevents premature commitment to parser-configuration API shape.

---

# 37. Advanced parsing configuration

DeclarativeParsingLimits and hardened parser classes remain internal or provisional.

If advanced limit configuration is later made public, it MUST be added through a qualified advanced API without breaking the eight stable helpers.

---

# 38. No public DeclarativeSchemaService

The conceptual DeclarativeSchemaService from document 34 is NOT part of the initial stable public API.

Users should call module-level functions.

This avoids exposing wiring and lifecycle concepts that provide no current user value.

---

# 39. Internal service classification

The following remain internal implementation details:

~~~text
YamlSchemaParser
SchemaDefinitionValidator
DeclarativeTypeResolver
SchemaDefinitionCompiler
DeclarativeTypeExporter
SchemaDefinitionExporter
YamlSchemaEmitter
SchemaDocumentCompiler
DeclarativeSafeLoader
~~~

They MUST NOT appear in schema_io.__all__.

---

# 40. Definition-model classification

The following are NOT part of the initial stable user-facing API:

~~~text
SchemaDocument
SchemaDefinition
FieldDefinition
TypeDefinition
all TypeDefinition subclasses
StructFieldDefinition
SourceContext
DefinitionLocationIndex
~~~

They may initially live in internal modules.

---

# 41. Why definitions stay internal

Freezing definition classes would prematurely expose:

- constructor shape;
- normalization strategy;
- inheritance choices;
- source-location representation;
- parser/compiler seams.

Users do not need these objects to load or dump Schema.

---

# 42. Public error namespace

Declarative errors SHALL be exposed from:

~~~text
pytransformkit.errors
~~~

not duplicated into pytransformkit.schema_io.

Example:

~~~python
from pytransformkit.errors import (
    DeclarativeSchemaError,
    DeclarativeSchemaTypeError,
)
~~~

---

# 43. Stable public declarative errors

The following exception hierarchy SHALL become public when the feature is released:

~~~text
DeclarativeSchemaError
DeclarativeSchemaParseError
DeclarativeSchemaVersionError
DeclarativeSchemaValidationError
DeclarativeSchemaUnknownPropertyError
DeclarativeSchemaTypeError
DeclarativeSchemaDuplicateKeyError
DeclarativeSchemaDuplicateFieldError
DeclarativeSchemaDuplicateSchemaError
DeclarativeSchemaCardinalityError
DeclarativeSchemaDependencyError
DeclarativeSchemaIOError
DeclarativeSchemaExportError
DeclarativeSchemaLimitError
~~~

Their PTK-DECL-* codes are frozen by document 35.

---

# 44. Error import example

~~~python
from pytransformkit.errors import DeclarativeSchemaError
from pytransformkit.schema_io import load_schema

try:
    schema = load_schema("customers.yml")
except DeclarativeSchemaError as exc:
    print(exc.error_code)
~~~

---

# 45. No root error promotion

Declarative errors are NOT promoted to:

~~~python
from pytransformkit import DeclarativeSchemaError
~~~

The qualified errors namespace remains authoritative.

---

# 46. Optional dependency extra

The stable installation extra SHALL be:

~~~text
yaml
~~~

Installation:

~~~bash
pip install "pytransformkit[yaml]"
~~~

Recommended dependency:

~~~text
PyYAML>=6,<7
~~~

subject to release qualification.

---

# 47. Extra classification

yaml SHOULD be classified as a stable runtime extra in the machine-readable public API compatibility snapshot.

It is not a tooling-only extra.

---

# 48. Core dependency guarantee

PyYAML MUST NOT move into project.dependencies solely to support this feature.

Core installation remains dependency-light:

~~~bash
pip install pytransformkit
~~~

without mandatory YAML support.

---

# 49. Import behavior without extra

Without the yaml extra:

~~~python
import pytransformkit
~~~

MUST succeed.

Importing the schema_io namespace SHOULD also succeed if its implementation can defer the optional import.

Actual YAML operations raise PTK-DECL-010 when the dependency is unavailable.

---

# 50. Preferred lazy-import behavior

Recommended:

~~~text
import pytransformkit.schema_io
        ↓
no PyYAML required yet
        ↓
load_schema(...)
        ↓
load YAML adapter
~~~

This makes API discovery and type checking possible without eager optional dependencies.

---

# 51. Path typing

Public path-taking functions SHOULD use:

~~~python
str | os.PathLike[str]
~~~

rather than requiring pathlib.Path specifically.

This accepts common filesystem path abstractions without widening to arbitrary objects.

---

# 52. Return types

Stable return types are:

~~~text
load_schema      → Schema
loads_schema     → Schema
load_schemas     → dict[str, Schema]
loads_schemas    → dict[str, Schema]
dump_schema      → None
dump_schemas     → None
dumps_schema     → str
dumps_schemas    → str
~~~

No parser/definition wrapper leaks through high-level functions.

---

# 53. Mapping input typing

Multi-schema dumping accepts:

~~~python
Mapping[str, Schema]
~~~

rather than dict only.

The implementation consumes mapping iteration order.

---

# 54. Mapping output typing

Multi-schema loading returns a concrete:

~~~python
dict[str, Schema]
~~~

because insertion ordering is a standard Python guarantee and callers commonly need name lookup.

---

# 55. Validation behavior is part of the API

All stable load helpers are strict and fail-closed.

They do not provide a permissive mode.

There is no:

~~~python
strict=False
~~~

parameter in V1.

---

# 56. Unknown-property behavior

Public helpers reject unknown properties.

This behavior cannot be disabled through the stable API.

---

# 57. Unknown-type behavior

Public helpers reject unknown type names.

There is no public plugin registry or custom-type resolver parameter.

Intentional unknown semantics require:

~~~yaml
type: unknown
~~~

---

# 58. Security policy is not configurable away

The stable high-level API does not offer flags to enable:

~~~text
anchors
aliases
custom tags
merge keys
multi-document YAML
environment interpolation
templating
remote includes
~~~

These are language restrictions, not optional strictness settings.

---

# 59. File encoding contract

File-based helpers use UTF-8.

Callers do not pass an encoding parameter in V1.

Generated YAML uses UTF-8 and one final newline.

---

# 60. No directory loading

V1 does NOT expose:

~~~python
load_schema_dir(...)
load_project_schemas(...)
discover_schemas(...)
~~~

Only explicit files or in-memory text are loaded.

---

# 61. No URL loading

V1 does NOT expose URL-based loaders.

These are intentionally absent:

~~~python
load_schema("https://...")
load_schema("s3://...")
~~~

as special network semantics.

A string path is interpreted as a local filesystem path.

---

# 62. No implicit extension discovery

load_schema does not try:

~~~text
path.yml
path.yaml
path/schema.yml
~~~

when the supplied path does not exist.

The exact path is authoritative.

---

# 63. .yml and .yaml extensions

The public API MAY accept files with any filename extension because parsing is content-driven after explicit caller selection.

Documentation SHOULD recommend:

~~~text
.yml
or
.yaml
~~~

No extension gate is required.

---

# 64. No schema-name return from single loader

load_schema and loads_schema intentionally return only Schema.

They do NOT return:

~~~python
tuple[str, Schema]
~~~

because the primary ergonomic use case is obtaining the canonical Domain value.

Applications requiring identity retention should use load_schemas / loads_schemas.

---

# 65. Identity-preserving recommendation

If schema name must survive load/edit/dump without being separately tracked, users SHOULD use:

~~~python
schemas = load_schemas(path)
~~~

even for a one-schema document.

This preserves the declarative identity in the mapping key.

---

# 66. Stable exception catch boundaries

Users may catch all declarative failures through:

~~~python
except DeclarativeSchemaError:
    ...
~~~

or all framework errors through:

~~~python
except PyTransformKitError:
    ...
~~~

Specific PTK-DECL subclasses support narrower handling.

---

# 67. Public API and SchemaCodec

schema_io does NOT re-export:

~~~text
SchemaCodec
DataTypeCodec
FieldCodec
~~~

Canonical wire serialization remains under:

~~~python
pytransformkit.serialization
~~~

This prevents authoring and wire APIs from becoming conflated.

---

# 68. Public API and engines

schema_io exposes no engine argument.

Invalid:

~~~python
load_schema(path, engine="pandas")
~~~

Declarative schemas compile to engine-neutral canonical Schema values.

---

# 69. Public API and runtime

schema_io exposes no runtime execution parameter.

It does not run transformations, inspect datasets or bind resources.

---

# 70. Public API and quality rules

Declarative schema V1 does not expose quality-rule loading through schema_io.

Future quality authoring requires a separate specification.

---

# 71. Public API documentation contract

User-facing documentation MUST clearly distinguish:

~~~text
Python Schema authoring
YAML Schema authoring
SchemaCodec wire serialization
~~~

Users should never be told that YAML replaces SchemaCodec.

---

# 72. Static typing

All eight stable functions MUST have complete type annotations and pass the project mypy configuration.

The package remains PEP 561 typed through the existing typed distribution strategy.

---

# 73. Positional vs keyword-only parameters

Stable calling conventions are:

~~~text
path             positional
text             positional
schema           positional
schemas          positional
name             keyword-only
source           keyword-only
~~~

This makes identity/diagnostic arguments explicit.

---

# 74. No **kwargs extensibility escape hatch

Stable helpers MUST NOT accept arbitrary **kwargs.

New options require explicit additive API design.

This protects typo detection and signature clarity.

---

# 75. No mutable default values

No stable function uses mutable default arguments.

Public operations are stateless by default.

---

# 76. Deterministic behavior

Given the same valid input text and same package version, loads_schema / loads_schemas MUST produce equal Domain values.

Given the same Schema input, name and package version, dumps_schema SHOULD produce identical text.

---

# 77. Thread-safety expectation

The high-level functions SHOULD be safe for independent concurrent calls because they rely on no shared mutable parser state.

No mutable global registry is part of the public contract.

---

# 78. Compatibility with existing root freeze

The feature is additive relative to PyTransformKit 1.0:

~~~text
existing root exports unchanged
existing qualified namespaces unchanged
existing wire contracts unchanged
new qualified schema_io namespace added
new errors added under pytransformkit.errors
new yaml runtime extra added
~~~

This is compatible with the V1 post-freeze additive-change policy.

---

# 79. Machine-readable API snapshot

When implementation lands, the public compatibility snapshot MUST be updated additively to track:

~~~text
pytransformkit.schema_io module
schema_io.__all__
eight public function signatures
PTK-DECL exception hierarchy
PTK-DECL error codes
yaml stable runtime extra
~~~

All existing baseline entries remain unchanged.

---

# 80. Public API snapshot gate

CI SHOULD fail if a released stable schema_io function is accidentally:

- removed;
- renamed;
- moved;
- given an incompatible signature;
- changed to a different return contract.

Additive future helpers require explicit compatibility review.

---

# 81. Error-catalogue gate

CI MUST verify all released PTK-DECL error codes are unique and preserve their documented class hierarchy.

Existing PTK-SCHEMA codes remain untouched.

---

# 82. Optional-extra gate

CI SHOULD verify:

~~~text
core install
    → import pytransformkit succeeds

core install
    → schema_io import succeeds where lazily designed

core install + YAML operation
    → PTK-DECL-010

install [yaml]
    → declarative suite succeeds
~~~

---

# 83. Public contract tests

Contract tests MUST cover every stable function with both success and expected failure behavior.

Tests SHOULD inspect signatures directly so accidental positional/keyword changes are caught.

---

# 84. Single-schema contract tests

Required:

~~~text
load_schema valid single        → Schema
loads_schema valid single       → Schema
load_schema multi-schema        → PTK-DECL-009
loads_schema multi-schema       → PTK-DECL-009
~~~

---

# 85. Multi-schema contract tests

Required:

~~~text
load_schemas single             → one-entry dict
loads_schemas single            → one-entry dict
load_schemas multiple           → ordered dict semantics
loads_schemas invalid member    → whole call fails
~~~

---

# 86. Dump contract tests

Required:

~~~text
dumps_schema returns str
dumps_schema requires keyword-only name
dump_schema writes UTF-8
dump_schema overwrites exact existing file
dump_schema does not create parents
dumps_schemas preserves Mapping order
dump_schemas emits one YAML document
~~~

---

# 87. Root-isolation test

A contract test MUST verify the eight schema_io functions are NOT added to:

~~~python
pytransformkit.__all__
~~~

This protects the intentionally small canonical root.

---

# 88. Internal-symbol isolation test

A contract or architecture test SHOULD verify schema_io.__all__ does not expose parser/compiler/definition implementation classes.

---

# 89. User-facing installation example

Recommended documentation:

~~~bash
pip install "pytransformkit[yaml]"
~~~

then:

~~~python
from pytransformkit.schema_io import load_schema

schema = load_schema("customers.yml")
~~~

---

# 90. Public API stability classification

Upon release, the following are STABLE:

~~~text
pytransformkit.schema_io namespace
eight load/dump functions
their documented signatures
their return types
their cardinality semantics
yaml extra name
public declarative exception hierarchy
PTK-DECL error codes
~~~

---

# 91. Provisional/internal classification

The following remain PROVISIONAL or INTERNAL:

~~~text
definition dataclasses
parser class
compiler class
validator class
emitter class
type resolver/exporter
parsing-limit object
parser library choice as semantic contract
internal module layout
~~~

---

# 92. Dependency implementation is replaceable

Although PyYAML is the selected initial adapter, users MUST NOT depend on PyYAML objects or exception classes through the public API.

A future parser replacement that preserves the schema_io contract is compatible.

---

# 93. Candidate implementation layout

A compatible implementation MAY use:

~~~text
src/pytransformkit/schema_io/
├── __init__.py
├── _api.py
├── _model.py
├── _validation.py
├── _compiler.py
├── _exporter.py
└── _yaml.py
~~~

The underscored layout is illustrative, not itself public contract.

---

# 94. Recommended public __init__.py

Conceptually:

~~~python
from ._api import (
    dump_schema,
    dump_schemas,
    dumps_schema,
    dumps_schemas,
    load_schema,
    load_schemas,
    loads_schema,
    loads_schemas,
)

__all__ = [
    "dump_schema",
    "dump_schemas",
    "dumps_schema",
    "dumps_schemas",
    "load_schema",
    "load_schemas",
    "loads_schema",
    "loads_schemas",
]
~~~

---

# 95. Error module implementation

Declarative exceptions SHOULD live in a dedicated implementation module such as:

~~~text
src/pytransformkit/errors/declarative.py
~~~

and be re-exported from:

~~~text
pytransformkit.errors
~~~

The implementation filename is not a stable public namespace by itself.

---

# 96. Release-line note

This specification intentionally does not assign the final package version.

The implementation roadmap in document 40 will determine the release line after scope, qualification effort and compatibility gates are finalized.

The feature is structurally suitable for an additive post-1.0 release.

---

# 97. Decisions frozen by this document

## DEC-API-01

The stable namespace is pytransformkit.schema_io.

## DEC-API-02

No schema_io functions are promoted to the pytransformkit root.

## DEC-API-03

The stable initial surface contains exactly eight load/dump functions.

## DEC-API-04

Single-schema loaders return bare Schema and require exactly one declaration.

## DEC-API-05

Multi-schema loaders return dict[str, Schema] preserving declaration order.

## DEC-API-06

Single-schema dump functions require explicit keyword-only name.

## DEC-API-07

Multi-schema dump functions use Mapping keys as declarative names.

## DEC-API-08

source is a keyword-only diagnostic argument on in-memory loaders.

## DEC-API-09

Stable in-memory loaders accept str, not bytes.

## DEC-API-10

Path APIs accept str | os.PathLike[str].

## DEC-API-11

File dumps overwrite the exact supplied file and do not create parent directories.

## DEC-API-12

No format, permissive-mode or parser-injection parameters exist in V1.

## DEC-API-13

Advanced parser limits remain outside the initial stable surface.

## DEC-API-14

Declarative parser/compiler/definition classes remain internal.

## DEC-API-15

Declarative errors are public through pytransformkit.errors.

## DEC-API-16

Declarative errors are not promoted to the root package.

## DEC-API-17

The stable optional dependency extra is yaml.

## DEC-API-18

PyYAML remains optional and lazily required.

## DEC-API-19

SchemaCodec remains exclusively under pytransformkit.serialization.

## DEC-API-20

The existing PyTransformKit 1.0 root and wire contracts remain unchanged.

---

# 98. Acceptance criteria

The public API design is complete when:

1. pytransformkit.schema_io exists as a qualified namespace;
2. it exposes exactly the eight stable helper functions initially;
3. no helper is added to pytransformkit.__all__;
4. load_schema and loads_schema enforce exactly-one cardinality;
5. load_schemas and loads_schemas preserve names/order;
6. dumps_schema requires explicit keyword-only name;
7. dumps_schemas consumes Mapping[str, Schema];
8. filesystem helpers accept str or PathLike[str];
9. in-memory helpers accept str only;
10. source remains diagnostic-only;
11. dump helpers write deterministic UTF-8 YAML;
12. exact output paths are used without discovery;
13. public helpers offer no permissive security bypass;
14. parser/compiler/definition objects remain internal;
15. PTK-DECL errors are exported through pytransformkit.errors;
16. yaml is an optional stable runtime extra;
17. core imports without PyYAML;
18. SchemaCodec API and wire contract remain untouched;
19. API/error/extra compatibility snapshots can be qualified in CI;
20. the implementation remains engine-independent.

---

# 99. Next document

The next document defines the full qualification matrix before implementation/release:

~~~text
39_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_TEST_MATRIX_AND_ACCEPTANCE_CRITERIA.md
~~~

It must consolidate:

~~~text
unit tests
grammar tests
type mapping tests
error tests
security tests
round-trip tests
wire bridge tests
public API contract tests
Python 3.11–3.14 matrix
core-without-yaml tests
yaml-extra tests
architecture/import tests
release acceptance gates
~~~

---

# 100. Final summary

The user-facing surface is deliberately compact:

~~~text
pytransformkit.schema_io
│
├── load_schema
├── loads_schema
├── load_schemas
├── loads_schemas
├── dump_schema
├── dumps_schema
├── dump_schemas
└── dumps_schemas
~~~

with failures exposed through:

~~~text
pytransformkit.errors
└── DeclarativeSchemaError + PTK-DECL-* hierarchy
~~~

and YAML support installed through:

~~~text
pytransformkit[yaml]
~~~

The root package remains unchanged, the canonical Domain remains Schema, and SchemaCodec remains the canonical wire contract.

> **A small stable authoring API around one existing canonical Schema model.**