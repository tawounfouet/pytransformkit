# 36 — PyTransformKit Declarative Schema — Security and Parsing Policy

> **Document status:** DRAFT NORMATIVE SPECIFICATION  
> **Depends on:** 31_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SPECIFICATION.md  
> **Depends on:** 34_PYTRANSFORMKIT_SCHEMA_LOADER_COMPILER_AND_EXPORTER_SPEC.md  
> **Depends on:** 35_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_VALIDATION_AND_ERROR_MODEL.md  
> **Security baseline:** docs/SECURITY_AND_THREAT_MODEL.md  
> **Declarative language version:** 1  
> **Primary format:** YAML

---

# 1. Purpose

This document defines the security policy for parsing declarative PyTransformKit schema documents.

It freezes the YAML dependency strategy, parser trust boundary, safe-loader policy, YAML feature restrictions, duplicate-key rejection, scalar resolution, resource limits, denial-of-service protections, parser error translation, optional dependency behavior and security-test requirements.

The primary security objective is:

> **A declarative schema file is untrusted data, not executable Python and not a privileged configuration channel.**

---

# 2. Threat model

Declarative schema input may originate from a repository checkout, generated artifact, CI pipeline, user upload, internal system, external integration or untrusted contributor.

The parser MUST therefore assume that every document can be malicious.

---

# 3. Protected assets

The parser must protect:

- the Python process;
- local filesystem integrity;
- process environment;
- network credentials;
- imported modules;
- CPU and memory;
- canonical Domain invariants;
- downstream engine/runtime state;
- logs and diagnostics.

---

# 4. Security boundary

~~~text
UNTRUSTED YAML TEXT
        ↓
security checks
        ↓
restricted YAML parser
        ↓
plain safe values
        ↓
strict declarative decoder
        ↓
SchemaDocument
        ↓
trusted application validation
~~~

No parser-controlled object may cross directly into the canonical Domain.

---

# 5. Fundamental security rule

The YAML document MUST be treated strictly as data.

The implementation MUST NOT permit YAML to instantiate arbitrary Python classes, import modules, execute functions, access environment variables, read secondary files, fetch network resources, execute shell expressions, run templates or activate PyTransformKit plugins.

---

# 6. YAML dependency decision

Declarative schema V1 SHOULD use:

~~~text
PyYAML >=6,<7
~~~

as an optional dependency.

Recommended extra:

~~~toml
[project.optional-dependencies]
yaml = [
  "PyYAML>=6,<7",
]
~~~

The exact minimum version MUST be qualified against every supported Python version before release.

---

# 7. Why PyYAML

PyYAML is selected because the feature needs safe YAML parsing rather than comment-preserving round-trip editing, benefits from a small optional dependency surface, and can be hardened through dedicated loader, constructor, resolver and token policies.

PyTransformKit MUST NOT rely on PyYAML defaults alone for its security policy.

---

# 8. Semantic rather than textual round-trip

Declarative V1 does not promise preservation of comments, whitespace, quoting style, original key formatting, anchors or aliases.

The required round-trip is:

~~~text
Schema → YAML → Schema
~~~

not byte-for-byte source preservation.

---

# 9. Optional dependency boundary

This MUST succeed without PyYAML installed:

~~~python
import pytransformkit
~~~

PyYAML is required only when a YAML declarative capability is invoked.

---

# 10. Missing dependency behavior

If PyYAML is unavailable when YAML functionality is invoked, the API MUST raise:

~~~text
DeclarativeSchemaDependencyError
PTK-DECL-010
~~~

Raw ImportError MUST NOT be the primary public contract.

---

# 11. Unsafe loaders are forbidden

The implementation MUST NOT use an unsafe arbitrary-object YAML loader.

The following capabilities are forbidden:

~~~text
UnsafeLoader
FullLoader for declarative input
python/object constructors
python/name constructors
python/module constructors
~~~

---

# 12. PyTransformKit-owned loader

The implementation SHOULD define a dedicated loader owned by PyTransformKit.

Conceptually:

~~~python
class DeclarativeSafeLoader(yaml.SafeLoader):
    ...
~~~

The loader MUST be hardened specifically for the declarative grammar.

Security behavior MUST NOT depend on undocumented defaults.

---

# 13. SafeLoader is necessary but insufficient

SafeLoader alone does not satisfy this specification because PyTransformKit additionally requires duplicate-key rejection, YAML boolean ambiguity control, anchor/alias prohibition, merge-key prohibition, multi-document prohibition, resource limits and strict unknown-key checks.

Therefore plain safe_load alone is NOT an acceptable implementation.

---

# 14. Parsing pipeline

~~~text
bytes / str
   ↓
UTF-8 + payload-size validation
   ↓
YAML token preflight
   ↓
restricted safe parse
   ↓
plain Python values
   ↓
nesting/count validation
   ↓
strict declarative decoder
   ↓
SchemaDocument
~~~

Each boundary MUST have independent tests.

---

# 15. Input encoding

Declarative documents MUST use UTF-8.

A UTF-8 BOM MAY be accepted.

Emitters SHOULD write UTF-8 without BOM.

Invalid UTF-8 MUST become a PyTransformKit-owned parse or I/O failure according to the API entry point.

---

# 16. Maximum payload size

The default maximum declarative YAML payload size SHALL be:

~~~text
1,048,576 bytes
1 MiB
~~~

Recommended constant:

~~~python
DEFAULT_MAX_DECLARATIVE_PAYLOAD_BYTES = 1_048_576
~~~

This intentionally aligns with the existing canonical serialization payload bound.

---

# 17. Payload measurement

For str input, size MUST be measured against UTF-8 encoded bytes.

For bytes input, raw byte length is used.

The payload bound MUST be checked before full YAML construction.

---

# 18. Payload-limit failure

Exceeding the configured payload bound raises:

~~~text
DeclarativeSchemaLimitError
PTK-DECL-013
~~~

with diagnostic context such as:

~~~text
limit_name = payload_bytes
limit = 1048576
actual = <actual bytes>
~~~

---

# 19. Maximum nesting depth

The default maximum nested container depth SHALL be:

~~~text
64
~~~

Recommended constant:

~~~python
DEFAULT_MAX_DECLARATIVE_NESTING_DEPTH = 64
~~~

This also aligns with existing V1 canonical serialization security policy.

---

# 20. Nesting-depth failure

Depth above the configured limit raises PTK-DECL-013.

The failure MUST occur before recursive compilation can exhaust the Python call stack.

The implementation MUST document one deterministic depth-counting algorithm.

---

# 21. Maximum schema count

The default maximum number of schemas in one document SHOULD be:

~~~text
256
~~~

Recommended constant:

~~~python
DEFAULT_MAX_DECLARATIVE_SCHEMAS = 256
~~~

---

# 22. Maximum fields per schema

The default maximum number of top-level fields in one schema SHOULD be:

~~~text
10,000
~~~

Recommended constant:

~~~python
DEFAULT_MAX_DECLARATIVE_FIELDS_PER_SCHEMA = 10_000
~~~

This is a defensive bound, not a recommended schema width.

---

# 23. Maximum total field nodes

The default total number of top-level and recursive StructField nodes SHOULD be:

~~~text
50,000
~~~

Recommended constant:

~~~python
DEFAULT_MAX_DECLARATIVE_FIELD_NODES = 50_000
~~~

---

# 24. Count-limit behavior

Count limits are checked before or during strict decoding.

Exceeding any configured bound raises PTK-DECL-013.

No partial SchemaDocument is returned.

---

# 25. Single YAML document

Exactly one YAML document is permitted per input stream.

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

Multiple logical schemas must use the declarative schemas mapping.

---

# 26. Multi-document handling

The implementation MUST NOT use a load-all API and silently choose one document.

Trailing YAML documents MUST NOT be ignored.

Multiple YAML documents raise:

~~~text
DeclarativeSchemaParseError
PTK-DECL-001
~~~

---

# 27. Custom YAML tags

Custom YAML tags are forbidden.

Invalid:

~~~yaml
value: !CustomTag abc
~~~

Invalid:

~~~yaml
value: !!python/object:pkg.Type {}
~~~

No document-defined tag is part of declarative schema V1.

---

# 28. Anchors

YAML anchors are forbidden.

Invalid:

~~~yaml
base: &common
  type: string
~~~

The declarative language deliberately has no identity/reference semantics.

---

# 29. Aliases

YAML aliases are forbidden.

Invalid:

~~~yaml
type: *common
~~~

This prevents hidden semantic reuse, cyclic graphs, expansion amplification and non-local interpretation.

---

# 30. Anchor/alias preflight

Token scanning SHOULD reject anchor and alias tokens before YAML object construction.

Rejected anchors and aliases raise PTK-DECL-001.

The implementation MUST NOT rely only on post-load object-identity checks.

---

# 31. Merge keys

YAML merge keys are forbidden.

Invalid:

~~~yaml
field:
  <<: *common
  name: customer_id
~~~

The parser MUST reject merge semantics before they can hide duplicate or inherited declarative properties.

---

# 32. Duplicate mapping keys

Duplicate keys are always forbidden.

Invalid:

~~~yaml
nullable: true
nullable: false
~~~

The parser MUST fail before any last-value-wins normalization.

---

# 33. Duplicate-key enforcement

Mapping construction SHOULD maintain a seen-key set recursively.

Duplicate keys raise:

~~~text
DeclarativeSchemaDuplicateKeyError
PTK-DECL-006
~~~

This applies at the root and every nested mapping level.

---

# 34. Mapping keys

Declarative grammar keys MUST be strings.

Invalid:

~~~yaml
1: customer_id
~~~

A non-string mapping key MUST fail strict decoding and MUST NOT be coerced to a string.

---

# 35. Scalar-resolution threat

Traditional YAML resolution can interpret values such as:

~~~text
yes
no
on
off
2026-10-01
0123
~~~

as non-string types.

That is too ambiguous for a strict declarative contract language.

---

# 36. Scalar-resolution policy

PyTransformKit MUST use a controlled scalar resolver.

The accepted implicit scalar classes SHOULD be limited to:

~~~text
string
boolean
integer
float
null
~~~

Declarative validation then decides where each class is legal.

Implicit timestamp/date resolution MUST be disabled.

---

# 37. Boolean lexical policy

Only these unquoted spellings SHOULD resolve as booleans:

~~~text
true
false
True
False
TRUE
FALSE
~~~

Canonical emission uses lowercase true/false.

The following MUST remain strings:

~~~text
yes
no
on
off
y
n
~~~

---

# 38. Integer lexical policy

Ordinary base-10 integer syntax MAY resolve to int.

Ambiguous legacy forms SHOULD be rejected or preserved as strings instead of receiving YAML 1.1 octal/sexagesimal semantics.

Declarative numeric parameters SHOULD use ordinary decimal integer syntax.

---

# 39. Float lexical policy

Ordinary finite decimal/scientific float syntax MAY resolve to float.

Non-finite values are forbidden:

~~~text
.nan
.inf
-.inf
NaN
Infinity
~~~

---

# 40. Null lexical policy

YAML null values MAY parse to None.

The strict declarative decoder then rejects None wherever explicit null is forbidden.

Safe parsing of null and semantic acceptance of null are separate decisions.

---

# 41. Implicit timestamps

Implicit timestamp/date construction MUST be disabled.

Example:

~~~yaml
name: 2026-10-01
~~~

At a string grammar position, this lexical value must remain a string.

The plain-value graph MUST NOT contain datetime/date objects.

---

# 42. Allowed plain-value types

After YAML parsing, the object graph MUST contain only:

~~~text
dict
list
str
int
float
bool
None
~~~

Any other Python value type is a parser-policy violation.

---

# 43. Finite numeric policy

Any float that reaches the plain-value boundary MUST be finite.

NaN and Infinity are forbidden.

This aligns declarative parsing with canonical wire security.

---

# 44. Cyclic graph prohibition

The parsed value graph MUST be acyclic.

Because aliases are forbidden, valid declarative input cannot intentionally create cycles.

Implementation code SHOULD nevertheless reject aliases before algorithms assume acyclicity.

---

# 45. No Python object deserialization

The parser MUST NOT support Python-specific object/name/module constructors or equivalent arbitrary-object mechanisms.

Declarative YAML is not a Python serialization format.

---

# 46. No filesystem directives

The grammar has no include/import directive.

Invalid:

~~~yaml
include: ./common.yml
~~~

The parser MUST never recursively open paths referenced by document content.

---

# 47. No remote references

The grammar has no network resource resolution.

Invalid directives include:

~~~yaml
include: https://example.com/schema.yml
~~~

and:

~~~yaml
include: s3://bucket/schema.yml
~~~

Parsing MUST perform zero network calls.

---

# 48. No environment interpolation

The parser MUST NOT resolve environment-variable syntax.

For example, dollar-brace variable text remains ordinary string content and is never looked up in os.environ.

---

# 49. No templating

The parser MUST NOT execute Jinja or any other template engine.

Template-looking text is treated as plain input and validated normally.

---

# 50. No plugin activation

Parsing MUST NOT trigger plugin discovery, entry-point scanning, plugin activation or custom type loading.

Unknown declarative types fail closed with PTK-DECL-005.

---

# 51. No engine imports

Declarative parsing and compilation MUST work without importing:

~~~text
pandas
polars
pyarrow
duckdb
~~~

Import-safety tests SHOULD assert this.

---

# 52. No import-time file I/O

Importing PyTransformKit or the declarative namespace MUST NOT automatically read schema files.

File access occurs only through explicit load helpers.

---

# 53. Explicit path access

load_schema and load_schemas operate only on the exact caller-supplied path.

They MUST NOT search parent directories, discover repository roots, expand globs or auto-read sibling schemas.

---

# 54. Symlink policy

Declarative schema loading does not claim filesystem sandboxing.

If a caller supplies a symlink path, host filesystem semantics MAY resolve it.

Applications requiring a confined root must enforce that separately or through a future explicit resource-loader abstraction.

---

# 55. File-size check ordering

Filesystem helpers SHOULD pre-check file size when reliable metadata is available.

They MUST still enforce the actual byte limit on the loaded content because metadata can race or be inaccurate.

---

# 56. Streaming

Streaming YAML parsing is NOT required in V1.

The 1 MiB default payload bound makes whole-document parsing acceptable.

---

# 57. CPU exhaustion controls

Aliases are forbidden, eliminating the principal YAML expansion mechanism.

Depth and count limits further bound work.

Implementations SHOULD avoid unnecessary repeated full-tree traversals.

---

# 58. Memory exhaustion controls

Default controls are:

~~~text
1 MiB payload
no aliases
one YAML document
64 levels of nesting
256 schemas
10,000 top-level fields per schema
50,000 total field nodes
~~~

These controls are defensive bounds, not an OS-level memory sandbox.

---

# 59. Recursion strategy

Depth validation SHOULD avoid uncontrolled Python recursion where practical.

An iterative stack walk MAY be used.

If recursion is used, the configured maximum MUST stay comfortably below interpreter recursion limits.

---

# 60. Security error mapping

| Failure | Public error |
| --- | --- |
| payload too large | PTK-DECL-013 |
| nesting too deep | PTK-DECL-013 |
| too many schemas | PTK-DECL-013 |
| too many field nodes | PTK-DECL-013 |
| malformed YAML | PTK-DECL-001 |
| custom tag | PTK-DECL-001 |
| anchor | PTK-DECL-001 |
| alias | PTK-DECL-001 |
| merge key | PTK-DECL-001 |
| multiple YAML documents | PTK-DECL-001 |
| duplicate key | PTK-DECL-006 |
| invalid strict scalar for grammar | PTK-DECL-003 / PTK-DECL-005 |
| missing PyYAML | PTK-DECL-010 |

---

# 61. Safe diagnostics

Security failures MUST NOT include the entire source document by default.

Diagnostics MAY include source name, line, column, declarative path, a bounded key/scalar value and the violated rule.

---

# 62. Diagnostic value limit

If a malicious key or scalar is rendered, the renderer SHOULD truncate it.

Recommended display limit:

~~~text
256 Unicode code points
~~~

This is a rendering limit, not a schema-value length contract.

---

# 63. Token preflight

Before construction, PyTransformKit SHOULD scan YAML tokens/events to reject disallowed syntax.

Preflight SHOULD detect at least:

~~~text
AnchorToken
AliasToken
TagToken
multiple document starts/documents
~~~

Merge-key rejection MAY additionally require node/mapping inspection.

---

# 64. Layered defense

Security does not depend on one control.

~~~text
token preflight
      +
safe loader
      +
plain-value audit
      +
depth/count limits
      +
strict decoder
      +
semantic validator
~~~

All remain active.

---

# 65. Resolver customization

PyTransformKit SHOULD use a loader-local scalar resolver table.

It MUST NOT mutate PyYAML global SafeLoader behavior for unrelated application code.

Recommended approach:

~~~text
subclass SafeLoader
copy resolver mappings
modify subclass only
~~~

---

# 66. Constructor isolation

Custom mapping constructors and duplicate-key enforcement MUST be registered only on the PyTransformKit-owned loader subclass.

PyTransformKit MUST NOT monkey-patch process-global YAML behavior.

---

# 67. Emitter security policy

YamlSchemaEmitter MUST emit only plain mappings, sequences and safe scalars.

It MUST NOT emit custom tags, aliases, anchors, Python object constructors or executable expressions.

---

# 68. Emitter alias suppression

If the YAML library attempts to create aliases for repeated object identities, the PyTransformKit emitter MUST suppress them.

Canonical declarative output contains no anchors or aliases.

---

# 69. Emitter scalar safety

Canonical output SHOULD quote strings when necessary to avoid ambiguous re-parsing.

String values lexically resembling booleans, nulls, dates or ambiguous numerics must reload with identical string semantics.

---

# 70. YAML semantic ownership

PyTransformKit declarative semantics are defined by this specification, not by whatever YAML schema/version behavior the underlying library defaults to.

Where PyYAML defaults differ, the PyTransformKit-owned resolver MUST override them.

---

# 71. Parser replacement policy

PyYAML is an adapter choice, not part of the semantic public contract.

A future parser MAY replace it only if it preserves accepted/rejected syntax, scalar semantics, security limits, error categories, deterministic output and diagnostic quality.

---

# 72. Python-version qualification

Before release, CI MUST qualify the selected PyYAML dependency range against:

~~~text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
~~~

The dependency range must be adjusted if the selected minimum does not support the full PyTransformKit matrix.

---

# 73. Supply-chain posture

The YAML dependency SHOULD remain constrained to a compatible major line.

Dependency upgrades MUST pass parser hardening, security, canonical emission and supported-Python tests.

PyTransformKit does not vendor the parser in V1.

---

# 74. Security conformance fixtures

Security fixtures SHOULD include:

~~~text
oversized_document.yml
deeply_nested.yml
too_many_schemas.yml
too_many_fields.yml
duplicate_key.yml
anchor.yml
alias.yml
merge_key.yml
custom_tag.yml
python_object_tag.yml
multi_document.yml
yaml11_yes_no.yml
yaml11_on_off.yml
implicit_date.yml
non_finite_float.yml
invalid_utf8.bin
~~~

---

# 75. Positive parser fixtures

Positive fixtures SHOULD include:

~~~text
basic_schema.yml
multi_schema.yml
unicode_names.yml
quoted_ambiguous_strings.yml
deep_but_allowed.yml
nested_struct_list_map.yml
~~~

---

# 76. Security test — arbitrary object construction

A test MUST prove that Python-object YAML tags do not execute and fail with PTK-DECL-001.

The test MUST use a harmless sentinel and MUST NOT depend on destructive commands.

---

# 77. Security test — no secondary file access

Tests SHOULD deny or monitor file-open operations beyond the explicitly requested top-level path.

Document content MUST NOT trigger secondary reads.

---

# 78. Security test — no network

Parsing tests SHOULD execute with network access denied or monkeypatched.

No declarative input may trigger network calls.

---

# 79. Security test — no environment interpolation

Tests SHOULD verify that environment-variable-looking strings are not substituted and that the parser does not inspect matching environment variables.

---

# 80. Security test — no plugin activation

Unknown type names MUST produce PTK-DECL-005 without plugin discovery or activation.

---

# 81. Security test — duplicate keys

Duplicate-key tests MUST cover root, schema, field, decimal, list, map and nested struct mappings.

All must fail before last-value-wins behavior.

---

# 82. Security test — alias amplification

An alias-amplification payload MUST be rejected at the alias boundary.

The test must not require materializing the expanded malicious graph.

---

# 83. Security test — depth boundary

Tests MUST cover:

~~~text
depth == limit      → parser proceeds if otherwise valid
depth == limit + 1  → PTK-DECL-013
~~~

---

# 84. Security test — payload boundary

Tests MUST cover:

~~~text
bytes == limit      → parser proceeds if otherwise valid
bytes == limit + 1  → PTK-DECL-013
~~~

---

# 85. Security test — scalar ambiguity

Tests MUST verify that yes/no/on/off and ISO-like date strings do not unexpectedly become booleans or date objects.

At string grammar positions they remain strings.

---

# 86. Security test — non-finite values

Inputs attempting to create NaN or infinity MUST fail before canonical Domain construction.

No non-finite float may survive into normalized declarative definitions.

---

# 87. Import-safety test

A test MUST prove that:

~~~python
import pytransformkit
~~~

does not import PyYAML before declarative YAML functionality is invoked.

---

# 88. Optional-extra installation test

CI SHOULD include a job that installs:

~~~text
pip install -e ".[yaml]"
~~~

and runs declarative parser/security tests.

Core jobs without the extra continue to verify import safety.

---

# 89. Parsing limits value object

Internal services MAY use an immutable configuration value.

~~~python
@dataclass(frozen=True, slots=True)
class DeclarativeParsingLimits:
    max_payload_bytes: int = 1_048_576
    max_nesting_depth: int = 64
    max_schemas: int = 256
    max_fields_per_schema: int = 10_000
    max_total_field_nodes: int = 50_000
~~~

Whether this becomes public is deferred to document 38.

---

# 90. Limit configuration

Every configured limit MUST be positive.

Invalid parser configuration is a programmer/configuration error and SHOULD fail immediately when constructing the service.

High-level APIs MUST NOT silently raise limits based on input.

---

# 91. Security logging

PyTransformKit MAY expose parser security failures through diagnostics.

It MUST NOT log entire untrusted documents by default.

Parsing security must remain deterministic without a logging or telemetry backend.

---

# 92. Side-effect model

In-memory parsing is side-effect free.

Filesystem helpers add only the explicitly requested top-level read/write.

Parsing never performs network access, plugin activation, engine execution or runtime transformation.

---

# 93. Fail-closed rule

When parser behavior is ambiguous, the implementation MUST reject rather than guess.

~~~text
unknown tag          → reject
unknown property     → reject
unknown type         → reject
unsupported version  → reject
duplicate key        → reject
excessive depth      → reject
~~~

---

# 94. Compatibility rule

Security restrictions are part of declarative language V1.

Relaxing restrictions such as allowing aliases, includes or custom tags requires explicit threat-model review, compatibility analysis, new security tests and likely a new declarative language version.

---

# 95. Relationship with canonical wire security

Declarative YAML and canonical JSON serialization are distinct contracts but share these principles:

~~~text
closed semantic vocabulary
strict parsing
payload bound
nesting bound
no arbitrary object construction
no code execution
fail-closed unknown values
~~~

Declarative YAML MUST NOT weaken the V1 wire security posture.

---

# 96. Relationship with Domain validation

Parser hardening does not replace Domain validation.

Required chain:

~~~text
secure parse
    ↓
strict decode
    ↓
declarative validation
    ↓
Domain constructors
~~~

---

# 97. Decisions frozen by this document

## DEC-SEC-01

PyYAML is the preferred optional parser for declarative V1.

## DEC-SEC-02

The recommended dependency range is PyYAML >=6,<7, subject to Python-version qualification.

## DEC-SEC-03

Plain safe_load is insufficient; PyTransformKit owns a hardened loader.

## DEC-SEC-04

Core import remains independent of the YAML dependency.

## DEC-SEC-05

Default payload limit is 1 MiB.

## DEC-SEC-06

Default nesting limit is 64.

## DEC-SEC-07

Default schema-count limit is 256.

## DEC-SEC-08

Default top-level field limit is 10,000 per schema.

## DEC-SEC-09

Default total field-node limit is 50,000.

## DEC-SEC-10

Duplicate YAML keys are rejected recursively.

## DEC-SEC-11

Anchors and aliases are forbidden.

## DEC-SEC-12

Merge keys are forbidden.

## DEC-SEC-13

Custom YAML tags are forbidden.

## DEC-SEC-14

Multi-document YAML streams are forbidden.

## DEC-SEC-15

Implicit timestamp/date construction is disabled.

## DEC-SEC-16

YAML yes/no/on/off boolean coercion is disabled.

## DEC-SEC-17

No include, remote resolution, environment interpolation or templating occurs.

## DEC-SEC-18

No plugin discovery or activation occurs during parsing.

## DEC-SEC-19

No engine import is required.

## DEC-SEC-20

Security-limit failures use PTK-DECL-013.

---

# 98. Acceptance criteria

The parsing/security policy is satisfied when:

1. core PyTransformKit imports without PyYAML;
2. YAML functionality fails cleanly when the extra is missing;
3. no unsafe YAML loader is used;
4. arbitrary Python object construction is impossible;
5. duplicate keys fail recursively;
6. anchors fail;
7. aliases fail;
8. merge keys fail;
9. custom tags fail;
10. multi-document streams fail;
11. yes/no/on/off remain strings rather than booleans;
12. implicit dates remain strings;
13. non-finite values fail;
14. payloads above 1 MiB fail by default;
15. nesting above 64 fails by default;
16. schema/field count limits are enforced;
17. parsing performs no network calls;
18. document content triggers no secondary file reads;
19. environment variables are not interpolated;
20. plugins are not activated;
21. engines are not imported;
22. public failures map to PTK-DECL-* errors;
23. security failures do not dump full source;
24. canonical emitted YAML never uses forbidden YAML features;
25. emitted YAML can be safely parsed by the same hardened parser.

---

# 99. Next document

The next document freezes the relationship between declarative YAML and existing canonical serialization:

~~~text
37_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ROUNDTRIP_AND_SERIALIZATION_MODEL.md
~~~

It must define semantic round-trip, YAML versus wire contracts, canonical emission, lossless Domain state, non-preserved comments/formatting, schema-name handling, multi-schema identity, fingerprinting boundaries, version independence and migration boundaries.

---

# 100. Final summary

Declarative YAML is accepted only through a deliberately narrow trust boundary:

~~~text
UNTRUSTED YAML
      ↓
size bound
      ↓
token security preflight
      ↓
PyTransformKit hardened SafeLoader
      ↓
plain-value audit
      ↓
depth/count bounds
      ↓
strict declarative decoder
      ↓
semantic validator
      ↓
canonical Domain
~~~

The parser is intentionally less permissive than general-purpose YAML.

Features that make YAML powerful as a serialization language — tags, aliases, anchors, merges and implicit coercions — are exactly the features PyTransformKit does not need for schema authoring.

> **Declarative schema YAML is a constrained data language, not a general YAML execution or composition environment.**