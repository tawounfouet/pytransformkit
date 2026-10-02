# 40 — PyTransformKit Declarative Schema — Implementation Roadmap

> **Document status:** DRAFT NORMATIVE IMPLEMENTATION ROADMAP  
> **Depends on:** 28_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_EXPRESSION_DU_BESOIN.md  
> **Depends on:** 29_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_REQUIREMENTS_ANALYSIS.md  
> **Depends on:** 30_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ARCHITECTURE.md  
> **Depends on:** 31_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SPECIFICATION.md  
> **Depends on:** 32_PYTRANSFORMKIT_DECLARATIVE_TYPE_SYSTEM_MAPPING.md  
> **Depends on:** 33_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_DOMAIN_MODEL.md  
> **Depends on:** 34_PYTRANSFORMKIT_SCHEMA_LOADER_COMPILER_AND_EXPORTER_SPEC.md  
> **Depends on:** 35_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_VALIDATION_AND_ERROR_MODEL.md  
> **Depends on:** 36_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SECURITY_AND_PARSING_POLICY.md  
> **Depends on:** 37_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ROUNDTRIP_AND_SERIALIZATION_MODEL.md  
> **Depends on:** 38_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_PUBLIC_API_SPEC.md  
> **Depends on:** 39_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_TEST_MATRIX_AND_ACCEPTANCE_CRITERIA.md  
> **Baseline release:** PyTransformKit 1.0.0  
> **Target release:** PyTransformKit 1.1.0  
> **Roadmap lots:** LOT-29 → LOT-43  
> **Declarative language version:** 1

---

# 1. Purpose

This document converts the complete declarative-schema specification into an ordered implementation roadmap.

It defines:

- the release line;
- implementation lots;
- dependencies between lots;
- package-version checkpoints;
- required code and tests per lot;
- acceptance gates;
- compatibility checkpoints;
- CI integration;
- documentation work;
- release-candidate qualification;
- stable-release closure.

The roadmap continues directly after the existing PyTransformKit V1 implementation sequence:

~~~text
LOT-00 → LOT-28  = PyTransformKit 1.0.0
LOT-29 → LOT-43  = Declarative Schema → PyTransformKit 1.1.0
~~~

---

# 2. Release decision

Declarative schema support SHALL target:

~~~text
PyTransformKit 1.1.0
~~~

Rationale:

- the current package baseline is 1.0.0;
- the feature is additive;
- the root API remains unchanged;
- existing SchemaCodec wire contracts remain unchanged;
- new public schema_io APIs are introduced;
- new public PTK-DECL errors are introduced;
- a new stable runtime extra yaml is introduced.

Under semantic versioning, this is a minor release rather than a patch release.

---

# 3. Release-line invariants

Throughout LOT-29 → LOT-43, the following MUST remain true:

~~~text
existing root exports unchanged
existing 1.0 public contracts preserved
SchemaCodec contract_version remains 1
canonical Domain remains YAML-independent
core package remains free of mandatory YAML dependency
engines remain unrelated to declarative parsing
Python 3.11–3.14 support remains intact
~~~

---

# 4. High-level implementation phases

The implementation is divided into five phases:

~~~text
PHASE A — FOUNDATIONS
LOT-29 → LOT-33

PHASE B — PARSING AND COMPILATION
LOT-34 → LOT-36

PHASE C — PUBLIC AUTHORING API
LOT-37 → LOT-39

PHASE D — COMPATIBILITY AND QUALIFICATION
LOT-40 → LOT-42

PHASE E — RELEASE CLOSURE
LOT-43
~~~

---

# 5. Version progression

Recommended package checkpoints:

| Lot | Version | Milestone |
| --- | --- | --- |
| LOT-29 | 1.1.0a1 | package/bootstrap |
| LOT-30 | 1.1.0a2 | definition model |
| LOT-31 | 1.1.0a3 | declarative errors |
| LOT-32 | 1.1.0a4 | type mapping |
| LOT-33 | 1.1.0a5 | validation |
| LOT-34 | 1.1.0a6 | hardened YAML parser |
| LOT-35 | 1.1.0a7 | compiler/load pipeline |
| LOT-36 | 1.1.0a8 | exporter/emitter |
| LOT-37 | 1.1.0b1 | stable schema_io surface implemented |
| LOT-38 | 1.1.0b2 | round-trip and wire bridge |
| LOT-39 | 1.1.0b3 | security hardening closure |
| LOT-40 | 1.1.0b4 | compatibility/public contract freeze |
| LOT-41 | 1.1.0rc1 | CI and built-artifact qualification |
| LOT-42 | 1.1.0rc2 | docs/examples/release candidate closure |
| LOT-43 | 1.1.0 | stable release |

Package-version bumps SHOULD occur only after the corresponding lot qualifies.

---

# 6. Dependency graph

~~~text
LOT-29  Bootstrap
   ↓
LOT-30  Definition model
   ↓
LOT-31  Errors
   ↓
LOT-32  Type resolver/exporter
   ↓
LOT-33  Validator
   ↓
LOT-34  Hardened YAML parser
   ↓
LOT-35  Compiler + loading pipeline
   ↓
LOT-36  Exporter + YAML emitter
   ↓
LOT-37  Public schema_io API
   ↓
LOT-38  Round-trip + SchemaCodec bridge
   ↓
LOT-39  Security hardening closure
   ↓
LOT-40  Public compatibility freeze
   ↓
LOT-41  CI + wheel/sdist qualification
   ↓
LOT-42  Documentation + RC closure
   ↓
LOT-43  1.1.0 stable
~~~

---

# 7. LOT-29 — Declarative Schema Package Bootstrap

## Objective

Create the implementation skeleton without exposing unstable public behavior.

## Primary changes

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

Add the optional runtime extra:

~~~toml
yaml = [
  "PyYAML>=6,<7",
]
~~~

subject to Python-version qualification.

## Constraints

- no public root export;
- no eager PyYAML import;
- no Domain import back toward schema_io;
- no user-visible API behavior beyond importability.

## Required tests

~~~text
schema_io package import
core import without PyYAML
architecture dependency direction
optional-extra metadata smoke
~~~

## Exit criteria

~~~text
package skeleton exists
core import remains dependency-light
schema_io imports without YAML installed
ruff/mypy/tests green
~~~

## Target version

~~~text
1.1.0a1
~~~

---

# 8. LOT-30 — Declarative Definition Model

## Objective

Implement the internal immutable definition model from document 33.

## Required objects

~~~text
SchemaDocument
SchemaDefinition
FieldDefinition
StructFieldDefinition
TypeDefinition hierarchy
StringTypeDefinition
BooleanTypeDefinition
IntegerTypeDefinition
FloatTypeDefinition
DecimalTypeDefinition
BinaryTypeDefinition
DateTypeDefinition
TimeTypeDefinition
TimestampTypeDefinition
DurationTypeDefinition
UnknownTypeDefinition
ListTypeDefinition
StructTypeDefinition
MapTypeDefinition
~~~

## Requirements

- frozen/immutable values;
- tuple-based ordered collections;
- no parser dependency;
- no engine dependency;
- no filesystem access;
- local invariants where appropriate;
- no public re-export from schema_io.

## Required tests

~~~text
DS-UNIT definition equality
immutability
defaults
local invariants
nested definition construction
ordering
~~~

## Exit criteria

All definition-model requirements from document 33 have executable unit evidence.

## Target version

~~~text
1.1.0a2
~~~

---

# 9. LOT-31 — Declarative Error Model

## Objective

Implement the complete PTK-DECL error hierarchy before parser/compiler code begins relying on it.

## Required public errors

~~~text
DeclarativeSchemaError                    PTK-DECL-000
DeclarativeSchemaParseError               PTK-DECL-001
DeclarativeSchemaVersionError             PTK-DECL-002
DeclarativeSchemaValidationError          PTK-DECL-003
DeclarativeSchemaUnknownPropertyError     PTK-DECL-004
DeclarativeSchemaTypeError                PTK-DECL-005
DeclarativeSchemaDuplicateKeyError        PTK-DECL-006
DeclarativeSchemaDuplicateFieldError      PTK-DECL-007
DeclarativeSchemaDuplicateSchemaError     PTK-DECL-008
DeclarativeSchemaCardinalityError         PTK-DECL-009
DeclarativeSchemaDependencyError          PTK-DECL-010
DeclarativeSchemaIOError                  PTK-DECL-011
DeclarativeSchemaExportError              PTK-DECL-012
DeclarativeSchemaLimitError               PTK-DECL-013
~~~

## Supporting value

Implement:

~~~text
DeclarativeErrorContext
~~~

with source, line, column and object_path.

## Public exposure

Errors are re-exported through:

~~~text
pytransformkit.errors
~~~

but not through the root package.

## Required tests

~~~text
hierarchy
error codes
structured context
message fragments
root non-promotion
existing PTK-SCHEMA stability
~~~

## Exit criteria

Every code is unique and every new public exception has stable tested ancestry.

## Target version

~~~text
1.1.0a3
~~~

---

# 10. LOT-32 — Declarative Type Resolver and Exporter

## Objective

Implement the closed mapping between internal TypeDefinition values and canonical DataType values.

## Forward path

~~~text
TypeDefinition
      ↓
DeclarativeTypeResolver
      ↓
DataType
~~~

## Reverse path

~~~text
DataType
      ↓
DeclarativeTypeExporter
      ↓
TypeDefinition
~~~

## Required mappings

All primitive, numeric, decimal, temporal, binary, unknown and nested list/struct/map mappings from document 32.

## Requirements

- deterministic;
- recursive;
- engine-independent;
- no plugin fallback;
- unknown definition subclass fails;
- unsupported DataType export fails;
- aliases are parser-level normalization only.

## Required tests

~~~text
DS-TYPE full scalar matrix
integer signedness
float width
decimal parameters
temporal units
timezone
list recursion
struct recursion
map recursion
UnknownType
unsupported subclasses
~~~

## Exit criteria

Every declarative-V1-representable DataType has proven bidirectional mapping.

## Target version

~~~text
1.1.0a4
~~~

---

# 11. LOT-33 — Declarative Semantic Validator

## Objective

Implement SchemaDefinitionValidator and deterministic semantic validation.

## Scope

~~~text
document version
schema uniqueness
field uniqueness
nested field uniqueness
blank names
required properties after decoding
decimal constraints
temporal units
nested holder completeness
count semantics not owned by parser limits
~~~

## Requirements

- validation is side-effect free;
- definitions are not mutated;
- first deterministic error wins;
- object_path is populated;
- no aggregate public error in V1;
- known Domain invariant failures can later be translated cleanly.

## Required tests

~~~text
DS-GRAMMAR semantic failures
DS-ERR validation errors
duplicate fields
duplicate schemas
nested duplicate fields
parameter errors
deterministic traversal order
~~~

## Exit criteria

All semantic invalidity specified in documents 31, 33 and 35 fails before canonical compilation where possible.

## Target version

~~~text
1.1.0a5
~~~

---

# 12. LOT-34 — Hardened YAML Parser and Decoder

## Objective

Implement the complete untrusted-YAML trust boundary.

## Components

~~~text
DeclarativeSafeLoader
token/event preflight
controlled scalar resolvers
duplicate-key mapping constructor
plain-value audit
depth/count enforcement
strict declarative decoder
YamlSchemaParser
~~~

## Security controls

~~~text
1 MiB payload limit
64 nesting levels
256 schemas
10,000 top-level fields/schema
50,000 total field nodes
duplicate keys rejected
anchors rejected
aliases rejected
merge keys rejected
custom tags rejected
multi-document streams rejected
implicit dates disabled
yes/no/on/off coercion disabled
NaN/Infinity rejected
~~~

## Requirements

- PyYAML imported lazily;
- no global SafeLoader mutation;
- no arbitrary Python constructors;
- source locations retained when possible;
- parser errors translated to PTK-DECL errors;
- strict unknown properties.

## Required tests

~~~text
DS-SEC complete parser suite
DS-GRAMMAR structural decoder suite
payload boundary
depth boundary
count boundaries
scalar ambiguity
no object construction
global loader isolation
~~~

## Exit criteria

The YAML parser is fail-closed and all security MUST criteria from document 36 are green.

## Target version

~~~text
1.1.0a6
~~~

---

# 13. LOT-35 — Compiler and Loading Pipeline

## Objective

Implement validated definition → canonical Schema compilation and the internal load orchestration.

## Components

~~~text
SchemaDefinitionCompiler
optional SchemaDocumentCompiler
internal loads-one orchestration
internal loads-many orchestration
cardinality enforcement
Domain error translation
~~~

## Required flow

~~~text
YAML text
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

## Requirements

- preserve field order;
- preserve nullable;
- preserve description;
- preserve nested type state;
- invoke canonical Domain constructors;
- do not bypass Domain invariants;
- multi-schema compilation is document-atomic;
- single-schema cardinality is explicit.

## Required tests

~~~text
basic compilation
all DataTypes
nested compilation
single/multi cardinality
Domain error chaining
Python-vs-YAML Schema equality
engine-free execution
~~~

## Exit criteria

Valid declarative documents compile into canonical Schema values equal to direct Python construction.

## Target version

~~~text
1.1.0a7
~~~

---

# 14. LOT-36 — Schema Exporter and Canonical YAML Emitter

## Objective

Implement the reverse path from canonical Schema to deterministic declarative YAML.

## Components

~~~text
SchemaDefinitionExporter
YamlSchemaEmitter
definition → plain-value encoder
canonical property ordering
safe scalar quoting
alias suppression
~~~

## Required flow

~~~text
Schema
 ↓
SchemaDefinitionExporter
 ↓
SchemaDocument
 ↓
SchemaDefinitionValidator
 ↓
YamlSchemaEmitter
 ↓
canonical YAML
~~~

## Requirements

- explicit schema name;
- no inferred names;
- canonical type spelling;
- explicit nullable emission;
- canonical temporal short forms;
- deterministic ordering;
- one final newline;
- no anchors/aliases/tags/merge keys;
- generated YAML accepted by hardened parser.

## Required tests

~~~text
all DataType exports
canonical type aliases
ordering
safe quoting
Unicode
deterministic bytes
parser/emitter closure
unsupported custom DataType
~~~

## Exit criteria

Schema → YAML → Schema semantic round-trip is green for all supported canonical states.

## Target version

~~~text
1.1.0a8
~~~

---

# 15. LOT-37 — Public schema_io API

## Objective

Expose the stable user-facing API defined in document 38.

## Stable namespace

~~~text
pytransformkit.schema_io
~~~

## Stable functions

~~~text
load_schema
loads_schema
load_schemas
loads_schemas
dump_schema
dumps_schema
dump_schemas
dumps_schemas
~~~

## Filesystem behavior

- UTF-8;
- exact caller path;
- no discovery;
- no directory scanning;
- no parent creation;
- overwrite exact existing target;
- no implicit backups.

## Public isolation

Do NOT add any of the eight helpers to pytransformkit.__all__.

Do NOT expose parser/compiler/definition classes through schema_io.__all__.

## Required tests

~~~text
exact __all__
exact signatures
keyword-only name/source
path typing
single/multi semantics
filesystem behavior
root isolation
internal symbol isolation
~~~

## Exit criteria

The eight-function surface behaves exactly as document 38 specifies.

## Target version

~~~text
1.1.0b1
~~~

---

# 16. LOT-38 — Round-Trip, Golden YAML and Wire Bridge

## Objective

Close semantic round-trip and prove coexistence with the frozen SchemaCodec wire contract.

## Required tests

~~~text
Schema → YAML → Schema
nested DataType round-trip
Field description round-trip
Unicode round-trip
multi-schema names/order round-trip
authoring normalization
golden YAML fixtures
YAML → Schema → SchemaCodec → Schema
SchemaCodec golden JSON → Schema → YAML → Schema
fingerprint invariance
schema-name fingerprint independence
~~~

## Required invariant

~~~text
SchemaCodec.contract == "pytransformkit.schema"
SchemaCodec.contract_version == 1
~~~

must remain unchanged.

## Golden fixture families

~~~text
declarative YAML goldens     additive
SchemaCodec JSON goldens     unchanged
~~~

## Exit criteria

Declarative and wire representations compose only through canonical Schema and all bridge tests are green.

## Target version

~~~text
1.1.0b2
~~~

---

# 17. LOT-39 — Security Hardening Closure

## Objective

Perform a dedicated adversarial qualification pass after the complete load/dump pipeline exists.

## Required adversarial cases

~~~text
python object tags
custom tags
anchors
aliases
alias amplification
merge keys
duplicate keys
multi-document streams
oversized payload
excessive depth
schema-count overflow
field-count overflow
NaN/Infinity
implicit date coercion
yes/no/on/off coercion
environment-looking strings
URL-looking strings
include-looking properties
unknown plugin-like types
~~~

## Side-effect proofs

~~~text
no network access
no secondary file reads
no environment interpolation
no plugin activation
no engine imports
no global PyYAML mutation
~~~

## Required CI integration

Declarative security tests SHOULD be included in or explicitly called by the existing security-contract gate.

## Exit criteria

No security release blocker from document 39 remains.

## Target version

~~~text
1.1.0b3
~~~

---

# 18. LOT-40 — Public Compatibility Freeze

## Objective

Freeze the new additive stable surface and integrate it into machine-readable compatibility contracts.

## Snapshot changes

Update public API snapshot tooling to include:

~~~text
pytransformkit.schema_io
eight function signatures
PTK-DECL public exception hierarchy
yaml stable runtime extra
~~~

## Error catalogue

Extend the machine-readable catalogue additively with:

~~~text
PTK-DECL-000 → PTK-DECL-013
~~~

## Must remain unchanged

~~~text
existing root exports
legacy compatibility names
engine IDs
existing wire contract IDs/versions
existing error codes
existing stable extras
~~~

## Required tests

~~~text
snapshot generation/check
root freeze
error hierarchy
error code uniqueness
extras classification
wire snapshot unchanged
consumer compatibility regression
~~~

## Exit criteria

The additive 1.1 public contract is machine-verifiable without weakening the 1.0 baseline.

## Target version

~~~text
1.1.0b4
~~~

---

# 19. LOT-41 — CI Matrix and Built-Artifact Qualification

## Objective

Make declarative schema qualification first-class in CI and prove installed-artifact behavior.

## Python matrix

Required:

~~~text
Python 3.11 + yaml
Python 3.12 + yaml
Python 3.13 + yaml
Python 3.14 + yaml
~~~

## Core-only negative capability

Clean environment:

~~~text
PyYAML absent
import pytransformkit PASS
import pytransformkit.schema_io PASS
YAML operation → PTK-DECL-010
~~~

## Wheel qualification

Built wheel MUST prove:

~~~text
core install
yaml-extra install
pip check
public schema_io imports
basic load/dump round-trip
API snapshot
error catalogue
no engine dependency
~~~

## sdist qualification

Repeat core and yaml-extra smoke from the source distribution.

## CI jobs

Integrate or add:

~~~text
declarative-schema-contract
declarative security coverage
declarative Python matrix
core-without-yaml gate
built-wheel yaml smoke
~~~

## Exit criteria

All required gates from document 39 are green from built artifacts.

## Target version

~~~text
1.1.0rc1
~~~

---

# 20. LOT-42 — Documentation, Examples and Release-Candidate Closure

## Objective

Finish user-facing documentation and prove that documented examples execute against the release candidate.

## Required documentation

At minimum:

~~~text
41_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_GETTING_STARTED.md
42_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_REFERENCE_EXAMPLES.md
~~~

## README integration

README SHOULD document:

~~~text
pip install "pytransformkit[yaml]"
Python Schema authoring
YAML Schema authoring
schema_io namespace
SchemaCodec distinction
~~~

## Reference examples

Cover:

~~~text
basic customer schema
all primitive types
decimal
temporal
list
struct
map
multi-schema file
dump/load round-trip
error handling
Python vs YAML equivalence
~~~

## Executable documentation

Reference snippets SHOULD be executable as tests or smoke scripts.

## RC qualification

Run full repository qualification after documentation changes.

## Exit criteria

Documentation matches the frozen API and all published examples pass.

## Target version

~~~text
1.1.0rc2
~~~

---

# 21. LOT-43 — Declarative Schema Stable Release Closure

## Objective

Promote the qualified release candidate to PyTransformKit 1.1.0 stable.

## Required final gates

~~~text
Python 3.11             PASS
Python 3.12             PASS
Python 3.13             PASS
Python 3.14             PASS

Ruff lint               PASS
Ruff format             PASS
mypy                    PASS

declarative unit        PASS
grammar                  PASS
type mapping             PASS
errors                   PASS
security                 PASS
round-trip               PASS
wire bridge              PASS
public API               PASS

core-without-yaml        PASS
yaml extra               PASS

public API freeze        PASS
error catalogue          PASS
backwards compatibility PASS

wheel                    PASS
sdist                    PASS
full repository suite    PASS
~~~

## Release actions

~~~text
set package version 1.1.0
build wheel + sdist
twine/check equivalent
verify clean installation
create v1.1.0 tag
publish GitHub Release
publish to PyPI through trusted publishing
record artifact hashes
close roadmap line
~~~

## Exit criteria

PyTransformKit 1.1.0 is published, installable and all stable declarative-schema contracts are frozen.

## Target version

~~~text
1.1.0
~~~

---

# 22. Lot summary

| Lot | Title | Target |
| --- | --- | --- |
| 29 | Package Bootstrap | 1.1.0a1 |
| 30 | Definition Model | 1.1.0a2 |
| 31 | Error Model | 1.1.0a3 |
| 32 | Type Resolver and Exporter | 1.1.0a4 |
| 33 | Semantic Validator | 1.1.0a5 |
| 34 | Hardened YAML Parser | 1.1.0a6 |
| 35 | Compiler and Loading Pipeline | 1.1.0a7 |
| 36 | Exporter and YAML Emitter | 1.1.0a8 |
| 37 | Public schema_io API | 1.1.0b1 |
| 38 | Round-Trip and Wire Bridge | 1.1.0b2 |
| 39 | Security Hardening Closure | 1.1.0b3 |
| 40 | Public Compatibility Freeze | 1.1.0b4 |
| 41 | CI and Built Artifacts | 1.1.0rc1 |
| 42 | Documentation and RC Closure | 1.1.0rc2 |
| 43 | Stable Release Closure | 1.1.0 |

---

# 23. Phase A exit gate

After LOT-33:

~~~text
definition model implemented
errors implemented
type bidirectional mapping implemented
semantic validation implemented
no YAML parsing required yet
all foundations unit-tested
~~~

The core architecture is ready for untrusted input.

---

# 24. Phase B exit gate

After LOT-36:

~~~text
hardened YAML parser implemented
YAML → Schema working
Schema → YAML working
semantic round-trip green
security parser basics green
~~~

No stable user-facing surface is considered frozen yet.

---

# 25. Phase C exit gate

After LOT-39:

~~~text
public schema_io API implemented
round-trip/wire bridge green
security closure green
feature behavior complete
~~~

The remaining work is compatibility/release qualification.

---

# 26. Phase D exit gate

After LOT-42:

~~~text
stable public API snapshot frozen
PTK-DECL catalogue frozen
yaml extra frozen
Python 3.11–3.14 qualified
wheel/sdist qualified
documentation executable
release candidate green
~~~

Only stable publication remains.

---

# 27. Branching strategy

Recommended implementation flow:

~~~text
main
 ↓
feat/declarative-schema-lot-29
 ↓ PR
main
 ↓
feat/declarative-schema-lot-30
...
~~~

One PR per lot is preferred when the lot is independently reviewable.

Adjacent small lots MAY be combined only if their acceptance evidence remains separately traceable.

---

# 28. PR requirements

Every implementation PR SHOULD include:

~~~text
lot identifier
specification references
implementation summary
tests added/changed
local qualification evidence
compatibility impact
public API impact
security impact where applicable
~~~

---

# 29. Merge policy

A lot SHOULD be merged only when:

~~~text
implementation complete
required tests green
Ruff green
format green
mypy green
relevant CI jobs green
no unresolved release blocker
~~~

Public-contract lots require explicit snapshot review.

---

# 30. Version bump policy

Version bumps SHOULD occur at the end of a qualified lot, not at lot start.

Example:

~~~text
LOT-34 implementation
 ↓
LOT-34 tests green
 ↓
version → 1.1.0a6
 ↓
merge
~~~

This makes package versions evidence-backed checkpoints.

---

# 31. Compatibility strategy

During the entire 1.1.0 line:

~~~text
1.0 root exports are preserved
1.0 qualified namespace contracts are preserved
1.0 wire contracts are preserved
1.0 error assignments are preserved
1.0 engine identifiers are preserved
~~~

Declarative support is additive only.

---

# 32. Public API freeze timing

The eight schema_io helpers are designed in document 38 but SHOULD become machine-frozen only at LOT-40 after implementation and security behavior have stabilized.

This avoids freezing accidental early implementation details.

---

# 33. Internal API flexibility

Before LOT-40, internal classes MAY be refactored without compatibility ceremony:

~~~text
SchemaDefinition internals
parser class organization
compiler helper names
emitter helper names
SourceContext implementation
limit configuration object
~~~

provided public behavior remains aligned with the specifications.

---

# 34. Security-first sequencing

The parser is deliberately implemented only after:

~~~text
definition model
error hierarchy
type rules
semantic validator
~~~

exist.

This prevents the YAML adapter from becoming the accidental owner of Domain semantics.

---

# 35. Public-API-late sequencing

The stable schema_io functions are exposed only after both loading and dumping internals exist.

This avoids a half-stable API where loading is public before round-trip semantics are known.

---

# 36. Wire-protection sequencing

SchemaCodec bridge qualification occurs before compatibility freeze.

Therefore any accidental pressure to modify the wire contract is detected before 1.1 API freezing.

---

# 37. Release blocker escalation

If any lot discovers a need to:

~~~text
change canonical Schema semantics
change SchemaCodec contract_version
add YAML dependency to core
promote helpers to root
enable executable YAML features
weaken duplicate-key handling
reduce Python support
~~~

implementation MUST pause for specification revision before continuing.

These are architecture-level changes, not ordinary coding details.

---

# 38. Deferred capabilities

The following are explicitly OUT of the 1.1.0 roadmap:

~~~text
declarative transformations
declarative TransformationPlan
quality/test DSL in YAML
schema directory discovery
remote schema loading
HTTP/S3 includes
environment interpolation
templating
custom declarative type plugins
YAML anchors/aliases
comment-preserving editing
JSON/TOML declarative adapters
automatic declarative V1→V2 migration
public parser-limit configuration
declarative document fingerprint
~~~

Deferral prevents scope creep and protects the stable release.

---

# 39. Release artifact expectations

PyTransformKit 1.1.0 release artifacts MUST include:

~~~text
wheel
sdist
stable package metadata
yaml optional extra metadata
public API snapshot
error-code catalogue
release qualification evidence
Git tag v1.1.0
GitHub Release
PyPI release
artifact hashes
~~~

---

# 40. Documentation sequence

Implementation-facing docs 28–40 precede coding.

User-facing docs 41–42 are finalized after the stable API and behavior exist.

~~~text
28–40 = design / contract / roadmap
41    = Getting Started
42    = Reference Examples
~~~

---

# 41. Definition of done for 1.1.0

The declarative-schema release line is DONE only when:

~~~text
YAML can author canonical Schema
canonical Schema can emit safe YAML
all supported DataTypes round-trip
strict errors are public and coded
untrusted YAML is hardened
schema_io stable API is frozen
root remains unchanged
SchemaCodec remains unchanged
yaml remains optional
Python 3.11–3.14 are green
built wheel and sdist are green
documentation examples execute
1.1.0 is published
~~~

---

# 42. Roadmap status at document creation

At the time this roadmap is authored:

~~~text
PyTransformKit 1.0.0 stable          COMPLETE
Declarative specifications 28–39     COMPLETE
Implementation LOT-29                NOT STARTED
Implementation LOT-30                NOT STARTED
Implementation LOT-31                NOT STARTED
Implementation LOT-32                NOT STARTED
Implementation LOT-33                NOT STARTED
Implementation LOT-34                NOT STARTED
Implementation LOT-35                NOT STARTED
Implementation LOT-36                NOT STARTED
Implementation LOT-37                NOT STARTED
Implementation LOT-38                NOT STARTED
Implementation LOT-39                NOT STARTED
Implementation LOT-40                NOT STARTED
Implementation LOT-41                NOT STARTED
Implementation LOT-42                NOT STARTED
Implementation LOT-43                NOT STARTED
~~~

---

# 43. Immediate next action

The immediate implementation step after this document is:

~~~text
LOT-29 — Declarative Schema Package Bootstrap
~~~

That lot should:

~~~text
create schema_io package skeleton
add yaml optional extra
preserve lazy optional import
add bootstrap architecture/import tests
qualify on current CI
bump to 1.1.0a1 after qualification
~~~

No parser or public stable load/dump semantics should be implemented ahead of the required foundations.

---

# 44. Decisions frozen by this roadmap

## DEC-ROADMAP-01

Declarative schema ships on the PyTransformKit 1.1.0 line.

## DEC-ROADMAP-02

The implementation continues existing lot numbering at LOT-29.

## DEC-ROADMAP-03

The roadmap ends at LOT-43 with 1.1.0 stable.

## DEC-ROADMAP-04

Foundation/model/error/type/validator work precedes YAML parsing.

## DEC-ROADMAP-05

Public schema_io API is introduced only after load and dump internals exist.

## DEC-ROADMAP-06

Security closure precedes public compatibility freeze.

## DEC-ROADMAP-07

Machine-readable compatibility freeze precedes release-candidate qualification.

## DEC-ROADMAP-08

Python 3.11–3.14 and both core/yaml dependency profiles are release-blocking.

## DEC-ROADMAP-09

SchemaCodec V1 remains unchanged throughout this roadmap.

## DEC-ROADMAP-10

User-facing Getting Started and Reference Examples are finalized before stable publication.

---

# 45. Final roadmap

~~~text
PyTransformKit 1.0.0
       │
       ▼
LOT-29  Bootstrap                         1.1.0a1
       │
LOT-30  Definition Model                  1.1.0a2
       │
LOT-31  Error Model                       1.1.0a3
       │
LOT-32  Type Resolver / Exporter          1.1.0a4
       │
LOT-33  Semantic Validator                1.1.0a5
       │
LOT-34  Hardened YAML Parser              1.1.0a6
       │
LOT-35  Compiler / Loading                1.1.0a7
       │
LOT-36  Exporter / Emitter                1.1.0a8
       │
LOT-37  Public schema_io API              1.1.0b1
       │
LOT-38  Round-Trip / Wire Bridge          1.1.0b2
       │
LOT-39  Security Closure                  1.1.0b3
       │
LOT-40  Compatibility Freeze              1.1.0b4
       │
LOT-41  CI / Artifact Qualification       1.1.0rc1
       │
LOT-42  Documentation / RC Closure        1.1.0rc2
       │
LOT-43  Stable Release                    1.1.0
       │
       ▼
DECLARATIVE SCHEMA V1 COMPLETE
~~~

> **The roadmap deliberately builds semantic foundations first, exposes the public API late, freezes compatibility only after security closure, and promotes to 1.1.0 only from qualified artifacts.**