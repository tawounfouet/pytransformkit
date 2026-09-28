# PyKit Ecosystem V2 — Observability, Events and Telemetry Model

> **Status:** NORMATIVE OBSERVABILITY BASELINE
> **Architecture generation:** V2
> **Date:** 2026-09-28
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit
> **Compatibility posture:** clean-slate observability model
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_SHARED_CONTRACTS_AND_REFERENCE_MODEL.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_EXECUTION_IDENTITY_AND_CORRELATION_MODEL.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_ERROR_FAILURE_RETRY_AND_UNCERTAINTY_MODEL.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_DATASET_RESOURCE_AND_ARTIFACT_INTEROPERABILITY.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_LINEAGE_PROVENANCE_AND_TRACEABILITY_MODEL.md

---

# 1. Purpose

This document defines the V2 observability model shared by PyIngestKit, PyTransformKit and PyWorkflowKit.

It covers structured events, logs, metrics, traces, diagnostics, manifests, correlation propagation, telemetry sinks, redaction, cardinality, retention and cross-framework aggregation.

The governing principle is:

> **Observability explains what happened; it does not own what happened.**

Telemetry is evidence about domain and runtime state. It MUST NOT become a second source of truth.

---

# 2. Canonical observability planes

The ecosystem distinguishes:

~~~text
EVENTS
LOGS
METRICS
TRACES
DIAGNOSTICS
MANIFESTS
~~~

Events describe meaningful transitions.

Logs provide human and developer diagnostics.

Metrics describe aggregate numerical behavior.

Traces describe distributed timing and call relationships.

Diagnostics explain decisions, warnings and anomalies.

Manifests preserve durable execution evidence.

These concepts complement each other and MUST NOT be treated as interchangeable.

---

# 3. Bounded-context ownership

Each framework owns the semantics of the telemetry it produces.

~~~text
PyIngestKit
    acquisition
    RAW persistence
    decode
    validation
    versioning
    publication

PyTransformKit
    planning
    optimization
    engine selection
    execution
    materialization
    output binding

PyWorkflowKit
    workflow lifecycle
    task lifecycle
    attempts
    retries
    cancellation
    recovery
    reconciliation
~~~

A shared telemetry backend may aggregate these signals. It does not become the semantic owner.

---

# 4. Event model

An Event is an immutable structured statement that a meaningful transition or observation occurred.

Examples:

~~~text
IngestionRunStarted
RawArtifactPersisted
DatasetVersionCreated

TransformationExecutionStarted
LogicalPlanCompiled
TransformationOutputProduced

WorkflowRunStarted
TaskAttemptFailed
RetryScheduled
WorkflowRunCompleted
~~~

Persisted or transmitted events SHOULD be timestamped, correlation-aware, serializable and versioned.

---

# 5. Common event envelope

Cross-framework events SHOULD support a conceptual envelope such as:

~~~text
EventEnvelope
    event_id
    event_type
    event_version
    occurred_at

    source_framework
    source_component?

    correlation_id?
    causation_id?

    workflow_run_id?
    task_run_id?
    task_attempt_id?
    ingestion_run_id?
    transformation_execution_id?

    trace_id?
    span_id?

    subject_reference?
    payload
    metadata?
~~~

The exact wire shape belongs to the serialization specification.

---

# 6. Event identity and versioning

EventId identifies the event record itself and MUST remain distinct from every execution ID and CorrelationId.

EventType SHOULD reveal semantic ownership.

Preferred examples:

~~~text
pyingestkit.dataset_version.created
pytransformkit.execution.started
pyworkflowkit.task_attempt.failed
~~~

Avoid unqualified event names such as Started, Failed or Completed.

Persisted event families require explicit EventVersion independent from package versions.

---

# 7. Event time, ordering and causation

Events SHOULD use timezone-aware timestamps.

occurred_at means when the producer observed the event.

recorded_at MAY identify persistence time.

Distributed systems do not guarantee a global event order.

Where ordering matters, use explicit local sequence fields and causation references.

Timestamp ordering MUST NOT replace CausationId.

---

# 8. Events are not state

Unless a framework explicitly adopts event sourcing:

~~~text
telemetry event stream
    !=
authoritative state store
~~~

Workflow status remains owned by PyWorkflowKit.

Ingestion status remains owned by PyIngestKit.

Transformation execution status remains owned by PyTransformKit.

Losing a telemetry event MUST NOT silently corrupt runtime state.

---

# 9. Logs

Libraries SHOULD emit structured logs through package namespaces:

~~~text
pyingestkit.*
pytransformkit.*
pyworkflowkit.*
~~~

Libraries MUST NOT configure the application root logger.

Relevant context may include:

~~~text
framework
component
correlation_id
workflow_run_id
task_run_id
task_attempt_id
ingestion_run_id
transformation_execution_id
engine
adapter
diagnostic_code
~~~

Only fields relevant to the current scope need to be attached.

---

# 10. Log severity

Conventional severity semantics SHOULD be preserved.

~~~text
DEBUG
    detailed developer diagnostics

INFO
    expected lifecycle milestones

WARNING
    unexpected but non-fatal condition

ERROR
    failed operation

CRITICAL
    process or system integrity at risk
~~~

A retryable failure is not automatically CRITICAL.

A successful execution may legitimately emit WARNING diagnostics.

---

# 11. No duplicate signal inflation

One failure may appear in state, events, logs, traces and metrics.

That is acceptable.

However, helpers SHOULD NOT repeatedly log the same exception at every call frame.

Prefer one meaningful log at each semantic boundary and preserve structured failure evidence.

---

# 12. Secret and payload safety

Telemetry MUST NOT expose:

~~~text
passwords
API keys
access tokens
private keys
signed URLs
SAS tokens
credential-bearing DSNs
raw secret values
~~~

Telemetry SHOULD NOT emit raw datasets by default.

Avoid entire rows, DataFrames, source files, unbounded query results and raw payload bodies.

Prefer safe counts, fingerprints, references, redacted summaries and explicitly configured samples.

Redaction MUST occur before telemetry leaves the producing runtime boundary.

---

# 13. Diagnostics

A Diagnostic is structured evidence explaining planning, validation, runtime decisions, warnings or anomalies.

Conceptually:

~~~text
Diagnostic
    code
    severity
    source_framework
    source_component?
    message
    execution_reference?
    correlation_id?
    details?
~~~

Stable diagnostic codes SHOULD be used when machine handling matters.

Human-readable messages may evolve.

---

# 14. Result diagnostics

Important diagnostics MUST remain accessible even when no external telemetry backend is configured.

Conceptually:

~~~text
TransformationResult
    execution_id
    status
    diagnostics
    warnings
    outputs
~~~

The same principle applies to IngestionResult and WorkflowResult.

Core correctness and inspectability do not depend on logging, metrics or tracing infrastructure.

---

# 15. Metrics

Metrics are aggregated numerical observations.

Representative metric families include:

~~~text
PyIngestKit
    ingestion_runs_total
    ingestion_duration_seconds
    source_bytes_acquired_total
    dataset_versions_created_total
    publications_total

PyTransformKit
    transformation_executions_total
    transformation_duration_seconds
    logical_plan_compile_duration_seconds
    optimizer_rules_applied_total
    engine_operations_total

PyWorkflowKit
    workflow_runs_total
    workflow_duration_seconds
    task_runs_total
    task_attempts_total
    retries_total
    recoveries_total
~~~

Metrics MAY be counters, gauges or histograms according to semantics.

---

# 16. Metric cardinality

Default metric labels MUST remain bounded.

Appropriate labels may include:

~~~text
framework
operation
status
engine
adapter
failure_category
environment
~~~

The following MUST NOT be default metric labels:

~~~text
workflow_run_id
task_run_id
task_attempt_id
ingestion_run_id
transformation_execution_id
correlation_id
dataset_version_id
full URI
error message
SQL text
~~~

Exact execution identities belong in logs, traces, events and manifests.

---

# 17. Failure, retry and uncertainty metrics

Failure metrics SHOULD use stable categories rather than exception text.

Retry metrics SHOULD distinguish owner and scope.

Examples:

~~~text
workflow_task_retries_total
ingestion_provider_retries_total
transformation_provider_retries_total
~~~

UNKNOWN_OUTCOME and REQUIRES_RECONCILIATION SHOULD be observable separately from FAILED.

Possible measures include:

~~~text
unknown_outcomes_total
reconciliations_started_total
reconciliations_resolved_total
~~~

---

# 18. Trace model

Tracing SHOULD map actual runtime boundaries into spans.

Typical shape:

~~~text
WorkflowRun
    ↓
TaskAttempt
        ↓
IngestionRun
            ↓
SourceAcquisition
~~~

or:

~~~text
WorkflowRun
    ↓
TaskAttempt
        ↓
TransformationExecution
            ↓
EngineOperation
~~~

TraceId and SpanId remain observability identifiers.

They MUST NOT replace native execution IDs.

---

# 19. Trace attributes

Useful attributes may include:

~~~text
pykit.framework
pykit.operation
pykit.correlation_id

pykit.workflow_run_id
pykit.task_run_id
pykit.task_attempt_id
pykit.ingestion_run_id
pykit.transformation_execution_id

pykit.engine
pykit.adapter
pykit.failure_category
pykit.outcome
~~~

Sensitive attributes MUST be redacted.

Trace sampling MUST NOT affect domain correctness or recovery.

---

# 20. Honest tracing granularity

PyTransformKit MUST NOT fabricate per-transformation spans or timings when a lazy engine does not expose separate physical execution boundaries.

Instead, it should expose:

~~~text
logical plan evidence
physical execution span
provider operations that are actually observable
~~~

Telemetry granularity must reflect real runtime evidence.

---

# 21. Manifests

Each framework MAY create durable execution manifests.

Possible contents:

~~~text
framework version
native execution identity
correlation context
definition or plan fingerprint
input references
output references
status
timestamps
diagnostics
lineage references
provider references
~~~

Manifests MUST NOT contain active handles or secrets.

A Manifest is durable evidence, not the runtime state machine.

---

# 22. Event sinks and telemetry adapters

Optional extension points may include:

~~~text
EventSink
MetricsSink
TraceProviderAdapter
DiagnosticCollector
ManifestWriter
RedactionPolicy
TelemetryProcessor
~~~

Core packages MUST NOT depend on one vendor such as Prometheus, Datadog, OpenTelemetry, Elastic, Splunk, CloudWatch or Azure Monitor.

Vendor integration belongs to optional adapters.

---

# 23. Multi-sink emission

A runtime MAY emit to several destinations:

~~~text
structured logs
+
event sink
+
metrics exporter
+
trace provider
+
manifest writer
~~~

One non-critical telemetry sink failing MUST NOT automatically fail or repeat the business operation.

Telemetry delivery retry is scoped to telemetry delivery only.

It MUST NEVER replay ingestion, transformation or workflow work.

---

# 24. Telemetry failure policy

Telemetry sinks SHOULD declare a policy such as:

~~~text
BEST_EFFORT
BUFFERED
REQUIRED
FAIL_CLOSED_FOR_AUDIT
~~~

Ordinary monitoring telemetry should generally be best-effort or buffered.

Recovery-critical state persistence is not telemetry and follows stronger domain guarantees.

---

# 25. Buffering and backpressure

Telemetry buffering MUST be bounded.

A telemetry adapter SHOULD define:

~~~text
buffer size
flush policy
shutdown timeout
overflow behavior
durability
~~~

Possible overflow strategies:

~~~text
DROP_NEWEST
DROP_OLDEST
BLOCK_WITH_TIMEOUT
SPILL_TO_DISK
FAIL
~~~

Non-critical telemetry MUST NOT block business execution indefinitely.

Dropped telemetry SHOULD be observable when practical.

---

# 26. Event delivery semantics

Event adapters SHOULD document whether they provide:

~~~text
BEST_EFFORT
AT_MOST_ONCE
AT_LEAST_ONCE
EFFECTIVELY_ONCE_WITH_DEDUP
~~~

Exactly-once semantics MUST NOT be implied without an explicit guarantee.

Consumers of at-least-once events SHOULD deduplicate by EventId when needed.

Duplicate event delivery does not imply duplicate domain execution.

---

# 27. Framework event families

Recommended PyIngestKit families include:

~~~text
IngestionRunStarted
SourceAcquisitionStarted
SourceAcquisitionCompleted
RawArtifactPersisted
DecodeCompleted
IngestionValidationCompleted
DatasetVersionCreated
PublicationStarted
PublicationCompleted
IngestionRunSucceeded
IngestionRunFailed
IngestionRunReconciliationRequired
~~~

Recommended PyTransformKit families include:

~~~text
TransformationExecutionStarted
InputBound
LogicalPlanCompiled
LogicalPlanValidated
OptimizerRuleApplied
PhysicalPlanCreated
EngineSelected
EngineExecutionStarted
OutputProduced
TransformationExecutionSucceeded
TransformationExecutionFailed
TransformationExecutionReconciliationRequired
~~~

Recommended PyWorkflowKit families include:

~~~text
WorkflowRunCreated
WorkflowRunStarted
TaskRunReady
TaskAttemptStarted
TaskAttemptSucceeded
TaskAttemptFailed
RetryDecisionMade
RetryScheduled
TaskRunSucceeded
TaskRunFailed
WorkflowRunCancellationRequested
WorkflowRunRecovered
WorkflowRunReconciled
WorkflowRunSucceeded
WorkflowRunFailed
~~~

---

# 28. Retry observability

Retry events SHOULD expose enough evidence to diagnose ownership and amplification.

Conceptually:

~~~text
RetryScheduled
    retry_owner
    failure_domain
    attempt_number
    reason_code
    delay
    deadline_remaining?
    failure_category
    uncertainty
    correlation_id
    execution_reference
~~~

Provider retries and WorkflowKit TaskAttempts MUST remain distinguishable.

---

# 29. Reconciliation, cancellation and recovery events

Reconciliation SHOULD emit explicit events such as:

~~~text
ReconciliationStarted
ReconciliationConfirmedSucceeded
ReconciliationConfirmedFailed
ReconciliationStillUnknown
~~~

Cancellation SHOULD distinguish request from confirmation:

~~~text
CancellationRequested
CancellationAccepted
CancellationConfirmed
CancellationUnsupported
CancellationUnconfirmed
~~~

Recovery MAY expose:

~~~text
RecoveryStarted
StateReloaded
ExternalExecutionReattached
TaskStateReconciled
RecoveryCompleted
RecoveryFailed
~~~

---

# 30. Telemetry configuration

Telemetry belongs to runtime configuration, not domain definitions.

~~~text
TransformationPlan
    does not contain monitoring vendor configuration

TransformationRuntimeConfig
    may configure telemetry
~~~

This preserves domain purity and portability.

---

# 31. Safe defaults

Default package behavior SHOULD guarantee:

- no external telemetry network calls without explicit configuration;
- no root logger configuration;
- no exporter thread started during import;
- no metrics server started during import;
- no secrets in telemetry;
- bounded buffering;
- no high-cardinality execution-ID labels;
- no telemetry dependency required for core import.

---

# 32. Context propagation

Correlation and tracing context SHOULD propagate through supported execution boundaries.

~~~text
thread
async task
process
subprocess
external provider request
~~~

Python context variables MAY help in-process propagation.

They MUST NOT be the only durable cross-process mechanism.

Concurrent executions MUST NOT leak context into one another.

---

# 33. Provider correlation

Adapters MAY attach correlation identifiers to provider-native observability mechanisms.

Example:

~~~text
Snowflake QUERY_TAG
    correlation_id
    workflow_run_id
    task_run_id
    transformation_execution_id
~~~

Provider tags are diagnostic aids.

They do not transfer execution ownership.

---

# 34. OpenTelemetry interoperability

The ecosystem MAY provide optional OpenTelemetry adapters.

Possible mappings include:

~~~text
execution boundaries → spans
structured events    → span events or logs
metrics              → OTel metrics
CorrelationContext   → safe attributes/context
~~~

The core model MUST NOT depend on OpenTelemetry.

Trace baggage SHOULD contain only small, non-sensitive values.

---

# 35. CLI and notebook observability

CLI execution SHOULD expose execution and correlation identifiers directly.

Users SHOULD NOT have to parse logs to discover them.

Machine-readable CLI output should use explicit versioned structures where stability matters.

Notebook execution SHOULD expose the same runtime evidence model:

~~~text
execution ID
status
diagnostics
explain information
output references
optional metrics summary
~~~

Interactive use must remain traceable.

---

# 36. Performance telemetry

Performance evidence MAY include:

~~~text
duration
bytes read
bytes written
rows processed when reliably known
memory usage when available
cache hit or miss
provider request count
~~~

Frameworks MUST NOT fabricate measurements unavailable from the engine.

Provider-reported, measured and estimated values SHOULD be distinguishable.

---

# 37. Cost telemetry

Adapters MAY expose provider cost-related evidence such as:

~~~text
bytes scanned
query duration
API call count
provider-reported credits
estimated compute cost
~~~

Estimated values MUST be labeled as estimates rather than exact billing truth.

---

# 38. Sampling and retention

High-volume logs, diagnostics and traces MAY be sampled.

Sampling MUST NOT remove:

- domain state required for recovery;
- reconciliation-critical evidence;
- explicitly audit-required records.

Retention may differ by signal:

~~~text
debug logs
metrics
traces
events
manifests
audit evidence
~~~

One retention period does not fit all telemetry.

---

# 39. Event schema evolution

Backward-compatible event changes MAY add optional fields.

Breaking changes include:

- changing required field meaning;
- removing required fields;
- changing identity semantics;
- changing event ownership;
- changing status meaning.

Breaking changes require event-version evolution.

Consumers SHOULD tolerate unknown optional fields when permitted by the contract.

---

# 40. Unknown events

Consumers SHOULD handle unknown event types safely.

Depending on role, they may:

~~~text
store or forward opaque event
ignore optional unknown event
reject when a strict known-event contract is required
~~~

Unknown telemetry events SHOULD NOT crash unrelated business execution by default.

---

# 41. Telemetry processor pipeline

A runtime MAY process records through:

~~~text
producer
    ↓
normalize
    ↓
enrich correlation
    ↓
redact
    ↓
filter or sample
    ↓
export
~~~

Redaction SHOULD happen before export to an external trust boundary.

Telemetry processors MUST avoid recursive failure loops.

---

# 42. Cross-framework aggregation

A shared operational UI may aggregate events into one timeline:

~~~text
WorkflowRunStarted W-42
TaskAttemptStarted TA-1
IngestionRunStarted I-288
DatasetVersionCreated customers@52
TaskAttemptSucceeded TA-1
TaskAttemptStarted TA-3
TransformationExecutionStarted T-913
TransformationExecutionSucceeded T-913
PublicationCompleted customer_mart@8
WorkflowRunSucceeded W-42
~~~

This timeline is a projection.

Native framework state remains authoritative.

---

# 43. Observability versus lineage

Telemetry may help produce lineage, but they are distinct.

~~~text
event
    says something happened

lineage
    says how objects are related
~~~

A TransformationOutputProduced event may contain references used to create a lineage relation.

The event itself is not the lineage graph.

---

# 44. Observability versus audit

Telemetry and audit overlap but are not identical.

Audit may require stronger guarantees around:

- actor identity;
- immutable retention;
- administrative reason;
- authorization decision;
- tamper resistance.

Telemetry events SHOULD NOT automatically be claimed as sufficient audit records.

---

# 45. Failure and uncertainty visualization

Operational tooling MUST distinguish:

~~~text
FAILED
TIMED_OUT
CANCELLED
UNKNOWN_OUTCOME
REQUIRES_RECONCILIATION
~~~

UNKNOWN_OUTCOME must not be visually collapsed into ordinary failure, because unsafe replay may result.

Failure views SHOULD preserve nested provenance rather than flatten everything into one text message.

---

# 46. Retry visualization

A retry view SHOULD show both workload and provider attempts.

Example:

~~~text
TaskRun TR-12
├── TaskAttempt 1
│   └── TransformationExecution T-912
│       └── provider attempts: 2
└── TaskAttempt 2
    └── TransformationExecution T-913
        └── provider attempts: 1
~~~

This makes nested retry behavior visible.

---

# 47. Health telemetry

Long-lived applications may expose:

~~~text
LIVENESS
READINESS
DEPENDENCY_HEALTH
~~~

Libraries themselves do not need to implement HTTP health endpoints.

Health presentation belongs to applications/platform adapters.

---

# 48. Multi-tenancy and security boundaries

If multi-tenancy is added, telemetry MUST prevent cross-tenant leakage.

Telemetry destinations and processors SHOULD support:

- tenant isolation;
- allowed attributes;
- redaction;
- secure transport;
- retention policy.

Sending telemetry to an external provider is an explicit deployment choice.

---

# 49. Testing requirements

Each framework SHOULD test:

- event envelope correctness;
- stable event namespaces;
- correlation propagation;
- causation propagation;
- redaction;
- no import-time telemetry activation;
- metric cardinality defaults;
- trace versus execution identity separation;
- diagnostics without external sink;
- telemetry sink failure isolation;
- concurrent context isolation;
- serialization of stable event contracts.

---

# 50. Cross-framework conformance tests

End-to-end scenarios SHOULD cover:

~~~text
WorkflowKit → IngestKit
WorkflowKit → TransformKit
IngestKit → TransformKit
TransformKit → IngestKit publication
~~~

For each flow, verify:

- CorrelationId is preserved;
- native execution IDs remain distinct;
- event ownership namespaces are correct;
- trace context propagates when enabled;
- failure origin survives adaptation;
- secrets are redacted;
- metrics avoid high-cardinality execution IDs by default;
- unknown outcomes remain observable as uncertainty.

---

# 51. Golden telemetry contracts

Stable releases SHOULD maintain representative serialized fixtures for stable public events and diagnostics.

Golden fixtures help detect accidental changes in:

~~~text
event type
event version
required fields
identity fields
enum values
owner namespace
diagnostic codes
~~~

Internal transient events need not be frozen as public contracts.

---

# 52. Metric contract testing

Stable exported metrics SHOULD test:

~~~text
name
type
unit
allowed labels
cardinality constraints
status and failure dimensions
~~~

Changing metric meaning while keeping the same metric name is prohibited.

---

# 53. Acceptance criteria

This specification is implemented correctly when:

1. Event, Log, Metric, Trace, Diagnostic and Manifest remain distinct concepts;
2. event names reveal bounded-context ownership;
3. EventId remains distinct from execution identity;
4. CorrelationId propagates across sibling boundaries;
5. TraceId never replaces native execution IDs;
6. core domains do not depend on telemetry vendors;
7. package import has no telemetry side effects;
8. result diagnostics work without an external telemetry backend;
9. structured logs carry relevant execution context;
10. secrets are redacted before export;
11. raw datasets are not emitted by default;
12. metric labels avoid high-cardinality execution IDs by default;
13. retry metrics distinguish owner and scope;
14. UNKNOWN_OUTCOME is observable separately from FAILED;
15. lazy engines do not fabricate unsupported timing granularity;
16. telemetry sink failure cannot replay business work;
17. event delivery semantics are documented;
18. correlation context remains isolated under concurrency;
19. external aggregation remains a projection over native state;
20. observability conformance tests run in CI.

---

# 54. Normative invariants

### OBS-INV-01 — Telemetry is evidence, not domain state

Observability records do not replace native framework state.

### OBS-INV-02 — Event ownership is bounded-context specific

Shared sinks do not flatten semantic ownership.

### OBS-INV-03 — Correlation propagates while execution identity remains local

One correlation story may contain many native runtime IDs.

### OBS-INV-04 — Trace identity is observational

TraceId and SpanId never substitute for durable domain IDs.

### OBS-INV-05 — Metrics control cardinality

High-cardinality execution identifiers are excluded from default labels.

### OBS-INV-06 — Telemetry is secret-safe

Sensitive values are redacted before export.

### OBS-INV-07 — Telemetry is optional for core correctness

Business execution works without an external telemetry platform.

### OBS-INV-08 — Import has no telemetry side effects

No exporter, thread, socket or metrics server starts during import.

### OBS-INV-09 — Runtime granularity is honest

Frameworks do not fabricate measurements unsupported by runtime evidence.

### OBS-INV-10 — Telemetry failure remains in telemetry scope

Exporter retry never retries the underlying business operation.

### OBS-INV-11 — Uncertainty remains observable

Unknown outcome is not coerced into generic failure for monitoring convenience.

### OBS-INV-12 — External aggregation is a projection

Native bounded-context stores remain authoritative.

---

# 55. Canonical observability flow

~~~text
Domain or Runtime Transition
        ↓
Structured Evidence
        ├── Event
        ├── Log
        ├── Metric update
        ├── Trace span/event
        ├── Diagnostic
        └── Manifest

Relevant signals carry:

CorrelationId
CausationId
Native Execution ID
Framework ownership
Portable references
Safe structured metadata
~~~

No observability signal replaces the underlying domain state.

---

# 56. Final architecture statement

The PyKit V2 ecosystem should be observable without becoming observability-driven.

Its shared grammar is:

~~~text
Events
    explain transitions

Logs
    explain diagnostics

Metrics
    explain aggregate behavior

Traces
    explain distributed timing

Diagnostics
    explain decisions and anomalies

Manifests
    preserve durable execution evidence
~~~

These signals are joined through correlation, causation, native execution identity and portable references while preserving bounded-context ownership.

The central rule is:

> **Emit enough structured evidence to explain an execution end-to-end, but never let telemetry become the hidden owner of state, identity or semantics.**

This specification is the baseline for:

~~~text
PYKIT_ECOSYSTEM_V2_INTEGRATION_AND_ANTI_CORRUPTION_LAYER_MODEL.md
PYKIT_ECOSYSTEM_V2_DEPENDENCY_PACKAGING_AND_OPTIONAL_EXTRAS_STRATEGY.md
PYKIT_ECOSYSTEM_V2_SERIALIZATION_AND_WIRE_CONTRACTS.md
PYKIT_ECOSYSTEM_V2_ARCHITECTURE_CONFORMANCE_AND_TEST_STRATEGY.md
~~~
