# 39 — PyTransformKit Declarative Schema — Test Matrix and Acceptance Criteria

> **Document status:** DRAFT NORMATIVE QUALIFICATION SPECIFICATION  
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
> **Python qualification matrix:** 3.11 / 3.12 / 3.13 / 3.14  
> **Declarative language version:** 1

---

# 1. Purpose

This document defines the complete executable qualification matrix for PyTransformKit declarative schema support.

It converts the design decisions from documents 28 through 38 into observable PASS/FAIL evidence.

The feature is not complete merely because YAML can be parsed.

It is complete only when syntax, semantics, security, Domain mapping, round-trip, public API, compatibility, packaging and release behavior are all qualified.

---

# 2. Qualification principle

The qualification model is:

~~~text
UNIT CORRECTNESS
      +
GRAMMAR CONFORMANCE
      +
TYPE MAPPING
      +
ERROR CONTRACT
      +
SECURITY HARDENING
      +
DOMAIN ROUND-TRIP
      +
WIRE BRIDGE
      +
PUBLIC API FREEZE
      +
PACKAGING / OPTIONAL EXTRA
      +
PYTHON MATRIX
      +
BUILT-ARTIFACT VALIDATION
      =
DECLARATIVE SCHEMA RELEASE QUALIFIED
~~~

---

# 3. Existing CI baseline

PyTransformKit already qualifies:

~~~text
Ruff lint
Ruff format
mypy
pytest
Python 3.11
Python 3.12
Python 3.13
Python 3.14
serialization contracts
security contracts
public API freeze
backwards compatibility
built wheel
sdist
stable release contract
~~~

Declarative schema qualification MUST extend these existing gates rather than bypass them.

---

# 4. Test taxonomy

The declarative feature SHOULD be covered by the following test families:

~~~text
DS-UNIT     definition/services unit tests
DS-GRAMMAR  declarative grammar tests
DS-TYPE     DataType mapping tests
DS-ERR      error-contract tests
DS-SEC      parser/security tests
DS-RT       semantic round-trip tests
DS-WIRE     SchemaCodec bridge tests
DS-API      public API contract tests
DS-ARCH     architecture/import-boundary tests
DS-PKG      package/optional-extra tests
DS-COMPAT   compatibility snapshot tests
DS-E2E      end-to-end reference scenarios
~~~

---

# 5. Recommended repository layout

A compatible test layout MAY use:

~~~text
tests/
├── unit/
│   └── schema_io/
│       ├── test_model.py
│       ├── test_validation.py
│       ├── test_type_resolution.py
│       ├── test_compiler.py
│       ├── test_exporter.py
│       └── test_yaml_parser.py
│
├── contract/
│   ├── schema_io/
│   │   ├── test_public_api.py
│   │   ├── test_roundtrip.py
│   │   ├── test_error_contract.py
│   │   ├── test_golden_yaml.py
│   │   └── test_wire_bridge.py
│   ├── security/
│   │   └── test_declarative_schema_security.py
│   └── release/
│       └── ...
│
└── fixtures/
    └── declarative_schema/
~~~

The exact filenames are implementation details.

The coverage categories are normative.

---

# 6. Core acceptance gate

No implementation lot may be considered complete unless all impacted tests pass under:

~~~bash
ruff check .
ruff format --check .
mypy src/pytransformkit
pytest
~~~

with the appropriate dependency profile installed.

---

# 7. Python support matrix

Declarative schema support MUST be qualified on:

~~~text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
~~~

The feature MUST NOT silently reduce the framework's current Python support matrix.

---

# 8. Two installation profiles

At minimum, two package profiles MUST be qualified.

~~~text
PROFILE A — CORE
pip install pytransformkit

PROFILE B — YAML
pip install "pytransformkit[yaml]"
~~~

The first verifies optionality.

The second verifies full declarative functionality.

---

# 9. Development profiles

Equivalent editable test profiles are:

~~~bash
pip install -e ".[dev]"
~~~

and:

~~~bash
pip install -e ".[dev,yaml]"
~~~

---

# 10. DS-UNIT — definition model

Unit tests MUST verify immutable value semantics for:

~~~text
SchemaDocument
SchemaDefinition
FieldDefinition
StructFieldDefinition
all TypeDefinition variants
~~~

Required properties include equality, frozen mutation rejection, tuple-based ordering and stable defaults.

---

# 11. DS-UNIT — model defaults

Tests MUST verify:

~~~text
FieldDefinition.nullable == True by default
StructFieldDefinition.nullable == True by default
ListTypeDefinition.element_nullable == True
MapTypeDefinition.value_nullable == True
IntegerTypeDefinition defaults to 64-bit signed
FloatTypeDefinition defaults to 64-bit
TimeTypeDefinition.unit == us
DurationTypeDefinition.unit == us
TimestampTypeDefinition == us + timezone None
~~~

---

# 12. DS-UNIT — local invariants

Tests MUST reject direct construction of impossible definition values where constructors own the invariant.

Representative cases:

~~~text
IntegerTypeDefinition(bits=7)
FloatTypeDefinition(bits=16)
DecimalTypeDefinition(precision=0, scale=0)
DecimalTypeDefinition(precision=10, scale=11)
TimeTypeDefinition(unit="minutes")
blank schema name where constructor validates it
blank field name where constructor validates it
~~~

---

# 13. DS-GRAMMAR — root forms

Positive tests MUST cover:

~~~text
single-schema document
multi-schema document
one-schema schemas mapping
empty Schema fields if Domain-valid
Unicode names
descriptions
nested types
~~~

---

# 14. DS-GRAMMAR — root failures

Negative tests MUST cover:

~~~text
non-mapping root
missing version
wrong version scalar type
unsupported version
schema and schemas both present
neither schema nor schemas present
unknown root property
~~~

Expected PTK-DECL code MUST be asserted.

---

# 15. DS-GRAMMAR — field forms

Positive field tests MUST cover:

~~~text
name + type only
nullable true
nullable false
description present
description omitted
all supported TypeDefinition forms
~~~

---

# 16. DS-GRAMMAR — field failures

Negative field tests MUST cover:

~~~text
missing name
blank name
missing type
nullable as string
nullable as integer
description null
description non-string
unknown property
duplicate field names
~~~

---

# 17. DS-TYPE — scalar mapping matrix

Every scalar authoring type MUST be tested against exact canonical Domain equality.

| YAML type | Expected Domain |
| --- | --- |
| string | StringType() |
| boolean | BooleanType() |
| int8 | IntegerType(8, signed=True) |
| int16 | IntegerType(16, signed=True) |
| int32 | IntegerType(32, signed=True) |
| int64 | IntegerType(64, signed=True) |
| uint8 | IntegerType(8, signed=False) |
| uint16 | IntegerType(16, signed=False) |
| uint32 | IntegerType(32, signed=False) |
| uint64 | IntegerType(64, signed=False) |
| float32 | FloatType(32) |
| float64 | FloatType(64) |
| binary | BinaryType() |
| date | DateType() |
| time | TimeType(unit="us") |
| timestamp | TimestampType(unit="us", timezone=None) |
| duration | DurationType(unit="us") |
| unknown | UnknownType() |

---

# 18. DS-TYPE — alias tests

Tests MUST verify:

~~~text
integer → IntegerType(bits=64, signed=True)
float   → FloatType(bits=64)
~~~

and canonical re-emission:

~~~text
integer input → int64 output
float input   → float64 output
~~~

No other undocumented aliases are accepted.

---

# 19. DS-TYPE — unsupported aliases

Negative tests SHOULD include:

~~~text
int
long
short
smallint
bigint
varchar
text
double
real
numeric
array
object
json
variant
~~~

All must fail as unknown declarative types unless a future language version explicitly adds them.

---

# 20. DS-TYPE — DecimalType

Positive tests MUST include:

~~~text
precision=1 scale=0
precision=18 scale=2
scale == precision
~~~

Negative tests MUST include:

~~~text
precision missing
scale missing
precision <= 0
scale < 0
scale > precision
precision string
scale string
unknown decimal property
~~~

---

# 21. DS-TYPE — temporal units

Each supported unit MUST be tested:

~~~text
s
ms
us
ns
~~~

Negative values MUST include:

~~~text
seconds
milliseconds
microseconds
NS
blank
null
integer
~~~

---

# 22. DS-TYPE — TimestampType

Tests MUST cover:

~~~text
default timestamp
unit s
unit ms
unit us
unit ns
timezone UTC
timezone Europe/Paris
non-default unit + timezone
blank timezone rejection
explicit null timezone rejection
~~~

---

# 23. DS-TYPE — ListType

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
unknown list property
~~~

---

# 24. DS-TYPE — StructType

Tests MUST cover:

~~~text
empty struct if Domain-valid
one field
multiple fields
field order
default nested nullable
explicit nested nullable
nested struct
list field
map field
duplicate nested field
nested description rejection
unknown nested property
~~~

---

# 25. DS-TYPE — MapType

Tests MUST cover:

~~~text
primitive key/value
nested value
nested key allowed by Domain
value_nullable true
value_nullable false
default value_nullable
missing key
missing value
invalid key declaration
invalid value declaration
unknown map property
~~~

---

# 26. DS-TYPE — recursive stress

A representative deeply nested but valid type MUST be tested.

Example shape:

~~~text
list
 └── struct
      └── map
           └── list
                └── decimal
~~~

The exact canonical DataType tree MUST be asserted.

---

# 27. DS-ERR — hierarchy

Tests MUST verify every released declarative exception inherits from PyTransformKitError and DeclarativeSchemaError according to document 35.

The exact public parent hierarchy must match the compatibility snapshot.

---

# 28. DS-ERR — code uniqueness

Tests MUST verify:

~~~text
PTK-DECL-000 through PTK-DECL-013
~~~

are unique and correctly bound to their public exception classes.

Existing PTK-SCHEMA codes MUST remain unchanged.

---

# 29. DS-ERR — structured context

Tests SHOULD assert:

~~~text
source
line
column
object_path
property_name
type_name
field_name
schema_name
required_count
actual_count
dependency_name
path
limit_name
limit
actual
~~~

where relevant.

---

# 30. DS-ERR — message policy

Tests SHOULD assert key actionable fragments rather than freeze entire prose unless exact wording is deliberately part of a compatibility contract.

Machine-readable assertions MUST prefer:

~~~text
exception class
error_code
structured attributes
~~~

---

# 31. DS-ERR — chaining

Tests MUST prove known wrapped failures retain __cause__.

Representative causes:

~~~text
PyYAML parser exception
OSError
UnicodeDecodeError
canonical Domain ValueError
DuplicateFieldError when translated
~~~

---

# 32. DS-SEC — malformed YAML

Malformed YAML MUST raise:

~~~text
DeclarativeSchemaParseError
PTK-DECL-001
~~~

Raw parser exceptions must not become the primary public failure.

---

# 33. DS-SEC — duplicate keys

Duplicate keys MUST fail recursively.

Coverage MUST include:

~~~text
root mapping
schema mapping
field mapping
decimal parameters
timestamp parameters
list mapping
map mapping
nested struct field mapping
~~~

Expected code:

~~~text
PTK-DECL-006
~~~

---

# 34. DS-SEC — forbidden YAML features

Tests MUST reject:

~~~text
anchors
aliases
merge keys
custom tags
python/object tags
multi-document streams
~~~

Expected primary code:

~~~text
PTK-DECL-001
~~~

except duplicate-key-specific cases.

---

# 35. DS-SEC — object-construction proof

A harmless sentinel test MUST prove that Python-object YAML syntax cannot instantiate or execute arbitrary Python behavior.

The test MUST not use destructive commands.

---

# 36. DS-SEC — scalar ambiguity

Tests MUST verify these values are not silently interpreted with unsafe YAML 1.1 semantics:

~~~text
yes
no
on
off
2026-10-01
00123 where policy requires string/rejection
~~~

ISO-like date strings MUST NOT become datetime/date objects.

---

# 37. DS-SEC — non-finite numbers

Inputs that could produce:

~~~text
NaN
+Infinity
-Infinity
~~~

MUST fail before normalized definitions or canonical Domain construction.

---

# 38. DS-SEC — payload boundary

Tests MUST cover the exact byte limit boundary.

~~~text
payload == 1,048,576 bytes      → may proceed
payload == 1,048,577 bytes      → PTK-DECL-013
~~~

The valid boundary fixture must otherwise be syntactically valid.

---

# 39. DS-SEC — nesting boundary

Tests MUST verify:

~~~text
depth == 64       → allowed if otherwise valid
depth == 65       → PTK-DECL-013
~~~

The implementation's exact depth-counting algorithm MUST be covered by tests.

---

# 40. DS-SEC — schema count

Tests MUST verify:

~~~text
schema count == 256       → accepted if otherwise valid
schema count == 257       → PTK-DECL-013
~~~

subject to the final constants frozen in implementation.

---

# 41. DS-SEC — field counts

Tests MUST verify:

~~~text
top-level fields/schema at limit
top-level fields/schema above limit
total recursive field nodes at limit
total recursive field nodes above limit
~~~

Limit failures use PTK-DECL-013.

---

# 42. DS-SEC — no network

A test SHOULD deny or monkeypatch network access and prove parsing performs no network calls.

Document content resembling URLs must remain data or fail grammar validation.

---

# 43. DS-SEC — no secondary file reads

Tests SHOULD monitor filesystem access.

Only the explicit file passed to load_schema/load_schemas may be read.

Document content MUST NOT cause includes or recursive file access.

---

# 44. DS-SEC — no environment interpolation

A test MUST prove environment-variable-looking strings are not resolved from os.environ.

Document parsing must not inspect or substitute process environment values.

---

# 45. DS-SEC — no plugin activation

An unknown type MUST fail with PTK-DECL-005 without triggering entry-point discovery or plugin activation.

---

# 46. DS-ARCH — Domain independence

Architecture tests MUST verify canonical Domain modules do NOT import:

~~~text
pytransformkit.schema_io
PyYAML
declarative parser modules
~~~

The dependency direction remains toward the Domain, never from it.

---

# 47. DS-ARCH — engine independence

Tests MUST prove declarative load/dump succeeds without:

~~~text
pandas
polars
pyarrow
duckdb
~~~

installed.

---

# 48. DS-ARCH — optional dependency import safety

In a core-only environment:

~~~python
import pytransformkit
import pytransformkit.schema_io
~~~

SHOULD succeed without importing PyYAML.

Calling a YAML operation then raises PTK-DECL-010.

---

# 49. DS-ARCH — global PyYAML isolation

Tests SHOULD verify PyTransformKit does not mutate global PyYAML SafeLoader resolver or constructor behavior.

The custom hardened loader must be isolated to PyTransformKit.

---

# 50. DS-RT — primitive round-trip

For every primitive supported DataType:

~~~text
DataType
 ↓ dumps_schema
YAML
 ↓ loads_schema
DataType'

DataType == DataType'
~~~

must hold through a containing Schema.

---

# 51. DS-RT — nested round-trip

Round-trip MUST preserve nested combinations of:

~~~text
ListType
StructType
MapType
DecimalType
temporal types
~~~

including recursive nullability.

---

# 52. DS-RT — field semantics

Round-trip MUST preserve:

~~~text
field name
field order
data type
nullable
description
~~~

for every top-level Field.

---

# 53. DS-RT — nested struct semantics

Round-trip MUST preserve:

~~~text
StructField name
StructField order
StructField data_type
StructField nullable
~~~

No nested description may be introduced or silently dropped.

---

# 54. DS-RT — normalization

Tests MUST prove semantically equivalent non-canonical inputs normalize to canonical output.

Representative cases:

~~~text
integer → int64
float → float64
default timestamp structured form → short timestamp
omitted nullable → explicit emitted nullable
ambiguous string → safely quoted output
~~~

---

# 55. DS-RT — comments/formatting

Tests MAY explicitly document that comments, blank lines, original indentation and quoting style are not preserved.

Loss of these non-semantic authoring details is expected behavior.

---

# 56. DS-RT — deterministic emission

Repeated emission of equal SchemaDocument semantics under the same implementation version MUST produce identical text.

~~~text
emit(x) == emit(x)
~~~

The output MUST end in one final newline.

---

# 57. DS-RT — parser/emitter closure

Every canonical YAML fixture emitted by PyTransformKit MUST parse successfully through the hardened parser.

The emitter MUST never generate a construct forbidden by the parser.

---

# 58. DS-RT — Unicode

Tests MUST cover Unicode schema names, field names and descriptions.

After dump/load, Python string values must be equal.

---

# 59. DS-RT — name boundary

Tests MUST prove that changing declarative name does not alter Schema equality.

~~~text
name=customers + Schema X
name=clients   + Schema X
~~~

load to equal canonical Schema values when field content is equal.

---

# 60. DS-RT — multi-schema identity

Multi-schema dump/load MUST preserve:

~~~text
mapping keys
mapping iteration order
Schema equality for every value
~~~

---

# 61. DS-WIRE — SchemaCodec preservation

Existing SchemaCodec contract MUST remain:

~~~text
contract = pytransformkit.schema
contract_version = 1
~~~

Declarative implementation must not alter its golden fixtures or canonical bytes.

---

# 62. DS-WIRE — YAML to wire bridge

Required test:

~~~text
YAML
 ↓ loads_schema
Schema A
 ↓ SchemaCodec.to_json/from_json
Schema B

Schema A == Schema B
~~~

---

# 63. DS-WIRE — wire to YAML bridge

Required test:

~~~text
golden SchemaCodec JSON
 ↓ SchemaCodec.from_json
Schema A
 ↓ dumps_schema
YAML
 ↓ loads_schema
Schema B

Schema A == Schema B
~~~

for declarative-V1-representable Schema values.

---

# 64. DS-WIRE — fingerprint invariance

Equivalent Schema values produced by Python construction, YAML loading and SchemaCodec decoding MUST have equal canonical fingerprints.

~~~text
SchemaCodec().fingerprint(schema_python)
==
SchemaCodec().fingerprint(schema_yaml)
==
SchemaCodec().fingerprint(schema_wire)
~~~

---

# 65. DS-WIRE — name independence

Changing declarative schema name MUST NOT change SchemaCodec fingerprint for the same Schema object.

YAML bytes themselves are not canonical Schema fingerprint input.

---

# 66. DS-API — namespace exports

Contract tests MUST verify:

~~~text
pytransformkit.schema_io.__all__
~~~

contains exactly the eight stable helpers defined in document 38.

---

# 67. DS-API — root isolation

Contract tests MUST verify none of the eight helpers appears in:

~~~python
pytransformkit.__all__
~~~

The existing canonical root remains unchanged.

---

# 68. DS-API — signatures

Exact stable signatures MUST be inspected.

Expected:

~~~text
load_schema(path)
loads_schema(text, *, source=None)
load_schemas(path)
loads_schemas(text, *, source=None)
dump_schema(schema, path, *, name)
dumps_schema(schema, *, name)
dump_schemas(schemas, path)
dumps_schemas(schemas)
~~~

No **kwargs escape hatch is permitted.

---

# 69. DS-API — single-schema behavior

Tests MUST verify:

~~~text
single document → Schema
multi-schema document → PTK-DECL-009
name not embedded into Schema
source affects diagnostics only
~~~

---

# 70. DS-API — multi-schema behavior

Tests MUST verify:

~~~text
single schema → one-entry dict
multiple schemas → ordered dict
invalid one-of-many → full failure
mapping values are canonical Schema
~~~

---

# 71. DS-API — dump behavior

Tests MUST verify:

~~~text
name required and keyword-only
exact caller path used
existing target overwritten
parent directories not auto-created
UTF-8 output
one final newline
no implicit backup
~~~

---

# 72. DS-API — unsupported inputs

Tests SHOULD verify clean failures for:

~~~text
non-PathLike file path
non-str in-memory text
blank export name
non-Schema dump value
non-string multi-schema key
non-Schema mapping value
~~~

Exact exception classification should follow the public API/error specification.

---

# 73. DS-COMPAT — public API snapshot

The existing public API snapshot tooling MUST be extended to include:

~~~text
pytransformkit.schema_io
eight stable signatures
yaml stable runtime extra
new public declarative exception hierarchy
~~~

All existing V1 categories remain unchanged except additive expected deltas.

---

# 74. DS-COMPAT — root freeze

The compatibility test MUST explicitly prove existing root exports are unchanged.

No declarative helper or declarative error is promoted to the root.

---

# 75. DS-COMPAT — error catalogue

The machine-readable error catalogue MUST be extended additively with PTK-DECL-* entries.

Tests MUST verify existing PTK-* code assignments are unchanged.

---

# 76. DS-COMPAT — extras snapshot

The machine-readable extras snapshot MUST add:

~~~text
yaml
~~~

to stable runtime extras.

Existing extras remain unchanged.

---

# 77. DS-COMPAT — wire snapshot

Public API snapshot tests MUST prove:

~~~text
SchemaCodec.contract == pytransformkit.schema
SchemaCodec.contract_version == 1
~~~

and all other frozen wire contracts remain unchanged.

---

# 78. DS-PKG — core wheel

A built wheel installed without optional extras MUST satisfy:

~~~text
pip check succeeds
import pytransformkit succeeds
import pytransformkit.schema_io succeeds if lazy import design is implemented
PyYAML is absent
schema_io YAML operation raises PTK-DECL-010
~~~

---

# 79. DS-PKG — YAML wheel capability

A clean environment MUST install:

~~~bash
pip install "dist/pytransformkit-*.whl[yaml]"
~~~

or equivalent wheel + PyYAML dependency installation.

Then a real load/dump round-trip smoke MUST pass.

---

# 80. DS-PKG — sdist

The source distribution MUST install with:

~~~text
core only
yaml extra
~~~

and expose the same public API behavior as the wheel.

---

# 81. DS-PKG — metadata

Distribution metadata MUST expose:

~~~text
Provides-Extra: yaml
~~~

through normal packaging metadata.

PyYAML must not appear as an unconditional dependency.

---

# 82. DS-PKG — optional dependency isolation

Core package qualification MUST prove PyYAML is not installed transitively by PyTransformKit itself.

This protects the zero-core-dependency baseline.

---

# 83. YAML-specific CI job

The implementation SHOULD add a dedicated CI job similar to:

~~~yaml
declarative-schema-contract:
  runs-on: ubuntu-latest
  steps:
    - checkout
    - setup Python 3.11
    - pip install -e ".[dev,yaml]"
    - pytest declarative-schema unit/contract suites
~~~

The exact workflow syntax may follow repository conventions.

---

# 84. Python matrix with YAML

Declarative functionality MUST execute on all supported Python versions.

Preferred CI coverage:

~~~text
Python 3.11 + [dev,yaml]
Python 3.12 + [dev,yaml]
Python 3.13 + [dev,yaml]
Python 3.14 + [dev,yaml]
~~~

This can be a dedicated matrix or integrated into the existing tests matrix.

---

# 85. Core-without-YAML CI gate

A dedicated negative-capability test SHOULD run in an environment where PyYAML is definitely absent.

Required evidence:

~~~text
core import                           PASS
schema_io import                      PASS
loads_schema(...)                    PTK-DECL-010
no accidental PyYAML dependency      PASS
~~~

---

# 86. Security-contract integration

The existing security-contract CI job SHOULD include declarative parser hardening tests when the yaml extra is installed.

Security qualification MUST not rely only on the generic pytest job.

---

# 87. Serialization-contract integration

The existing serialization-contract job MUST continue to qualify current wire contracts unchanged.

Declarative wire bridge tests MAY be added alongside it, but YAML fixtures do not replace SchemaCodec golden fixtures.

---

# 88. API-freeze integration

The built-wheel public API freeze job MUST eventually verify the released schema_io namespace and signatures from an installed wheel.

This prevents source-tree-only success.

---

# 89. Backwards-compatibility integration

The backwards-compatibility gate MUST verify the declarative additions do not alter existing:

~~~text
root exports
legacy compatibility names
wire contract IDs
existing exception codes
engine IDs
existing extras
~~~

except for explicitly additive snapshot changes.

---

# 90. DS-E2E — reference single-schema scenario

An end-to-end test MUST cover:

~~~text
customers.yml
 ↓ load_schema
Schema
 ↓ inspect fields/types
 ↓ dumps_schema(name=customers)
YAML
 ↓ loads_schema
equal Schema
~~~

---

# 91. DS-E2E — reference multi-schema scenario

An end-to-end test MUST cover:

~~~text
schemas.yml
 ├── customers
 ├── orders
 └── payments
      ↓
load_schemas
      ↓
ordered dict[str, Schema]
      ↓
dumps_schemas
      ↓
loads_schemas
      ↓
same keys/order/Schema values
~~~

---

# 92. DS-E2E — Python vs YAML equivalence

One reference Schema MUST be authored both:

~~~text
directly in Python
and
through declarative YAML
~~~

The resulting Schema objects MUST compare equal.

---

# 93. DS-E2E — no-engine environment

The reference YAML scenario MUST succeed in an environment containing no physical engine extras.

This proves the feature belongs to logical schema authoring rather than engine execution.

---

# 94. Property-based testing

Property-based testing SHOULD be considered for DataType round-trip.

A Hypothesis strategy MAY generate bounded valid canonical DataType trees.

Core property:

~~~text
T == parse_type(emit_type(T))
~~~

within declarative V1 representability limits.

---

# 95. Property-based depth bound

Generated recursive types MUST respect the security depth limit so property tests remain bounded and deterministic.

Negative strategies MAY generate exactly-one-over-limit structures.

---

# 96. Mutation testing targets

Optional mutation testing would be especially valuable around:

~~~text
duplicate-key detection
unknown-property rejection
integer signedness
decimal scale validation
timestamp timezone preservation
nullable defaults
alias normalization
cardinality checks
payload/depth comparison operators
~~~

Mutation testing is recommended, not a release blocker for the first implementation.

---

# 97. Coverage expectation

The declarative implementation SHOULD achieve strong branch coverage, particularly in:

~~~text
security parser branches
error translation
type dispatch
nested recursion
export dispatch
optional dependency paths
~~~

A numeric coverage threshold MAY follow repository-wide policy rather than being independently frozen here.

---

# 98. Performance smoke

Declarative parsing does not require a full benchmark suite initially.

However, a smoke test SHOULD verify ordinary schema documents parse without pathological overhead.

No engine initialization, network access or plugin discovery may occur.

---

# 99. Complexity expectation

For ordinary input, work SHOULD remain approximately linear in declarative node count.

Tests MAY use instrumentation to detect accidental repeated expansion or quadratic behavior in large-but-valid fixtures.

---

# 100. Release blocker definition

Any of the following is a release blocker:

~~~text
arbitrary object construction possible
duplicate key accepted
unknown property silently ignored
unknown type converted to UnknownType
round-trip loses canonical Domain state
SchemaCodec wire contract changes unintentionally
root API changes unintentionally
core import requires PyYAML
Python 3.11–3.14 regression
built wheel differs from source behavior
PTK-DECL code collision
~~~

---

# 101. Required release gates

Before feature release, all of the following MUST be green:

~~~text
Ruff lint
Ruff format
mypy
Python 3.11 tests
Python 3.12 tests
Python 3.13 tests
Python 3.14 tests
declarative unit suite
declarative grammar suite
declarative type suite
declarative error suite
declarative security suite
declarative round-trip suite
wire bridge suite
schema_io public API contract
core-without-yaml contract
yaml-extra contract
public API freeze
error catalogue
backwards compatibility
wheel qualification
sdist qualification
~~~

---

# 102. Acceptance status categories

Each implementation lot SHOULD finish in one of:

~~~text
NOT STARTED
IMPLEMENTED
TESTED
QUALIFIED
MERGED
~~~

A lot is not QUALIFIED until its required test families are green.

---

# 103. Requirements traceability

Implementation PRs SHOULD reference the relevant design decisions and test IDs.

Example:

~~~text
DEC-SEC-10 duplicate keys rejected
  ↳ DS-SEC duplicate-key tests

DEC-RT-11 SchemaCodec fingerprint authority
  ↳ DS-WIRE fingerprint invariance

DEC-API-03 eight stable functions
  ↳ DS-API namespace/signature tests
~~~

---

# 104. Specification-to-test traceability

| Specification | Primary evidence |
| --- | --- |
| 31 grammar | DS-GRAMMAR |
| 32 type mapping | DS-TYPE |
| 33 definition model | DS-UNIT |
| 34 services | DS-UNIT / DS-E2E |
| 35 errors | DS-ERR |
| 36 security | DS-SEC / DS-ARCH |
| 37 round-trip | DS-RT / DS-WIRE |
| 38 public API | DS-API / DS-COMPAT / DS-PKG |

---

# 105. Minimum fixture catalogue

The implementation SHOULD include at least:

~~~text
basic_schema.yml
multi_schema.yml
all_scalar_types.yml
decimal.yml
temporal.yml
nested_types.yml
unicode.yml
ambiguous_strings.yml
duplicate_key.yml
unknown_property.yml
unknown_type.yml
anchor.yml
alias.yml
merge_key.yml
custom_tag.yml
multi_document.yml
deeply_nested.yml
oversized_document.yml
~~~

---

# 106. Golden declarative fixtures

Generated canonical YAML SHOULD have golden fixtures for representative schemas.

Golden YAML protects deterministic emission.

It does not replace semantic round-trip assertions.

---

# 107. Golden wire fixtures

Existing wire golden fixtures remain authoritative for SchemaCodec.

They MUST continue to pass unchanged after declarative support is added.

---

# 108. No live external dependency tests

Declarative schema qualification requires no network service, cloud account, database or physical execution engine.

All release-blocking tests SHOULD be locally reproducible.

---

# 109. Local qualification command

A developer SHOULD be able to run the feature suite locally with a command equivalent to:

~~~bash
pip install -e ".[dev,yaml]"
pytest tests/unit/schema_io tests/contract/schema_io tests/contract/security -ra
~~~

Exact test paths may be adapted to the final repository layout.

---

# 110. Full repository qualification

Before merge/release, the entire repository test suite MUST still pass.

Declarative qualification is additive:

~~~text
new tests green
AND
all old tests still green
~~~

---

# 111. Built-wheel qualification

Source-tree success alone is insufficient.

The built wheel MUST be installed in clean environments and tested for:

~~~text
core import
schema_io public imports
missing-yaml behavior
yaml-extra behavior
API snapshot
error catalogue
basic YAML round-trip
~~~

---

# 112. Release acceptance decision

Declarative schema support is release-ready only if no known release blocker remains and every MUST-level criterion in documents 31–39 has executable evidence.

Open SHOULD-level improvements may be deferred only when documented and non-contractual.

---

# 113. Decisions frozen by this document

## DEC-TEST-01

Declarative schema qualification spans unit, grammar, type, error, security, round-trip, wire, API, architecture, packaging and compatibility tests.

## DEC-TEST-02

Python 3.11 through 3.14 are mandatory.

## DEC-TEST-03

Both core-only and yaml-extra environments are mandatory.

## DEC-TEST-04

Existing SchemaCodec golden contracts remain unchanged.

## DEC-TEST-05

Built-wheel qualification is mandatory.

## DEC-TEST-06

Security tests are release-blocking.

## DEC-TEST-07

Root API isolation is release-blocking.

## DEC-TEST-08

PTK-DECL error-code uniqueness and compatibility are release-blocking.

## DEC-TEST-09

Round-trip semantic equality is release-blocking.

## DEC-TEST-10

Unknown properties/types and duplicate keys must fail closed.

## DEC-TEST-11

No physical engine dependency is required for qualification.

## DEC-TEST-12

Declarative support extends existing CI gates rather than replacing them.

---

# 114. Final acceptance checklist

A release candidate passes this specification only when every item below is true:

~~~text
[ ] schema_io public namespace matches document 38
[ ] eight stable signatures match exactly
[ ] root exports unchanged
[ ] yaml extra is optional and qualified
[ ] PyYAML absent from core dependency set
[ ] Python 3.11 green
[ ] Python 3.12 green
[ ] Python 3.13 green
[ ] Python 3.14 green
[ ] all declarative grammar tests green
[ ] all DataType mappings green
[ ] all PTK-DECL error contracts green
[ ] duplicate-key tests green
[ ] tag/anchor/alias/merge rejection green
[ ] payload/depth/count limits green
[ ] no network/include/env/plugin side effects
[ ] Schema semantic round-trip green
[ ] nested round-trip green
[ ] multi-schema name/order round-trip green
[ ] deterministic YAML emission green
[ ] SchemaCodec bridge green
[ ] SchemaCodec fingerprints invariant
[ ] existing wire golden fixtures unchanged
[ ] public API snapshot updated additively
[ ] error catalogue updated additively
[ ] core wheel qualification green
[ ] yaml wheel qualification green
[ ] sdist qualification green
[ ] full repository suite green
~~~

---

# 115. Next document

The next document converts this qualification model into the implementation sequence:

~~~text
40_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_IMPLEMENTATION_ROADMAP.md
~~~

It must split the work into implementation lots covering:

~~~text
package/bootstrap
definition model
errors
type resolver
validator
hardened YAML parser
compiler
exporter/emitter
public schema_io API
round-trip/wire bridge
security hardening
public compatibility snapshot
CI matrix
docs/examples
release qualification
~~~

---

# 116. Final summary

Declarative schema support is not considered successful because one YAML example works.

It must prove:

~~~text
correct syntax
+ correct semantics
+ strict errors
+ hardened parsing
+ lossless Domain mapping
+ deterministic export
+ stable public API
+ unchanged wire contracts
+ optional dependency isolation
+ Python 3.11–3.14 compatibility
+ built-artifact qualification
~~~

Only then is the feature ready to enter the release line.

> **A declarative contract is trustworthy only when its parser, semantics, compatibility and packaging are all executable specifications.**