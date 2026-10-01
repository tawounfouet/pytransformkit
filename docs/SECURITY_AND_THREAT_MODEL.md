# PyTransformKit V1 Security and Threat Model

> Freeze baseline: LOT-26 / `0.8.0`  
> Applies to the V1 architecture and public API.

PyTransformKit is an in-process transformation framework. It reduces risk at its
logical, serialization, plugin, resource and observability boundaries, but it is
not a sandbox for arbitrary Python code.

## Assets

Security-relevant assets include:

- transformation declarations and LogicalPlans;
- resource locators and credential references;
- native engine handles;
- local files resolved by Reader/Writer implementations;
- serialized wire contracts;
- plugin code and plugin metadata;
- diagnostics, lineage and telemetry;
- execution/correlation identifiers.

Raw credentials and governed DatasetVersion state are intentionally outside the
logical transformation model.

## Trust boundaries

### Core logical model

Dataset, Schema, Expression, TransformationPlan and LogicalPlan are trusted local
Python values after constructor validation. They do not perform physical I/O during
construction.

### Wire boundary

Serialized payloads may be untrusted. Decoding is fail-closed through explicit
contract IDs, versions, payload/depth limits and a closed semantic type registry.

Arbitrary Python object reconstruction is not supported.

### Resource boundary

ResourceReference is portable location metadata, not an authorization token.
CredentialReference contains identifiers, not secret values.

The local filesystem resolver confines file access to an explicitly configured root.

### Engine boundary

Engine adapters execute native code and may allocate memory, open engine-owned
resources or call providers in future integrations. Engine selection is explicit and
capability-gated.

### Plugin boundary

In-process plugins are trusted Python code once activated. They are not sandboxed.

Discovery is metadata inspection only; activation is explicit. Untrusted wire payloads
cannot cause plugin activation.

### Telemetry boundary

Telemetry is best-effort and redacted before leaving runtime. Sensitive-key patterns
and high-cardinality identifiers are restricted by the observability model.

## Threats and controls

### Arbitrary code execution through deserialization

Threat:
a malicious payload attempts to reconstruct callables, classes or executable objects.

Controls:

- no pickle/cloudpickle/dill durable fallback;
- closed SemanticTypeRegistry;
- explicit tagged dataclass/enum representation;
- callbacks/callables rejected as non-portable;
- unknown semantic type IDs rejected;
- future unsupported contract versions fail closed.

Residual risk:
a bug in a registered safe semantic constructor could still be triggered by malformed
data. Constructor validation and negative tests reduce this risk.

### Resource path traversal

Threat:
a file ResourceReference escapes the configured local root.

Controls:

- LocalFilePathResolver resolves against configured root;
- resolved path must remain beneath that root;
- traversal raises ResourcePathViolationError.

Residual risk:
filesystem permissions, symlink policy and host isolation remain deployment concerns.

### Credential leakage

Threat:
secrets appear in plans, ResourceReference, lineage, diagnostics or telemetry.

Controls:

- ResourceReference has no credential-value field;
- CredentialReference carries identifiers only;
- telemetry redaction covers credential/secret/token-like keys;
- serialization contracts exclude active provider credentials.

### Hidden engine fallback

Threat:
installed optional libraries silently change execution semantics.

Controls:

- engine ID is an explicit runtime argument;
- EngineRegistry has no implicit fallback;
- missing/unsupported capabilities fail explicitly;
- conformance tests verify no hidden fallback.

### Plugin auto-activation

Threat:
package import, discovery or wire decoding executes third-party plugin code.

Controls:

- core import does not discover/activate plugins;
- discovery and activation are separate operations;
- PluginDescriptor is not part of the safe wire semantic registry;
- activation requires an explicit plugin ID.

### Import-time side effects

Threat:
`import pytransformkit` imports optional engines, opens files or contacts networks.

Controls:

- root depends only on core dependencies;
- optional adapter packages are imported only through their qualified namespaces;
- LOT-26 import-safety tests block optional engine imports and network access.

### Telemetry-induced replay or failure

Threat:
telemetry failure changes business outcome or causes transformation replay.

Controls:

- telemetry is isolated as best-effort;
- sink failure becomes a diagnostic;
- runtime does not repeat transformation work because telemetry failed.

### Unbounded payload/resource consumption

Threat:
oversized or deeply nested wire payloads cause memory/CPU exhaustion.

Controls:

- maximum payload bytes;
- maximum nesting depth;
- strict JSON parser;
- explicit collection tags.

Residual risk:
engine-native execution can still be expensive; resource quotas belong to deployment
and orchestration environments.

### Native binding portability confusion

Threat:
a process-local DataFrame/Relation is mistaken for durable workflow state.

Controls:

- InputBinding distinguishes NATIVE and RESOURCE;
- native bindings carry explicit engine ID;
- PhysicalHandle is process-local;
- durable serialization codecs do not serialize active engine objects.

## Out of scope

PyTransformKit does not claim to provide:

- OS/container isolation;
- multi-tenant authorization;
- secret storage;
- arbitrary Python plugin sandboxing;
- network egress controls;
- malware scanning;
- distributed execution isolation;
- governed dataset publication.

Those concerns belong to the host platform, secret manager, workflow/orchestration
layer or sibling bounded context.

## Security conformance

LOT-26 CI verifies:

- core import without optional engines;
- core import with network calls denied;
- no canonical legacy root promotion;
- constructors do not perform physical file access;
- ResourceReference wire payloads do not contain credential material;
- unknown executable semantic types fail decoding;
- source contains no pickle/cloudpickle/dill durable fallback;
- serialization security/migration contracts;
- local filesystem confinement tests;
- plugin discovery/activation separation through the existing plugin contract suite.

## Threat-model review rule

A new V1.x feature that introduces a new trust boundary must document:

1. the untrusted input;
2. the protected asset;
3. the authority performing validation;
4. failure behavior;
5. secret handling;
6. replay/idempotency implications where side effects exist;
7. observability/redaction behavior;
8. conformance tests.

Changes that weaken a frozen security invariant require explicit release/security
review and cannot be hidden inside an adapter implementation.
