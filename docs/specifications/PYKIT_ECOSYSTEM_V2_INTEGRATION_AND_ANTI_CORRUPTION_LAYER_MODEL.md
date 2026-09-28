# PyKit Ecosystem V2 — Integration and Anti-Corruption Layer Model

> **Status:** NORMATIVE INTEGRATION BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit  
> **Compatibility posture:** clean-slate integration architecture  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_SHARED_CONTRACTS_AND_REFERENCE_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_EXECUTION_IDENTITY_AND_CORRELATION_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ERROR_FAILURE_RETRY_AND_UNCERTAINTY_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_DATASET_RESOURCE_AND_ARTIFACT_INTEROPERABILITY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_LINEAGE_PROVENANCE_AND_TRACEABILITY_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_OBSERVABILITY_EVENTS_AND_TELEMETRY_MODEL.md

---

# 1. Purpose

This document defines how the three PyKit frameworks integrate without merging their bounded contexts.

It formalizes:

- allowed dependency directions;
- anti-corruption layers;
- adapters;
- ports and protocols;
- provider/consumer responsibilities;
- boundary DTOs and references;
- translation rules;
- error/failure propagation;
- retry ownership;
- correlation propagation;
- lineage and observability handoff;
- optional dependency packaging;
- compatibility checks;
- cross-framework contract testing.

The governing principle is:

> **Integrate through explicit contracts; never integrate by sharing internal domain objects.**

---

# 2. Canonical integration directions

The V2 ecosystem allows exactly these sibling directions:

~~~text
PyWorkflowKit
    ├── optional integration ─► PyIngestKit
    └── optional integration ─► PyTransformKit

PyIngestKit
    └── optional integration ─► PyTransformKit

PyTransformKit
    └── no sibling dependency
~~~

This direction is architectural, not merely packaging convenience.

---

# 3. Forbidden sibling directions

The following are forbidden in core architecture:

~~~text
PyTransformKit → PyIngestKit
PyTransformKit → PyWorkflowKit

PyIngestKit core → PyWorkflowKit

PyWorkflowKit core → PyIngestKit internals
PyWorkflowKit core → PyTransformKit internals
~~~

The following cycle is explicitly forbidden:

~~~text
PyTransformKit
    ↓
PyIngestKit
    ↓
PyTransformKit
~~~

No convenience integration justifies a dependency cycle.

---

# 4. Anti-corruption layer

An Anti-Corruption Layer, or ACL, protects one bounded context from the internal model of another.

Canonical shape:

~~~text
Provider Domain
      ↓
Provider Public Contract
      ↓
Boundary DTO / Reference
      ↓
Consumer ACL
      ↓
Consumer Domain
~~~

The ACL translates semantics.

It MUST NOT simply re-export provider internals.

---

# 5. Why the ACL is mandatory

Without an ACL, one framework may begin depending on:

- private classes;
- storage schemas;
- persistence models;
- runtime state enums;
- engine-specific objects;
- provider retry policy;
- provider exception hierarchy;
- provider lifecycle details.

That creates semantic coupling.

The ACL exists to prevent such leakage.

---

# 6. Provider and consumer roles

For any integration:

~~~text
PROVIDER
    owns the source semantics

CONSUMER
    owns mapping into the target semantics
~~~

Example:

~~~text
PyIngestKit
    PROVIDES DatasetVersionReference

PyTransformKit integration
    CONSUMES it
    and maps it into InputBinding
~~~

The provider SHOULD NOT construct the consumer's internal domain object.

---

# 7. Consumer-owned translation

The default V2 rule is:

> **The consumer owns translation into its own domain.**

Therefore:

~~~text
PyTransformKit integration adapter
    understands DatasetVersionReference
~~~

rather than:

~~~text
PyIngestKit core
    constructs PyTransformKit Dataset internals
~~~

This preserves dependency direction and semantic isolation.

---

# 8. Integration module locations

Recommended modules are:

~~~text
pyingestkit.integrations.pytransformkit

pyworkflowkit.integrations.pyingestkit
pyworkflowkit.integrations.pytransformkit
~~~

These modules are optional integration surfaces.

They SHOULD remain isolated from core domain imports.

---

# 9. Core versus integration packages

Canonical package layering:

~~~text
core domain
    ↓
application/runtime
    ↓
infrastructure/adapters
    ↓
integrations
~~~

Sibling imports are permitted only at the integration boundary when required.

Core domain modules MUST remain sibling-independent.

---

# 10. Integration contracts

Cross-framework integration SHOULD use:

~~~text
public definitions
public result types
portable references
typed DTOs
small Protocols
stable error metadata
CorrelationContext
ExecutionReference
~~~

It SHOULD NOT use:

~~~text
private ORM entities
private repository classes
native engine objects
private graph nodes
process-local runtime state
undocumented dictionaries
~~~

---

# 11. Integration contract categories

The ecosystem recognizes five primary integration contract categories:

~~~text
INPUT CONTRACT
OUTPUT CONTRACT
EXECUTION CONTRACT
FAILURE CONTRACT
OBSERVABILITY CONTRACT
~~~

These categories may share references but have different semantic roles.

---

# 12. Input contract

An input contract tells the consumer what it is allowed to receive.

Examples:

~~~text
DatasetVersionReference
ResourceReference
ArtifactReference
TransformationPlan
IngestionDefinition
WorkflowDefinition
CorrelationContext
~~~

The receiving ACL validates the contract before mapping it.

---

# 13. Output contract

An output contract tells the caller what the provider returns.

Examples:

~~~text
IngestionResult
TransformationResult
WorkflowResult
ExecutionReference
ExternalRunRef
FailureEvidence
~~~

Result objects SHOULD contain portable references rather than private runtime internals.

---

# 14. Execution contract

An execution contract defines how one framework invokes another framework's runtime.

Conceptual examples:

~~~text
IngestionWorkloadAdapter.run(...)
TransformationWorkloadAdapter.execute(...)
TransformationInputAdapter.bind(...)
~~~

The exact APIs are framework-specific.

The semantic separation is normative.

---

# 15. Failure contract

Cross-framework failures SHOULD preserve:

~~~text
source framework
source component
error code
failure category
retryability
uncertainty
execution reference
correlation ID
provider evidence
~~~

Adapters MUST NOT flatten all failures into generic RuntimeError.

---

# 16. Observability contract

Cross-framework integrations SHOULD preserve:

~~~text
CorrelationId
CausationId
TraceId when enabled
native execution IDs
provider execution refs
framework ownership
~~~

The integration MAY emit its own adapter-level diagnostic event.

It MUST NOT impersonate the provider's domain events.

---

# 17. PyWorkflowKit → PyIngestKit integration

Canonical flow:

~~~text
WorkflowRuntime
    ↓
TaskAttempt
    ↓
PyIngestKit workload adapter
    ↓
IngestionRuntime.run(...)
    ↓
IngestionResult
    ↓
IngestionExecutionReference
    ↓
ExternalRunRef
    ↓
TaskAttempt evidence
~~~

WorkflowKit owns task lifecycle.

PyIngestKit owns ingestion lifecycle.

---

# 18. WorkflowKit → IngestKit responsibilities

PyWorkflowKit MAY own:

- when the task starts;
- task timeout;
- workload retry;
- task cancellation policy;
- task state;
- TaskAttempt identity;
- recovery coordination.

PyIngestKit owns:

- acquisition;
- RAW;
- decode;
- ingestion validation;
- DatasetVersion creation;
- publication semantics;
- bounded ingestion-specific retries;
- ingestion reconciliation.

---

# 19. WorkflowKit must not decompose ingestion stages

WorkflowKit MUST NOT reinterpret:

~~~text
ACQUIRE
PERSIST_RAW
DECODE
VALIDATE
VERSION
PUBLISH
~~~

as native WorkflowKit tasks unless the application explicitly models them as separate workloads.

PyIngestKit internal lifecycle remains opaque to WorkflowKit by default.

---

# 20. WorkflowKit → IngestKit retry boundary

Canonical rule:

~~~text
PyWorkflowKit
    retries the ingestion workload

PyIngestKit
    retries only bounded internal operations it can prove safe
~~~

If an IngestionRun ends with UNKNOWN_OUTCOME:

~~~text
WorkflowKit
    MUST NOT blindly launch a fresh ingestion attempt
~~~

until the adapter/provider can reconcile or the explicit policy allows a safe fresh execution.

---

# 21. WorkflowKit → IngestKit cancellation

Workflow cancellation may request ingestion cancellation.

Conceptually:

~~~text
TaskAttempt cancellation
    ↓
IngestionWorkloadAdapter.cancel(...)
    ↓
IngestionRuntime/provider cancellation
~~~

The adapter MUST preserve:

~~~text
CANCELLED
CANCELLATION_REQUESTED
CANCELLATION_UNCONFIRMED
CANCELLATION_UNSUPPORTED
~~~

where relevant.

---

# 22. WorkflowKit → IngestKit outputs

Typical task output should be:

~~~text
DatasetVersionReference
ArtifactReference
IngestionExecutionReference
ExternalRunRef
~~~

not:

~~~text
PyIngestKit ORM entity
internal repository object
raw database session
large decoded payload
~~~

---

# 23. PyWorkflowKit → PyTransformKit integration

Canonical flow:

~~~text
WorkflowRuntime
    ↓
TaskAttempt
    ↓
PyTransformKit workload adapter
    ↓
TransformationRuntime.execute(...)
    ↓
TransformationResult
    ↓
TransformationExecutionReference
    ↓
ExternalRunRef
    ↓
TaskAttempt evidence
~~~

WorkflowKit owns operational retry.

PyTransformKit owns transformation computation and engine interaction.

---

# 24. WorkflowKit must not inspect TransformationGraph for scheduling

The WorkflowKit integration MUST treat a TransformationPlan as one workload unless the application explicitly models its internals as separate WorkflowKit tasks.

Therefore:

~~~text
TransformationGraph
    !=
WorkflowGraph
~~~

WorkflowKit MUST NOT schedule transformation nodes individually by reaching into PyTransformKit internals.

---

# 25. WorkflowKit → PyTransformKit retry boundary

If a TransformationExecution fails with a known retryable workload-level failure:

~~~text
WorkflowKit
    may create a new TaskAttempt
        ↓
new TransformationExecution
~~~

If the transformation has UNKNOWN_OUTCOME after a side-effecting write:

~~~text
reconcile original TransformationExecution first
~~~

before fresh execution.

---

# 26. WorkflowKit → PyTransformKit cancellation

WorkflowKit MAY request cancellation through the adapter.

PyTransformKit/engine adapter determines:

- whether cancellation exists;
- whether it is asynchronous;
- whether completion is confirmed;
- whether provider execution may continue.

WorkflowKit preserves the provider truth.

---

# 27. WorkflowKit → PyTransformKit outputs

Typical task outputs include:

~~~text
TransformationResult
ResourceReference
ArtifactReference
TransformationExecutionReference
~~~

WorkflowKit SHOULD persist references, not native DataFrames or engine handles.

---

# 28. PyIngestKit → PyTransformKit integration

This integration allows ingestion to delegate logical transformation semantics.

Canonical flow:

~~~text
PyIngestKit decoded data
    ↓
PyTransformKit integration adapter
    ↓
InputBinding
    ↓
TransformationPlan
    ↓
TransformationRuntime.execute(...)
    ↓
TransformationResult
    ↓
portable output reference
    ↓
PyIngestKit validation/version/publication
~~~

PyIngestKit remains owner of ingestion lifecycle.

PyTransformKit remains owner of transformation semantics.

---

# 29. Why IngestKit may depend on TransformKit optionally

PyIngestKit may need optional transformation capability for:

- normalization;
- typed projection;
- derivation;
- joins;
- aggregation;
- standard reusable transformation logic before publication.

Instead of rebuilding such logic, it may delegate to PyTransformKit.

This dependency is optional because ingestion without business transformation must remain valid.

---

# 30. IngestKit must not absorb TransformationPlan internals

PyIngestKit SHOULD accept a public TransformationPlan or transformation integration contract.

It MUST NOT depend on:

- private AST nodes;
- optimizer internals;
- physical plan internals;
- engine adapter private classes.

---

# 31. TransformKit must not know IngestKit

PyTransformKit core MUST remain usable independently.

Therefore PyTransformKit core does not import:

~~~text
DatasetVersion
IngestionRun
RAW
PublishedDataset
PyIngestKit repositories
~~~

Any DatasetVersion mapping is handled in an optional integration layer outside TransformKit core.

---

# 32. DatasetVersionReference → InputBinding

Canonical translation:

~~~text
DatasetVersionReference
        ↓
DatasetVersionResolver
        ↓
ResourceReference
        ↓
PyTransformKit integration adapter
        ↓
InputBinding
        ↓
Logical Dataset binding
~~~

The transformation domain never needs the provider's persistence internals.

---

# 33. Transformation output → PyIngestKit publication

Canonical reverse handoff:

~~~text
TransformationResult
    ↓
OutputBinding
    ↓
ResourceReference / ArtifactReference
    ↓
PyIngestKit publication adapter
    ↓
DatasetVersion
    ↓
PublishedDataset
~~~

This is not a reverse package dependency from PyTransformKit to PyIngestKit.

The application or PyIngestKit integration owns the publication step.

---

# 34. Anti-corruption mapping rules

An ACL MUST define explicit mappings for:

~~~text
identity
status
errors
references
retryability
uncertainty
correlation
timestamps
outputs
capabilities
~~~

Mappings MUST be testable and versioned where persisted.

---

# 35. Identity mapping

Adapters preserve native identity.

Example:

~~~text
IngestionRunId I-288
    ↓
IngestionExecutionReference
    ↓
ExternalRunRef(provider="pyingestkit", external_run_id="I-288")
~~~

The adapter MUST NOT replace I-288 with TaskRunId.

---

# 36. Status mapping

Status translation SHOULD be conservative.

Example:

~~~text
PyTransformKit UNKNOWN_OUTCOME
    ↓
WorkflowKit TaskAttempt
    MUST NOT become simple FAILED automatically
~~~

The target domain may represent a corresponding uncertain state or structured failure evidence.

Lossy translation requires explicit policy.

---

# 37. Error mapping

Adapters SHOULD translate errors at semantic boundaries.

Example:

~~~text
TransformationExecutionError
    ↓
FailureEvidence
    ↓
TaskAttempt failure state
~~~

The original exception MAY remain as chained cause in-process.

Durable state uses structured evidence.

---

# 38. Retryability mapping

Provider retryability is evidence.

WorkflowKit remains owner of TaskRetryPolicy.

Therefore:

~~~text
provider says RETRYABLE
    does not mean
WorkflowKit MUST retry
~~~

WorkflowKit may still reject retry due to:

- deadline;
- exhausted attempts;
- cancellation;
- unsafe side effects;
- workflow policy.

---

# 39. Uncertainty mapping

Adapters MUST preserve:

~~~text
CERTAIN
OUTCOME_UNKNOWN
SIDE_EFFECT_MAY_HAVE_OCCURRED
REQUIRES_RECONCILIATION
~~~

Unknown outcome MUST NOT be flattened to generic failure for convenience.

---

# 40. Correlation mapping

Incoming CorrelationContext SHOULD propagate unchanged for the broader operation.

Adapters MAY add:

~~~text
causation_id
parent_execution_id
native execution reference
provider trace context
~~~

They MUST NOT create a new CorrelationId unless the integration intentionally starts an independent operation.

---

# 41. Causation mapping

When TaskAttempt invokes a sibling runtime:

~~~text
TaskAttemptId
    becomes causation reference
for sibling execution
~~~

Example:

~~~text
TaskAttempt TA-3
    ↓ causes
TransformationExecution T-913
~~~

The new transformation execution still gets its own native identity.

---

# 42. Lineage mapping

Cross-framework adapters SHOULD emit/link references sufficient to reconstruct:

~~~text
TaskAttempt
    → external execution

DatasetVersion
    → TransformationExecution input

TransformationExecution
    → output Resource

output Resource
    → published DatasetVersion
~~~

The adapter links native lineage models rather than merging them.

---

# 43. Observability mapping

Adapters SHOULD preserve:

~~~text
CorrelationId
CausationId
Trace context
native execution IDs
provider IDs
failure category
uncertainty
~~~

Adapter-specific events SHOULD use their own namespaced types.

Example:

~~~text
pyworkflowkit.integration.pytransformkit.invocation_started
~~~

Such events supplement rather than replace native provider events.

---

# 44. Capability negotiation

Integrations SHOULD validate compatibility before execution where possible.

Examples:

~~~text
PyTransformKit engine supports input Resource format?
PyIngestKit publication target supports idempotency?
WorkflowKit executor supports async cancellation?
~~~

Capability mismatch SHOULD fail during preflight when determinable.

---

# 45. Integration preflight

An integration MAY expose preflight checks for:

- package availability;
- package version compatibility;
- adapter presence;
- required extras;
- contract version support;
- provider capabilities;
- resolver availability;
- credential provider availability.

Preflight SHOULD avoid performing primary business side effects.

---

# 46. Optional dependencies

Core package import MUST work without sibling packages installed.

Examples:

~~~text
import pyworkflowkit
    must not require pyingestkit or pytransformkit

import pyingestkit
    must not require pytransformkit

import pytransformkit
    requires no sibling
~~~

Integration extras may add these dependencies explicitly.

---

# 47. Optional extras

Recommended conceptual extras:

~~~text
pyingestkit[transform]

pyworkflowkit[ingest]
pyworkflowkit[transform]
pyworkflowkit[ingest,transform]
~~~

Exact package names may evolve.

The architecture requires explicit optionality, not these exact strings.

---

# 48. Import isolation

Integration modules SHOULD import sibling packages lazily or behind optional dependency checks where practical.

Missing optional dependencies MUST produce clear errors such as:

~~~text
PyTransformKit integration requires pytransformkit>=X,<Y
~~~

not unrelated ImportError chains.

---

# 49. Version compatibility

Package versions remain independent.

Integration compatibility SHOULD be declared through package ranges and contract versions.

Example conceptually:

~~~text
pyworkflowkit 2.1
    supports pytransformkit >=0.8,<1.1
    transformation_execution_reference contract v1
~~~

Matching package versions are not required.

---

# 50. Contract version compatibility

Boundary DTO compatibility is based on explicit contract versions.

~~~text
contract_version != package_version
~~~

Adapters SHOULD reject unsupported required contract versions clearly.

Unknown optional fields may be tolerated according to the wire contract.

---

# 51. Integration handshake

A future adapter MAY expose a handshake describing:

~~~text
adapter_version
provider_package_version
supported_contract_versions
supported capabilities
optional features
~~~

Handshake is useful for remote/plugin integrations but is not mandatory for simple in-process imports.

---

# 52. Remote integrations

The same ACL principles apply if frameworks later communicate through:

- HTTP;
- RPC;
- queue;
- subprocess;
- container boundary;
- remote worker.

The only difference is that portable serialization becomes mandatory.

No design should rely exclusively on in-process object identity.

---

# 53. In-process optimization

Adapters MAY optimize in-process integration by sharing a PhysicalHandle when:

- both runtimes support it;
- ownership is explicit;
- lifetime is bounded;
- failure/recovery semantics are understood;
- durable reference exists when recovery needs one.

Optimization MUST NOT redefine the canonical portable contract.

---

# 54. Large payload rule

Integrations MUST prefer references for large payloads.

Do not pass whole DataFrames through WorkflowKit metadata or serialized task state.

Canonical handoff:

~~~text
large data
    ↓
durable resource
    ↓
ResourceReference / DatasetVersionReference
~~~

---

# 55. Resource ownership

If an integration passes active resources, ownership MUST be explicit:

~~~text
BORROWED
OWNED
TRANSFERRED
~~~

The receiving runtime MUST NOT close borrowed resources.

Portable references do not imply active resource ownership.

---

# 56. Transaction boundary

Cross-framework integration does not imply one distributed transaction.

Example:

~~~text
TransformationExecution succeeds
    ↓
PyIngestKit publication fails
~~~

These are two distinct runtime outcomes.

The application/workflow decides compensation, retry or reconciliation.

A fake atomic cross-framework transaction MUST NOT be implied.

---

# 57. Saga-like composition

WorkflowKit MAY coordinate multi-step compensation:

~~~text
ingest
    ↓
transform
    ↓
publish
    ↓
notification
~~~

If publication fails after transformation succeeded, WorkflowKit may coordinate next action.

But the provider domain defines compensation semantics.

---

# 58. Integration idempotency

Adapters MUST not invent idempotency.

If an external or sibling operation is retried:

- provider idempotency semantics must be known;
- idempotency key scope must be explicit;
- retry owner must be explicit;
- uncertain outcomes must be reconciled.

---

# 59. Integration cancellation

Cancellation contracts SHOULD specify:

~~~text
request semantics
confirmation semantics
timeout
unsupported behavior
uncertainty
provider operation identity
~~~

Caller and provider cancellation states may differ temporarily.

---

# 60. Integration recovery

Recovery should reattach to existing sibling executions when possible.

Example:

~~~text
Workflow process restarts
    ↓
TaskAttempt retains ExternalRunRef T-913
    ↓
adapter queries/reconciles T-913
~~~

Recovery SHOULD NOT start T-914 merely because local process state was lost.

---

# 61. Integration replay

Replay is explicit.

If WorkflowKit asks PyIngestKit to replay from RAW:

~~~text
new IngestionRunId
REPLAYED_FROM original RAW
~~~

The adapter should call a PyIngestKit replay API, not reconstruct ingestion stages manually.

---

# 62. Integration observability failures

An adapter failing to export telemetry MUST NOT imply provider execution failed.

Telemetry errors remain telemetry-scope unless telemetry is explicitly required by policy.

---

# 63. Integration security

Boundary adapters MUST treat references and metadata as untrusted input unless trust is explicitly established.

They SHOULD validate:

- contract type;
- contract version;
- namespace;
- locator safety;
- credential references;
- allowed metadata;
- resource ownership;
- serialization limits.

---

# 64. No credential tunneling

An adapter MUST NOT place credentials into:

~~~text
ResourceReference.metadata
ExternalRunRef.metadata
CorrelationContext
lineage metadata
telemetry attributes
~~~

Credentials travel through explicit credential providers/references.

---

# 65. Input validation at ACL boundary

An ACL SHOULD validate inbound contracts before mapping.

Validation layers:

~~~text
structural validation
semantic validation
runtime preflight
~~~

The ACL must distinguish malformed reference from inaccessible resource.

---

# 66. Output sanitization

Before returning a cross-framework result, the integration layer SHOULD remove or avoid:

- active sessions;
- raw provider clients;
- engine-native objects unless explicitly in-process;
- private domain objects;
- secret metadata.

The result should remain understandable from public contracts.

---

# 67. Integration APIs are not universal APIs

The ecosystem SHOULD NOT create generic abstractions such as:

~~~text
UniversalWorkloadAdapter
GenericPipelineAdapter
PyKitService
AnyRun
BaseIntegrationResult
~~~

unless real cross-domain semantics emerge later.

Specific adapters are preferred.

---

# 68. Ports

Small consumer-owned ports MAY define required capabilities.

Examples:

~~~text
DatasetVersionResolver
TransformationExecutor
IngestionRunner
ExternalRunInspector
CancellationPort
ReconciliationPort
~~~

Each port SHOULD model one capability.

Avoid God interfaces.

---

# 69. Protocol evolution

A public Protocol or interface becomes a compatibility contract.

Before stabilizing it, define:

- lifecycle;
- thread/process safety;
- exceptions;
- ownership;
- async semantics;
- return types;
- versioning;
- optional capabilities.

Do not publish extension interfaces prematurely.

---

# 70. Sync versus async integration

An integration may offer sync or async execution according to runtime needs.

The architecture does not require every adapter to expose both.

If both exist, they MUST preserve equivalent semantics for:

- identity;
- correlation;
- failure;
- cancellation;
- results.

---

# 71. Subprocess integration

A subprocess adapter SHOULD serialize:

~~~text
input contract
CorrelationContext
execution config
portable references
~~~

It MUST NOT rely on arbitrary Python object pickle as the durable compatibility mechanism.

---

# 72. Queue integration

Queue-based adapters SHOULD include:

~~~text
message_id
contract type/version
correlation_id
causation_id
payload/reference
idempotency metadata
~~~

Delivery semantics and deduplication must be documented.

---

# 73. Remote status polling

Remote integrations may need polling.

Polling belongs to the adapter/provider integration.

WorkflowKit MAY ask:

~~~text
inspect ExternalRunRef
~~~

but should not know provider-specific polling fields.

---

# 74. Push callbacks/webhooks

A remote provider MAY push completion callbacks.

Callbacks MUST map to existing execution identities.

They MUST NOT create a new run merely because completion arrived asynchronously.

Webhook authentication/security is adapter responsibility.

---

# 75. Integration lifecycle

A stateful adapter MAY define:

~~~text
initialize
preflight
execute
inspect
cancel
reconcile
close
~~~

Not every adapter needs every operation.

Capabilities should be declared explicitly.

---

# 76. Integration registry

A runtime MAY maintain an explicit integration registry.

Example:

~~~text
provider = "pytransformkit"
    → TransformationWorkloadAdapter
~~~

Registration MUST be explicit.

Importing a package MUST NOT silently mutate a global registry.

---

# 77. Plugin discovery

Integration plugins MAY be discovered from package metadata.

Discovery and activation remain separate.

Installed code is not automatically trusted or activated.

Compatibility should be checked before registration.

---

# 78. Integration naming

Public integration types SHOULD reveal both direction and role when ambiguity exists.

Examples:

~~~text
PyTransformKitDatasetInputAdapter
PyTransformKitWorkloadAdapter
PyIngestKitWorkloadAdapter
PyIngestKitPublicationAdapter
~~~

Avoid generic Adapter at package root.

---

# 79. Integration result types

Integration adapters MAY return small adapter-specific result DTOs when the provider result alone is insufficient.

Such DTOs SHOULD contain references to provider results rather than duplicate them wholesale.

Example:

~~~text
TransformationWorkloadOutcome
    transformation_result_reference
    external_run_ref
    failure_evidence?
~~~

---

# 80. No semantic duplication

If PyTransformKit already defines TransformationResult, the WorkflowKit integration SHOULD NOT create another full transformation result model.

It may wrap/reference it for workflow purposes.

The same rule applies to IngestionResult.

---

# 81. Integration lineage

Adapters SHOULD preserve enough links to compose end-to-end traceability.

Example:

~~~text
TaskAttempt
    EXECUTED_BY
TransformationExecution

TransformationExecution
    CONSUMED
DatasetVersion

TransformationExecution
    PRODUCED
Resource

Resource
    PUBLISHED_AS
DatasetVersion
~~~

No adapter becomes owner of every edge.

---

# 82. Integration manifests

An integration MAY produce a small manifest recording:

~~~text
adapter
provider version
consumer version
contract versions
input refs
output refs
native execution refs
correlation
mapping diagnostics
~~~

This is useful for support.

It does not replace provider/consumer manifests.

---

# 83. Integration observability namespace

Integration-specific telemetry SHOULD use explicit namespace.

Examples:

~~~text
pyworkflowkit.integration.pyingestkit.*
pyworkflowkit.integration.pytransformkit.*
pyingestkit.integration.pytransformkit.*
~~~

This makes adapter problems distinguishable from provider runtime failures.

---

# 84. Adapter error classification

An adapter should distinguish:

~~~text
ADAPTER_CONFIGURATION_ERROR
CONTRACT_VERSION_UNSUPPORTED
CONTRACT_MAPPING_ERROR
PROVIDER_UNAVAILABLE
PROVIDER_FAILURE
REFERENCE_RESOLUTION_FAILED
CAPABILITY_MISMATCH
CANCELLATION_UNSUPPORTED
RECONCILIATION_UNSUPPORTED
~~~

These categories should not overwrite the original provider failure category.

---

# 85. Compatibility failure

Incompatible package/contract versions SHOULD fail during integration setup or preflight when possible.

Do not wait until deep execution to discover obvious incompatibility.

---

# 86. Graceful absence

If an optional sibling package is not installed:

- core import still works;
- unrelated features still work;
- integration entry point fails clearly;
- error message indicates required optional extra or package range.

---

# 87. Framework independence test

A mandatory architecture test is:

~~~text
uninstall sibling packages
    ↓
import core package
    ↓
run core-only tests
    ↓
success
~~~

This test should exist for all three projects.

---

# 88. Import graph test

Static architecture tests SHOULD assert:

~~~text
pytransformkit.core
    imports no pyingestkit
    imports no pyworkflowkit

pyingestkit.core
    imports no pyworkflowkit

pyworkflowkit.core
    imports no pyingestkit
    imports no pytransformkit
~~~

Only integration namespaces may cross allowed boundaries.

---

# 89. Consumer contract tests

The consumer SHOULD own contract tests proving it can consume supported provider contracts.

Examples:

~~~text
PyTransformKit
    consumes DatasetVersionReference v1

PyWorkflowKit
    consumes TransformationExecutionReference v1
~~~

Provider internals are irrelevant to these tests.

---

# 90. Provider contract tests

Providers SHOULD test that emitted references/results satisfy their published contract.

Examples:

~~~text
PyIngestKit
    emits valid DatasetVersionReference

PyTransformKit
    emits valid TransformationExecutionReference
~~~

This enables independent evolution.

---

# 91. Producer-consumer compatibility tests

For important integrations, CI SHOULD run matrix tests across supported package ranges.

Example:

~~~text
PyWorkflowKit 2.x
    × PyTransformKit supported versions

PyIngestKit 2.x
    × PyTransformKit supported versions
~~~

The exact matrix belongs to release/compatibility strategy.

---

# 92. Golden boundary fixtures

Stable serialized reference/result fixtures SHOULD be used for cross-version tests.

Golden fixtures should verify:

- contract version;
- required fields;
- namespace;
- identity;
- optional-field tolerance;
- redaction.

---

# 93. Failure propagation tests

Required scenarios include:

~~~text
provider validation failure
provider transient failure
provider timeout
provider UNKNOWN_OUTCOME
provider cancellation unsupported
reconciliation success
reconciliation still unknown
retry exhaustion
~~~

The consumer must preserve semantic distinctions.

---

# 94. Correlation propagation tests

Tests SHOULD verify:

~~~text
incoming CorrelationId
    unchanged downstream

TaskAttemptId
    propagated as causation where appropriate

provider native execution ID
    returned through reference

Trace context
    preserved when enabled
~~~

---

# 95. Data handoff tests

At minimum:

~~~text
DatasetVersionReference
    → PyTransformKit InputBinding

Transformation output ResourceReference
    → PyIngestKit publication

WorkflowKit Task output
    → durable reference only
~~~

Process-local handles should be rejected from durable workflow state.

---

# 96. Retry ownership tests

Tests MUST prove that:

- WorkflowKit retries workloads;
- IngestKit does not silently retry whole workflow-owned ingestion runs;
- TransformKit does not silently retry whole workflow-owned transformations;
- provider retries are bounded and visible;
- unknown outcomes trigger reconciliation before unsafe replay.

---

# 97. Cancellation tests

Integration tests SHOULD cover:

~~~text
request accepted
confirmed cancelled
unsupported cancellation
unconfirmed cancellation
provider completes after cancellation request
~~~

Task/workflow status mapping must remain semantically correct.

---

# 98. Recovery tests

Simulate:

~~~text
Workflow process crash
    ↓
persisted ExternalRunRef
    ↓
restart
    ↓
adapter reattaches/reconciles provider execution
~~~

A fresh provider execution MUST NOT start merely because local process memory was lost.

---

# 99. Security tests

Integration tests SHOULD verify:

- credentials are not serialized in references;
- URIs are redacted where required;
- untrusted metadata cannot instantiate arbitrary Python classes;
- unsupported contract types fail closed;
- optional plugin activation is explicit.

---

# 100. Performance tests

Integration overhead SHOULD remain measurable.

Potential tests include:

~~~text
reference translation latency
serialization overhead
zero-copy path availability
resolver latency
adapter call overhead
~~~

Performance optimization MUST NOT weaken boundary semantics.

---

# 101. No premature shared contracts package

The ACL model does not require a shared runtime dependency.

Shared semantics may initially be implemented independently.

A shared contracts package may be extracted later only when:

- multiple frameworks implement the same stable contract;
- wire schemas are stable;
- duplication is measurable;
- extraction avoids cycles;
- the package remains domain-neutral.

---

# 102. Integration architecture review gate

Every new sibling integration MUST answer:

1. What is the dependency direction?
2. Which framework is provider?
3. Which framework is consumer?
4. Which public contract crosses the boundary?
5. Who maps the contract into the consumer domain?
6. Which runtime owns retry?
7. How are uncertain outcomes preserved?
8. How are native execution IDs preserved?
9. How is CorrelationId propagated?
10. Which lineage links are emitted?
11. Which telemetry namespace is used?
12. What optional dependencies are required?
13. Which contract/package versions are supported?
14. How does cancellation work?
15. How does recovery/reconciliation work?

If these cannot be answered, the integration is not architecture-ready.

---

# 103. Anti-patterns

Rejected:

~~~text
PyWorkflowKit imports pytransformkit._internal.*
~~~

Rejected:

~~~text
PyIngestKit creates PyTransformKit private graph nodes
~~~

Rejected:

~~~text
PyTransformKit imports DatasetVersion ORM model
~~~

Rejected:

~~~text
WorkflowKit stores Pandas DataFrame inside TaskRun metadata
~~~

Rejected:

~~~text
adapter catches every exception
    and raises RuntimeError
~~~

Rejected:

~~~text
provider UNKNOWN_OUTCOME
    mapped to FAILED
~~~

Rejected:

~~~text
Task retry + provider whole-run retry
    without explicit ownership
~~~

Rejected:

~~~text
global registry modified during import
~~~

---

# 104. Canonical end-to-end integration

~~~text
                         PyWorkflowKit
                              │
                      WorkflowRun W-42
                              │
          ┌───────────────────┼────────────────────┐
          │                   │                    │
          ▼                   ▼                    ▼
    ingest_customers    transform_customers      publish
          │                   │                    │
          ▼                   ▼                    ▼
PyIngestKit adapter   PyTransformKit adapter   PyIngestKit adapter
          │                   │                    │
          ▼                   ▼                    ▼
 IngestionRun I-1   TransformationExecution T-1  IngestionRun I-2
          │                   │                    │
          ▼                   │                    ▼
 customers@52 ───────────────►│              customer_mart@8
                              │
                              ▼
                     ResourceReference R-90
                              │
                              └────────────────────► publication
~~~

The workflow coordinates.

The ingestion framework governs dataset lifecycle.

The transformation framework owns logical compute semantics.

The adapters preserve boundaries.

---

# 105. Acceptance criteria

This specification is implemented correctly when:

1. sibling dependency direction follows the canonical graph;
2. PyTransformKit has no sibling dependency;
3. PyIngestKit core has no PyWorkflowKit dependency;
4. PyWorkflowKit core has no sibling dependency;
5. all sibling integrations live behind explicit integration modules;
6. consumer ACLs map provider contracts into consumer domains;
7. private provider objects never become cross-framework contracts;
8. DatasetVersionReference can become PyTransformKit InputBinding without PyIngestKit internals;
9. WorkflowKit can invoke IngestKit and TransformKit as opaque workloads;
10. WorkflowKit does not schedule TransformationGraph internals;
11. retry ownership remains explicit;
12. UNKNOWN_OUTCOME survives adapter translation;
13. native execution identities remain intact;
14. CorrelationId propagates end-to-end;
15. cancellation and reconciliation semantics are preserved;
16. large data passes by reference rather than workflow metadata;
17. optional sibling dependencies are truly optional;
18. package and contract compatibility is checked explicitly;
19. architecture/import graph tests prevent forbidden dependencies;
20. producer-consumer integration tests run in CI.

---

# 106. Normative invariants

### INT-INV-01 — Integration occurs through public contracts

Private objects never cross sibling boundaries.

### INT-INV-02 — Consumer owns domain translation

Providers do not construct consumer internals.

### INT-INV-03 — Dependency direction is acyclic

No sibling integration creates a package cycle.

### INT-INV-04 — Core packages remain independently usable

Sibling frameworks are optional.

### INT-INV-05 — WorkflowKit treats siblings as workloads

It does not absorb their internal domain models.

### INT-INV-06 — PyTransformKit remains lowest-level

It never depends on PyIngestKit or PyWorkflowKit.

### INT-INV-07 — Retry ownership survives integration

Adapters do not silently add whole-workload retries.

### INT-INV-08 — Uncertainty survives mapping

UNKNOWN_OUTCOME is never flattened for convenience.

### INT-INV-09 — Native identities survive mapping

TaskRunId, IngestionRunId and TransformationExecutionId remain distinct.

### INT-INV-10 — Correlation propagates across adapters

One broader operation retains one correlation story.

### INT-INV-11 — Durable boundaries use portable references

Physical handles are optimization-only.

### INT-INV-12 — Integration compatibility is explicit

Package ranges and contract versions are declared and tested.

---

# 107. Final architecture statement

PyKit V2 integration is not shared-domain inheritance.

It is explicit composition:

~~~text
Provider Domain
    ↓
Public Contract
    ↓
Portable Reference / Result
    ↓
Consumer Anti-Corruption Layer
    ↓
Consumer Domain
~~~

The three canonical bridges are:

~~~text
PyWorkflowKit → PyIngestKit
PyWorkflowKit → PyTransformKit
PyIngestKit   → PyTransformKit
~~~

with no reverse core dependencies.

The central rule is:

> **A framework may understand another framework's public contract, but it must never need to understand that framework's private model in order to compose with it.**

This specification is the baseline for:

~~~text
PYKIT_ECOSYSTEM_V2_DEPENDENCY_PACKAGING_AND_OPTIONAL_EXTRAS_STRATEGY.md
PYKIT_ECOSYSTEM_V2_SERIALIZATION_AND_WIRE_CONTRACTS.md
PYKIT_ECOSYSTEM_V2_ARCHITECTURE_CONFORMANCE_AND_TEST_STRATEGY.md
PYKIT_ECOSYSTEM_V2_REFERENCE_APPLICATION_SPEC.md
~~~
