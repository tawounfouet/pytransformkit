# PyKit Ecosystem V2 — Serialization and Wire Contracts

> **Status:** NORMATIVE SERIALIZATION BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit  
> **Compatibility posture:** schema-driven portable contracts with explicit versioning  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_SHARED_CONTRACTS_AND_REFERENCE_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_EXECUTION_IDENTITY_AND_CORRELATION_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ERROR_FAILURE_RETRY_AND_UNCERTAINTY_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_DATASET_RESOURCE_AND_ARTIFACT_INTEROPERABILITY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_LINEAGE_PROVENANCE_AND_TRACEABILITY_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_OBSERVABILITY_EVENTS_AND_TELEMETRY_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_INTEGRATION_AND_ANTI_CORRUPTION_LAYER_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_DEPENDENCY_PACKAGING_AND_OPTIONAL_EXTRAS_STRATEGY.md

---

# 1. Purpose

This document defines the canonical V2 serialization and wire-contract model for the PyKit ecosystem.

It specifies how portable contracts are represented when they must survive process, host, storage, queue, subprocess, API and historical-version boundaries.

The governing principle is:

> **Persist semantics, not Python object graphs.**

PyKit wire contracts MUST be explicit, schema-driven, versioned, portable and safe to decode without executing arbitrary code.

---

# 2. Scope

This specification applies to durable or transmitted forms of:

~~~text
ResourceReference
ArtifactReference
DatasetReference
DatasetVersionReference

IngestionExecutionReference
TransformationExecutionReference
WorkflowExecutionReference
ExternalRunRef

CorrelationContext
FailureEvidence
RetryDecision
IdempotencyReference

EventEnvelope
Diagnostic
Manifest
LineageRecord
Compatibility metadata
~~~

Not every in-memory domain object is required to be serializable.

---

# 3. Serialization, persistence and materialization

Serialization answers:

> How is a semantic value represented outside the current Python object graph?

Persistence answers:

> Where and for how long is the representation stored?

Materialization answers:

> How is physical data loaded or produced?

These concepts remain distinct.

~~~text
Domain value
    ↓ serialize
Wire contract
    ↓ persist
file / database / queue / API
~~~

is different from:

~~~text
DatasetVersionReference
    ↓ resolve
ResourceReference
    ↓ materialize
physical dataset
~~~

---

# 4. Wire-contract goals

Stable wire contracts SHOULD be:

- explicit about contract identity;
- explicit about contract version;
- deterministic where canonicalization is promised;
- portable across Python processes;
- independent from private module paths;
- safe to parse;
- free from active resources;
- free from raw credentials;
- forward-evolvable;
- backwards-readable according to declared policy;
- testable with golden fixtures.

---

# 5. Non-goals

The wire model does not provide:

- arbitrary Python object serialization;
- universal RPC;
- universal data-file format;
- transparent DataFrame serialization;
- transparent function or lambda serialization;
- automatic support for every historical contract forever;
- implicit reconstruction of private runtime objects.

---

# 6. Canonical baseline encoding

JSON is the canonical baseline interchange format for shared metadata contracts.

This choice favors:

- language neutrality;
- debuggability;
- tooling;
- golden fixtures;
- APIs and queues;
- explicit schema validation.

Alternative encodings MAY exist:

~~~text
MessagePack
CBOR
Avro
Protobuf
database-native representation
~~~

but they MUST preserve the same semantic contract.

---

# 7. JSON is not a performance mandate

JSON defines reference semantics, not mandatory transport performance.

The same EventEnvelope could be:

~~~text
JSON over HTTP
~~~

or:

~~~text
Protobuf over RPC
~~~

without changing EventEnvelope semantics.

Transport encoding belongs to adapters.

---

# 8. Canonical envelope

Stable top-level contracts SHOULD follow a common pattern:

~~~json
{
  "contract": "pykit.dataset_version_reference",
  "contract_version": 1,
  "payload": {
    "...": "..."
  }
}
~~~

The envelope separates:

~~~text
contract identity
contract version
payload
~~~

---

# 9. Contract identifier

The contract field identifies semantic type.

Recommended examples:

~~~text
pykit.resource_reference
pykit.artifact_reference
pykit.dataset_reference
pykit.dataset_version_reference

pykit.correlation_context
pykit.failure_evidence
pykit.external_run_ref

pykit.event
pykit.lineage_record
~~~

Contract IDs are semantic identifiers, not Python module paths.

---

# 10. Contract ID stability

Contract identifiers SHOULD remain stable across package refactors.

Rejected:

~~~text
pytransformkit.internal.runtime.models.SomeReference
~~~

Preferred:

~~~text
pykit.dataset_version_reference
~~~

or a framework-owned semantic namespace when the contract is not shared.

---

# 11. Contract version

contract_version identifies the wire schema version.

It is distinct from:

~~~text
package version
Python version
DatasetVersion
WorkflowDefinition version
TransformationPlan version
EventVersion
~~~

A package release does not automatically increment contract_version.

---

# 12. Contract version numbering

Initial V2 contracts SHOULD use integer major schema versions:

~~~text
1
2
3
~~~

Backward-compatible additive evolution MAY remain within one version when old readers can safely ignore new optional fields.

Incompatible semantic evolution requires a new version.

---

# 13. Breaking changes

A contract version MUST change when semantics cannot safely be read under the old schema.

Examples:

- removing a required field;
- changing required field meaning;
- changing identifier semantics;
- changing timestamp meaning;
- changing ownership semantics;
- narrowing accepted values incompatibly;
- changing uncertainty or idempotency meaning.

---

# 14. Backward-compatible changes

Changes MAY remain compatible when they only:

- add optional fields;
- add optional namespaced metadata;
- clarify documentation without changing meaning;
- add safely ignorable descriptive evidence.

Compatibility still requires tests.

---

# 15. Unknown optional fields

Readers SHOULD tolerate unknown optional fields when the contract version is supported.

This enables additive forward evolution.

Unknown fields MUST NOT override known required semantics.

---

# 16. Missing required fields

Missing required fields make the payload invalid.

Readers MUST fail explicitly.

Defaults MUST NOT be guessed for fields affecting:

- identity;
- ownership;
- retryability;
- uncertainty;
- idempotency;
- security;
- contract kind.

---

# 17. Unknown contract identifiers

Unknown contract identifiers require explicit policy:

~~~text
REJECT
STORE_OPAQUELY
FORWARD_OPAQUELY
IGNORE_IF_OPTIONAL
~~~

A decoder MUST NOT import or instantiate arbitrary Python classes based on contract text.

---

# 18. Unsupported contract versions

Known contract plus unsupported version must produce an explicit compatibility error.

~~~text
UNSUPPORTED_CONTRACT_VERSION
~~~

A v2 payload MUST NOT silently be interpreted as v1.

---

# 19. Canonical JSON

When deterministic bytes are promised, canonical JSON rules MUST define:

- UTF-8;
- key ordering;
- whitespace;
- Unicode normalization;
- null handling;
- array ordering semantics;
- number representation;
- timestamp normalization;
- binary encoding conventions.

Canonicalization must be frozen before public hashing or signing.

---

# 20. UTF-8 and Unicode

Portable JSON MUST use UTF-8.

Where canonical fingerprints depend on text normalization, the baseline SHOULD use Unicode NFC unless a specific contract defines otherwise.

---

# 21. Object key ordering

JSON object order is not semantic.

Canonical serialization SHOULD use deterministic key ordering.

Cross-language fingerprint contracts must freeze the exact ordering rule.

---

# 22. Collection ordering

List order is semantic unless explicitly declared otherwise.

If a collection is semantically unordered, canonicalization SHOULD sort by a documented stable key before hashing.

The contract must distinguish:

~~~text
ordered list
unordered set
keyed map
multiset
~~~

---

# 23. Null versus absent

Contracts SHOULD distinguish:

~~~text
field absent
field present with null
~~~

Recommended rule:

- absent means unspecified or not applicable;
- null is used only when explicit absence is itself meaningful.

Avoid gratuitous null fields in canonical payloads.

---

# 24. Boolean values

Booleans serialize as JSON booleans.

Do not use:

~~~text
"true"
"false"
0
1
~~~

as equivalent values unless an external compatibility adapter explicitly requires coercion.

---

# 25. Numeric values

Integers use JSON numbers when their range is interoperable.

Opaque identifiers SHOULD generally serialize as strings even when internally numeric.

Large integers that may exceed safe consumer precision SHOULD serialize as decimal strings or explicit typed values.

---

# 26. Floating-point values

Special values such as:

~~~text
NaN
Infinity
-Infinity
~~~

are not standard JSON numbers.

Contracts MUST either reject them or define an explicit safe representation.

Precision-sensitive values SHOULD avoid binary floating point.

---

# 27. Decimal values

Decimal values SHOULD serialize as exact decimal strings or another explicit lossless representation.

Conceptually:

~~~json
{
  "type": "decimal",
  "value": "123.4500"
}
~~~

Scale meaning must be documented when significant.

---

# 28. Dates and timestamps

Dates use ISO 8601 calendar form:

~~~text
2026-09-28
~~~

Durable timestamps use timezone-aware RFC 3339 / ISO 8601 forms.

Preferred UTC example:

~~~text
2026-09-28T17:24:00Z
~~~

Naive timestamps are prohibited in durable cross-framework contracts.

---

# 29. Timestamp precision

Contracts SHOULD cap timestamp precision to a portable level.

Microsecond precision is a suitable default unless a contract requires less.

Excess precision that cannot round-trip through supported stores SHOULD be avoided.

---

# 30. Durations

Durations require explicit units.

Preferred field names may encode the unit:

~~~text
timeout_ms
delay_seconds
~~~

or use a structured value.

Unitless durations are discouraged.

---

# 31. Identifiers

UUID, ULID and similar identifiers SHOULD serialize as canonical strings.

Consumers treat them as opaque unless structure is part of the contract.

---

# 32. Enums

Enums SHOULD serialize as stable strings.

Examples:

~~~text
SUCCEEDED
FAILED
UNKNOWN_OUTCOME
REQUIRES_RECONCILIATION
~~~

Ordinal integers are discouraged because they hide meaning and complicate evolution.

---

# 33. Unknown enum values

Each enum family SHOULD define one of:

~~~text
REJECT_UNKNOWN
PRESERVE_UNKNOWN
MAP_TO_UNKNOWN
~~~

Safety-critical enums should generally fail closed.

Descriptive extensible enums may preserve unknown values.

---

# 34. Binary values

Raw binary payloads SHOULD NOT be embedded in ordinary metadata contracts.

Small binary values, when unavoidable, use a documented encoding such as Base64.

Large bytes belong in Resources or Artifacts and cross boundaries by reference.

---

# 35. Large payload rule

The following MUST remain metadata-sized:

~~~text
CorrelationContext
ExternalRunRef
FailureEvidence
EventEnvelope
Workflow metadata
LineageRecord
~~~

Large datasets, files or logs belong behind references.

---

# 36. Metadata maps

Extension metadata MAY use JSON object maps.

Metadata must remain:

- bounded;
- non-secret;
- supplementary;
- serializable.

Required semantics MUST NOT be tunneled through arbitrary metadata.

---

# 37. Metadata namespaces

Cross-framework extension keys SHOULD be namespaced when collision is possible.

Examples:

~~~text
pyingestkit.source_etag
pytransformkit.plan_fingerprint
pyworkflowkit.task_attempt_id
company.cost_center
~~~

---

# 38. Python implementation independence

In-memory contracts MAY use:

- frozen dataclasses;
- attrs;
- Pydantic;
- TypedDict;
- custom immutable objects.

Wire compatibility depends on serialized semantics, not on the Python model library.

---

# 39. No pickle as public wire format

Pickle, cloudpickle, dill and similar arbitrary object serializers MUST NOT be canonical cross-framework or durable formats.

Reasons include:

- code-execution risk;
- Python-version coupling;
- module-path coupling;
- private implementation coupling;
- weak cross-language interoperability.

---

# 40. No module-path reconstruction

Rejected:

~~~json
{
  "class": "pytransformkit.internal.foo.Bar",
  "args": []
}
~~~

Readers MUST NOT import arbitrary classes named in untrusted payloads.

Decoding is schema-driven.

---

# 41. No arbitrary function serialization

Functions, closures and lambdas are not portable contract values by default.

If callable references are ever supported, they require a separate stable plugin/function-reference contract.

Raw executable code blobs are prohibited.

---

# 42. Expression serialization

PyTransformKit MAY define portable serialization for its expression AST.

A stable expression IR MUST:

- version node semantics;
- identify node kinds explicitly;
- serialize literals safely;
- preserve logical types;
- avoid executable code;
- support deterministic canonicalization when fingerprinted.

---

# 43. LogicalPlan serialization

LogicalPlan MAY have a portable IR.

A stable LogicalPlan wire form SHOULD carry:

~~~text
IR contract ID
IR version
logical nodes
expression nodes
logical schemas
input identities
semantic options
fingerprint
~~~

It MUST NOT embed native engine handles.

---

# 44. PhysicalPlan serialization

PhysicalPlan may contain engine-specific details.

If serialized, it MUST declare:

~~~text
engine identity
engine compatibility assumptions
physical-plan contract version
portability scope
~~~

A serialized physical plan is not automatically replayable on another engine or version.

---

# 45. Definition serialization

IngestionDefinition, TransformationPlan and WorkflowDefinition MAY be portable only if their semantics can be represented without arbitrary executable Python state.

If callbacks, closures or opaque plugin objects prevent safe serialization, the API MUST report limited/non-portable serialization rather than pretending otherwise.

---

# 46. Reference contracts

Reference wire contracts deserve especially strong stability because they connect frameworks.

Priority contracts include:

~~~text
ResourceReference
ArtifactReference
DatasetVersionReference
ExecutionReference
ExternalRunRef
CorrelationContext
~~~

Provider-specific details should remain namespaced or nested when possible.

---

# 47. ResourceReference example

Conceptual form:

~~~json
{
  "contract": "pykit.resource_reference",
  "contract_version": 1,
  "payload": {
    "namespace": "pyingestkit.resource",
    "resource_id": "res_01J...",
    "locator": "s3://bucket/path/file.parquet",
    "format": "PARQUET",
    "media_type": "application/vnd.apache.parquet",
    "checksum": {
      "algorithm": "sha256",
      "value": "..."
    }
  }
}
~~~

Credentials are prohibited.

---

# 48. DatasetVersionReference example

Conceptual form:

~~~json
{
  "contract": "pykit.dataset_version_reference",
  "contract_version": 1,
  "payload": {
    "owner": "pyingestkit",
    "dataset_id": "customers",
    "version_id": "52",
    "schema_fingerprint": "sha256:...",
    "content_fingerprint": "sha256:..."
  }
}
~~~

A resource representation may be nested or separately referenced according to the final schema.

---

# 49. CorrelationContext example

~~~json
{
  "contract": "pykit.correlation_context",
  "contract_version": 1,
  "payload": {
    "correlation_id": "C-42",
    "causation_id": "TA-3",
    "workflow_run_id": "W-42",
    "task_run_id": "TR-17",
    "task_attempt_id": "TA-3",
    "transformation_execution_id": "T-913"
  }
}
~~~

Only relevant optional IDs need to be emitted.

---

# 50. ExternalRunRef example

~~~json
{
  "contract": "pykit.external_run_ref",
  "contract_version": 1,
  "payload": {
    "provider": "pytransformkit",
    "external_run_id": "T-913",
    "kind": "transformation_execution"
  }
}
~~~

Provider metadata remains optional and credential-safe.

---

# 51. FailureEvidence example

~~~json
{
  "contract": "pykit.failure_evidence",
  "contract_version": 1,
  "payload": {
    "source_framework": "pytransformkit",
    "error_code": "TRANSFORM_ENGINE_TIMEOUT",
    "category": "TIMEOUT",
    "retryability": "RETRYABLE_AFTER_RECONCILIATION",
    "uncertainty": "SIDE_EFFECT_MAY_HAVE_OCCURRED",
    "correlation_id": "C-42",
    "message_summary": "Engine response timed out"
  }
}
~~~

Raw exception objects are never part of the durable contract.

---

# 52. Event example

~~~json
{
  "contract": "pykit.event",
  "contract_version": 1,
  "payload": {
    "event_id": "E-100",
    "event_type": "pyworkflowkit.task_attempt.failed",
    "event_version": 1,
    "occurred_at": "2026-09-28T17:24:00Z",
    "source_framework": "pyworkflowkit",
    "correlation_id": "C-42",
    "task_attempt_id": "TA-3",
    "data": {}
  }
}
~~~

Generic envelope and event-specific payload evolution must remain explicit.

---

# 53. Nested contracts

A contract MAY include another public contract.

Two acceptable patterns are:

~~~text
fully enveloped nested contract
typed nested payload whose type is fixed by parent schema
~~~

Untyped arbitrary nested dictionaries are discouraged for normative semantics.

---

# 54. Recursion limits

Wire contracts SHOULD avoid recursive object cycles.

Readers SHOULD enforce reasonable nesting limits.

Graphs should use explicit:

~~~text
nodes
edges
references
~~~

rather than recursively embedding the same objects.

---

# 55. Payload size limits

Remote, queue and untrusted readers SHOULD enforce maximum payload sizes.

Oversized metadata should move into an Artifact and be referenced.

The wire layer is not a generic blob transport.

---

# 56. Canonical fingerprints

Stable fingerprints follow:

~~~text
semantic payload
    ↓ normalize
canonical bytes
    ↓ hash
fingerprint
~~~

Fingerprint specifications MUST define:

- included fields;
- excluded fields;
- canonicalization version;
- hash algorithm;
- semantic scope.

---

# 57. Fingerprint qualification

Fingerprints SHOULD identify algorithm:

~~~text
sha256:abcdef...
~~~

Different semantic scopes require different field names:

~~~text
schema_fingerprint
content_fingerprint
plan_fingerprint
contract_fingerprint
artifact_checksum
~~~

---

# 58. Canonicalization evolution

Canonicalization rules are themselves compatibility-sensitive.

If canonicalization changes incompatibly, fingerprint semantics change.

A stable public fingerprint MUST NOT silently change implementation.

---

# 59. Signing

Deployments MAY sign contracts.

Signatures SHOULD cover canonical bytes and identify:

~~~text
signature algorithm
key identifier
canonicalization version
contract fingerprint
~~~

Private keys remain outside the payload.

Signing does not replace semantic validation.

---

# 60. Encryption

Encryption is normally transport/storage infrastructure.

The semantic contract remains conceptually independent from one encryption provider.

Encryption at rest or in transit does not change contract_version.

---

# 61. Compression

Compression is representation/transport metadata.

Compressing JSON with gzip or zstd does not alter contract semantics.

---

# 62. Serialization APIs

Frameworks MAY expose:

~~~text
to_dict
from_dict
to_json
from_json
serialize
deserialize
~~~

but API naming should remain consistent within each package.

Conversion, encoding and persistence should remain conceptually distinct.

---

# 63. Serialization must be side-effect free

Pure serialization/deserialization MUST NOT:

- access networks;
- resolve credentials;
- open provider sessions;
- resolve ResourceReference;
- materialize datasets;
- activate plugins implicitly.

---

# 64. Codec versus store

A useful separation is:

~~~text
ContractCodec
    encode
    decode

ContractStore
    put
    get
~~~

A persistence adapter may combine them internally, but the semantic distinction remains.

---

# 65. Decode validation pipeline

Canonical decoding is:

~~~text
parse bytes
    ↓
validate envelope
    ↓
identify contract
    ↓
validate contract version
    ↓
validate payload schema
    ↓
migrate if needed
    ↓
construct public DTO/value
    ↓
semantic validation
~~~

Domain execution starts only after this pipeline succeeds.

---

# 66. Structural validation

Structural validation checks:

~~~text
required fields
field types
array/object shape
enum syntax
timestamp syntax
nested contract shape
~~~

---

# 67. Semantic validation

Semantic validation checks:

~~~text
owner matches contract
namespace is allowed
identity is non-empty
forbidden secret field absent
cross-field invariants hold
uncertainty/retry fields are compatible
~~~

Structural correctness alone is insufficient.

---

# 68. Wire error taxonomy

Recommended categories include:

~~~text
WIRE_PARSE_ERROR
UNKNOWN_CONTRACT
UNSUPPORTED_CONTRACT_VERSION
MISSING_REQUIRED_FIELD
INVALID_FIELD_TYPE
INVALID_ENUM_VALUE
INVALID_TIMESTAMP
SEMANTIC_CONTRACT_VIOLATION
PAYLOAD_TOO_LARGE
NESTING_LIMIT_EXCEEDED
DUPLICATE_KEY
~~~

They map into the owning package error hierarchy.

---

# 69. Safe parser rules

Wire readers MUST NOT:

- call eval;
- unpickle untrusted input;
- import classes named by payload;
- execute code embedded in fields;
- activate unknown plugins based on payload alone.

---

# 70. Contract registry

A runtime MAY maintain an explicit registry:

~~~text
contract ID
    → supported versions
    → validator
    → decoder
    → encoder
~~~

Registration must be explicit.

Unknown contracts follow declared policy.

---

# 71. External schema registry

A deployment MAY use an external schema registry.

Core PyKit decoding MUST NOT require network access to such a registry.

Schemas needed for ordinary supported contracts should be available locally.

---

# 72. JSON Schema

Stable contracts MAY publish JSON Schema.

Benefits include:

- language-neutral validation;
- documentation;
- fixture validation;
- API integration.

JSON Schema does not replace semantic invariants that cannot be expressed structurally.

---

# 73. Schema layout

A repository MAY use:

~~~text
schemas/
  pykit.dataset_version_reference/
    v1.schema.json
  pykit.correlation_context/
    v1.schema.json
~~~

Exact paths are implementation details, but schema identity/version must be stable.

---

# 74. Generated schemas

If schemas are generated from Python models, CI MUST detect drift between:

- model;
- generated schema;
- fixtures;
- documentation.

Generation must be reproducible.

---

# 75. Historical schema retention

Supported historical contract schemas SHOULD remain available as long as readers promise support.

Writer migration does not justify deleting old reader schemas.

---

# 76. Reader and writer versions

A runtime MAY support:

~~~text
read: v1, v2
write: v2
~~~

This is normal.

Read support and write support do not need to be symmetrical.

---

# 77. Upgrade on read

Older contracts MAY decode through deterministic migration:

~~~text
wire v1
    ↓
v1 DTO
    ↓ migrate
current DTO
~~~

The original persisted payload need not be rewritten.

---

# 78. Migration functions

Migrations SHOULD be:

- version-specific;
- deterministic;
- explicit;
- tested;
- side-effect free where possible.

Preferred:

~~~text
v1 → v2
v2 → v3
~~~

Avoid opaque migrate_anything behavior.

---

# 79. Migration chaining

Readers MAY migrate sequentially:

~~~text
v1 → v2 → v3
~~~

Direct shortcuts are optional.

Both paths must produce equivalent current semantics if both exist.

---

# 80. Lossy migration

Lossy migration MUST be explicit.

Critical semantics MUST never be silently discarded.

Examples that must not disappear silently:

~~~text
uncertainty
idempotency scope
ownership
execution identity
security-sensitive meaning
~~~

---

# 81. Contract deprecation

Deprecated contract versions SHOULD document:

- replacement version;
- last writer support;
- reader support horizon;
- migration path.

Removal of historical reader support is an explicit compatibility decision.

---

# 82. Manifest serialization

Execution manifests SHOULD use explicit contract IDs and versions.

A manifest may reference subcontracts instead of embedding all details.

It MUST remain bounded, portable and secret-safe.

---

# 83. Lineage serialization

Portable lineage SHOULD use explicit records such as:

~~~text
LineageRecord
    subject_reference
    relationship
    object_reference
    confidence
    execution_reference?
    correlation_id?
    metadata?
~~~

Lineage records remain domain-owner-aware.

---

# 84. Event serialization

Events use:

~~~text
common event envelope
+
event-specific payload
~~~

EventType/EventVersion evolution remains explicit.

Telemetry delivery encoding does not redefine event semantics.

---

# 85. Failure serialization

FailureEvidence SHOULD carry structured safe evidence:

~~~text
error code
failure category
retryability
uncertainty
provider code
provider execution ID
safe message summary
~~~

Raw provider exception objects are not durable wire values.

---

# 86. Traceback persistence

Tracebacks are diagnostic artifacts, not stable contracts.

If persisted:

- redact sensitive values;
- apply retention;
- do not include them in identity fingerprints;
- do not parse them for machine decisions.

---

# 87. CorrelationContext remains small

CorrelationContext MUST NOT become a generic metadata bag.

It carries correlation/causation/execution identifiers only.

Large diagnostic information belongs elsewhere.

---

# 88. IdempotencyReference serialization

A portable idempotency reference preserves:

~~~text
namespace
key
scope
owner
~~~

The key may itself be sensitive.

Its scope MUST remain explicit.

---

# 89. SecretReference serialization

CredentialReference or SecretReference may serialize only the identifier needed for runtime secret resolution.

The actual secret value MUST NOT be serialized.

---

# 90. URI safety

Long-lived contracts SHOULD prefer credential-free resource locators.

Serializers or validators SHOULD reject or redact:

~~~text
user:password URLs
signed query tokens
presigned URLs
SAS tokens
~~~

according to policy.

---

# 91. Semantic equality and byte equality

Distinguish:

~~~text
semantic equality
canonical byte equality
raw byte equality
~~~

Equivalent JSON documents may differ in whitespace/key order.

Fingerprints use canonical bytes, not arbitrary producer formatting.

---

# 92. Round-trip guarantee

Stable DTOs SHOULD satisfy:

~~~text
value
    ↓ encode
wire
    ↓ decode
semantically equivalent value
~~~

Python object identity is irrelevant.

---

# 93. Golden fixtures

Every stable contract SHOULD have fixtures covering:

- minimal valid form;
- fully populated form;
- unknown optional field;
- missing required field;
- unsupported version;
- invalid enum/timestamp;
- redaction;
- migration where applicable.

---

# 94. Property-based testing

Property-based tests MAY supplement fixtures for:

- round-trip behavior;
- Unicode;
- nested optionals;
- size limits;
- ordering;
- invalid combinations.

Golden fixtures remain the compatibility anchor.

---

# 95. Cross-language fixtures

If non-Python implementations appear, the same serialized fixtures SHOULD be used to verify interoperability.

Portable contracts must not depend on Python-only behavior.

---

# 96. Fuzz testing

Untrusted parsers SHOULD be candidates for fuzz tests, especially:

- envelope parsing;
- schema validation;
- migration;
- URI handling;
- nested contract decoding.

---

# 97. Safety limits

Readers SHOULD support bounded limits such as:

~~~text
maximum bytes
maximum nesting depth
maximum array length
maximum metadata keys
maximum string length
~~~

Syntactically valid but excessive payloads should fail cleanly.

---

# 98. Database storage

A database MAY persist contracts as:

- normalized columns;
- JSON/JSONB;
- binary encoding;
- hybrid structures.

Private database layout does not need to equal the public wire schema.

Semantic compatibility remains required.

---

# 99. Database migration is separate

Database schema migration and wire-contract migration are different concerns.

A new database schema may still store historical v1 wire payloads.

Do not conflate database version with contract_version.

---

# 100. Queue messages

Queue transport SHOULD preserve:

~~~text
message_id
contract ID
contract version
correlation_id
causation_id
payload or reference
~~~

Queue delivery metadata is transport-level, not domain-level.

---

# 101. HTTP transport

HTTP APIs SHOULD:

- validate media type;
- validate contract/version;
- enforce payload limits;
- preserve correlation;
- redact responses;
- return explicit compatibility errors.

HTTP status codes do not replace FailureEvidence.

---

# 102. Subprocess transport

Subprocess integrations SHOULD prefer:

~~~text
stdin JSON
stdout JSON
manifest file
small environment context
~~~

over pickled object transfer.

---

# 103. File-based contracts

JSON contract files SHOULD:

- use UTF-8;
- contain contract ID/version internally;
- use atomic write strategy where corruption matters;
- optionally carry checksums.

Filename alone is not contract identity.

---

# 104. Atomic file writes

For important manifests/state snapshots, preferred strategy is:

~~~text
write temporary
    ↓
flush/fsync if required
    ↓
atomic rename/replace
~~~

Exact guarantees depend on the filesystem.

---

# 105. Parser strictness

Strict wire validation SHOULD reject ambiguous coercions.

Examples:

~~~text
"5" as integer
"false" as boolean
01/02/03 as date
unknown casing for safety enum
~~~

unless the contract explicitly permits normalization.

Predictability is preferred over magical coercion.

---

# 106. Duplicate JSON keys

Readers MUST reject duplicate object keys when parser behavior could otherwise create ambiguity.

A payload with two contract_version keys is invalid.

---

# 107. Graph serialization

Graphs SHOULD serialize with explicit:

~~~text
nodes
edges
stable node IDs
~~~

rather than recursive nested objects.

This applies to:

- transformation graphs;
- workflow graphs;
- lineage projections.

---

# 108. Graph canonicalization

Public graph fingerprints require ordering independent from incidental insertion order.

Canonicalization SHOULD use stable node IDs and deterministic edge ordering.

The exact algorithm must be frozen before exposure.

---

# 109. Defaults

Readers MAY apply a default only when the contract defines that default normatively.

Changing application defaults over time MUST NOT retroactively reinterpret historical payloads.

---

# 110. Missing contract_version

Missing contract_version is invalid for stable V2 contracts.

V2 never assumes version 1 implicitly.

---

# 111. Legacy unversioned payloads

Pre-V2 unversioned data MAY be handled by a dedicated legacy migration reader.

Legacy support remains outside the normative V2 writer path.

All V2 writers emit explicit contract identity and version.

---

# 112. Wire compatibility is public API

Changing stable wire semantics is a public compatibility change even if Python method signatures remain unchanged.

Release policy must treat contract changes accordingly.

---

# 113. Release gates for wire changes

A release changing a stable contract SHOULD verify:

~~~text
schema diff
golden fixture diff
reader compatibility
writer compatibility
migration tests
cross-framework integration tests
documentation
release notes
~~~

Silent wire drift is prohibited.

---

# 114. Schema diffing

CI MAY detect structural breaking changes automatically:

- field removal;
- newly required field;
- type change;
- nullability change;
- enum narrowing.

Semantic review remains necessary.

---

# 115. Canonical byte fixtures

Contracts promising deterministic canonical bytes SHOULD store exact byte fixtures.

Contracts promising only semantic JSON compatibility need structural fixtures, not formatting freeze.

---

# 116. Security classification

Wire fields MAY have classifications such as:

~~~text
PUBLIC
INTERNAL
SENSITIVE
SECRET
~~~

Canonical shared contracts SHOULD avoid SECRET fields entirely.

Serializers/exporters may use classifications for redaction.

---

# 117. Authorization is separate

Successfully decoding a ResourceReference does not authorize resource access.

Serialization communicates identity and semantics.

Runtime authorization remains separate.

---

# 118. Trust boundary

Every deserialization point is a trust boundary.

Payloads may be:

- malformed;
- stale;
- oversized;
- malicious;
- inconsistent;
- unauthorized.

Validation MUST happen before domain use.

---

# 119. Fail closed for safety semantics

If a reader cannot interpret semantics affecting:

- retry safety;
- uncertainty;
- ownership;
- identity;
- credentials;
- authorization context;
- idempotency;

it MUST fail closed.

---

# 120. Opaque forwarding

Infrastructure MAY forward unknown contracts without decoding them if:

- size is bounded;
- no code is executed;
- envelope integrity is preserved;
- transport policy allows it.

Examples include archives and queue relays.

---

# 121. Producer metadata

A contract MAY include diagnostic producer metadata such as:

~~~text
producer_framework
producer_package_version
created_at
~~~

These fields aid support.

They MUST NOT replace contract_version.

---

# 122. Compatibility matrix

Integrations SHOULD eventually declare:

~~~text
supported contract IDs
supported read versions
preferred write version
migrations available
supported package range
~~~

This becomes part of release conformance.

---

# 123. Reader/writer asymmetry

Supporting:

~~~text
read v1, v2
write v2
~~~

is expected.

Historical read support can outlive old writer support.

---

# 124. Downgrade behavior

Writing an older version is allowed only when current semantics fit safely.

If downgrade would lose required safety or identity information, it MUST fail.

---

# 125. Historical replay

Replay guarantees depend on historical contract readability.

A framework must not promise indefinite replay if it removes required old readers.

Support windows should be explicit.

---

# 126. Archived contracts

Long-lived archives SHOULD retain:

~~~text
contract payload
contract ID
contract version
checksum
producer metadata
~~~

Applications with strict compliance may additionally archive schemas.

---

# 127. Contract integrity versus semantic validity

Checksum verifies stored bytes.

Schema/domain validation verifies semantic correctness.

Both may be needed.

One does not replace the other.

---

# 128. Plugin contracts

Plugins MAY define namespaced wire contracts.

A payload MUST NOT auto-install or auto-activate a plugin.

A plugin decoder may run only when the plugin is already installed, trusted, compatible and explicitly activated.

---

# 129. CLI JSON

Machine-readable CLI output intended for automation SHOULD use versioned schemas.

Human-readable CLI text is not a stable contract unless explicitly declared so.

---

# 130. Notebook display

Notebook rendering is presentation.

HTML or rich display may be generated from public DTOs but is not the durable wire format.

---

# 131. Remote API wrappers

HTTP/RPC services MAY wrap PyKit contracts in protocol-specific envelopes.

The embedded PyKit contract identity and version must remain recoverable.

Transport wrappers MUST NOT silently redefine semantics.

---

# 132. Compatibility errors

Unsupported contracts SHOULD expose machine-readable evidence such as:

~~~text
requested contract ID
requested version
supported versions
~~~

without leaking sensitive implementation details.

---

# 133. Reference-application fixtures

The ecosystem reference application SHOULD generate examples for:

~~~text
IngestionResult
DatasetVersionReference
TransformationExecutionReference
ExternalRunRef
CorrelationContext
FailureEvidence
EventEnvelope
Manifest
LineageRecord
~~~

These become living integration fixtures.

---

# 134. Cross-framework conformance

Required scenarios include:

~~~text
PyIngestKit DatasetVersionReference
    → serialize
    → PyTransformKit decode
    → InputBinding

PyTransformKit TransformationExecutionReference
    → serialize
    → PyWorkflowKit decode
    → ExternalRunRef

CorrelationContext
    → workflow
    → ingestion/transformation
    → round-trip

FailureEvidence with UNKNOWN_OUTCOME
    → survives every adapter unchanged semantically
~~~

---

# 135. Corruption tests

Test suites SHOULD include:

- truncated JSON;
- invalid UTF-8;
- duplicate keys;
- unsupported contract;
- unsupported version;
- invalid enum;
- naive/invalid timestamp;
- oversized metadata;
- forbidden credential field;
- invalid nested contract.

---

# 136. Migration tests

For every supported migration:

~~~text
old fixture
    ↓ decode
old DTO
    ↓ migrate
current DTO
    ↓ validate
expected semantic value
~~~

The migration must be deterministic.

---

# 137. Canonicalization tests

Fingerprint contracts SHOULD test that:

- key order does not affect fingerprint;
- insignificant whitespace does not affect fingerprint;
- semantic field changes do affect fingerprint;
- unordered collections canonicalize deterministically;
- timestamp normalization is consistent.

---

# 138. Acceptance criteria

This specification is implemented correctly when:

1. stable portable contracts declare explicit contract ID;
2. stable portable contracts declare explicit contract version;
3. JSON is the canonical baseline representation;
4. unsupported versions fail explicitly;
5. unknown optional fields are tolerated where allowed;
6. missing required fields fail explicitly;
7. timestamps are timezone-aware;
8. raw credentials are never ordinary contract fields;
9. large data crosses boundaries by reference;
10. pickle is not a public durable interchange format;
11. canonicalization is frozen before public fingerprinting;
12. fingerprints declare algorithm and semantic scope;
13. parsing never executes arbitrary code;
14. readers enforce payload limits;
15. schema validation precedes domain use;
16. migrations are explicit and tested;
17. reader and writer version support may differ;
18. golden fixtures exist for stable contracts;
19. real serialized fixtures are tested cross-framework;
20. package version and contract version evolve independently.

---

# 139. Normative invariants

### WIRE-INV-01 — Persist semantics, not Python object graphs

Durable contracts are schema-driven.

### WIRE-INV-02 — Contract identity is explicit

Stable payloads always identify semantic type.

### WIRE-INV-03 — Contract version is explicit

No stable V2 payload relies on an implicit version.

### WIRE-INV-04 — Package version is not wire version

The two evolve independently.

### WIRE-INV-05 — Unknown required semantics fail closed

Readers do not guess safety-sensitive meaning.

### WIRE-INV-06 — Portable contracts contain no active resources

Sessions, connections and engine handles remain runtime-local.

### WIRE-INV-07 — Credentials are referenced, not serialized

Secret material stays outside ordinary contracts.

### WIRE-INV-08 — Large payloads move by reference

Metadata contracts remain bounded.

### WIRE-INV-09 — Canonicalization precedes stable hashing

Arbitrary serializer formatting is not fingerprint semantics.

### WIRE-INV-10 — Migrations are explicit

Historical payloads are never silently reinterpreted.

### WIRE-INV-11 — Parsing is non-executable

Wire payloads cannot select arbitrary code to run.

### WIRE-INV-12 — Golden fixtures protect interoperability

Stable contracts are tested as serialized artifacts.

---

# 140. Canonical serialization flow

~~~text
Public DTO / Reference
        ↓
Semantic validation
        ↓
Contract envelope
        ↓
Canonical encoding
        ↓
Optional fingerprint/signature
        ↓
Transport or persistence
        ↓
Parse
        ↓
Envelope validation
        ↓
Contract-version validation
        ↓
Payload schema validation
        ↓
Migration if required
        ↓
Current public DTO
        ↓
Semantic validation
        ↓
Consumer anti-corruption layer
~~~

At no point does decoding require reconstruction of arbitrary private Python objects.

---

# 141. Final architecture statement

The PyKit V2 wire model exists so that a contract can outlive:

~~~text
one function call
one Python process
one worker
one host
one package minor version
one runtime implementation
~~~

without becoming detached from its meaning.

The canonical model is:

~~~text
semantic contract
    ↓
explicit contract ID
    ↓
explicit contract version
    ↓
strict portable payload
    ↓
safe deterministic serialization
    ↓
tested compatibility and migration
~~~

The central rule is:

> **If a value must cross time, process, host or framework boundaries, its semantics must be explicit on the wire.**

This specification is the baseline for:

~~~text
PYKIT_ECOSYSTEM_V2_ARCHITECTURE_CONFORMANCE_AND_TEST_STRATEGY.md
PYKIT_ECOSYSTEM_V2_SECURITY_AND_TRUST_BOUNDARIES.md
PYKIT_ECOSYSTEM_V2_REFERENCE_APPLICATION_SPEC.md
PYKIT_ECOSYSTEM_V2_RELEASE_COMPATIBILITY_AND_VERSIONING_POLICY.md
PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md
~~~
