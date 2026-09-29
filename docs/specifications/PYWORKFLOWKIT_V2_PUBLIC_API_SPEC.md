# PyWorkflowKit V2 — Public API Specification

> **Status:** NORMATIVE PUBLIC API BASELINE  
> **Target release:** PyWorkflowKit 2.0.0  
> **Date:** 2026-09-29  
> **Architecture generation:** PyKit Ecosystem V2  
> **Tagline:** Reliable workflows without running a workflow platform.  
> **Depends on:** PYWORKFLOWKIT_V2_TARGET_ARCHITECTURE.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_DECLARATION_PLAN_RUNTIME_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_RELEASE_COMPATIBILITY_AND_VERSIONING_POLICY.md

---

# 1. Purpose

This document freezes the target public Python API of PyWorkflowKit 2.0.

It defines stable vocabulary, import paths, workflow and task authoring, planning, runtime execution, execution identities, state inspection, retry, timeout, cancellation, executors, metadata stores, recovery, reconciliation, results, diagnostics, exceptions, serialization, plugins and sibling-framework integrations.

> **The public API must make workflow intent declarative, execution state explicit, retry and recovery observable, and sibling runtimes opaque behind portable contracts.**

---

# 2. Canonical user flow

The canonical lifecycle is:

~~~text
declare TaskDefinition values
        ↓
build WorkflowDefinition
        ↓
compile to ExecutionPlan when inspection is useful
        ↓
WorkflowRuntime.run(...)
        ↓
WorkflowRun
    └── TaskRun
          └── TaskAttempt
        ↓
WorkflowResult
~~~

Compilation is optional for the common path because WorkflowRuntime MAY plan internally.

---

# 3. Canonical package-root imports

PyWorkflowKit 2.0 SHOULD support:

~~~python
from pyworkflowkit import (
    ExecutionPlan,
    RetryPolicy,
    TaskAttempt,
    TaskAttemptId,
    TaskDefinition,
    TaskRun,
    TaskRunId,
    TimeoutPolicy,
    WorkflowDefinition,
    WorkflowResult,
    WorkflowRun,
    WorkflowRunId,
    WorkflowRuntime,
)
~~~

The root surface remains curated.

---

# 4. Stable root surface

The following categories are intended to be STABLE at 2.0:

~~~text
WorkflowDefinition
TaskDefinition
ExecutionPlan
WorkflowRuntime

WorkflowRun / WorkflowRunId
TaskRun / TaskRunId
TaskAttempt / TaskAttemptId

WorkflowResult
RetryPolicy
TimeoutPolicy

selected state enums
selected references
selected public exceptions
~~~

Private graph structures, executor internals, persistence entities and plugin-loader implementation types are not root exports.

---

# 5. Qualified public namespaces

Stable or intentionally public namespaces SHOULD include:

~~~text
pyworkflowkit.authoring
pyworkflowkit.planning
pyworkflowkit.runtime
pyworkflowkit.states
pyworkflowkit.policies
pyworkflowkit.executors
pyworkflowkit.persistence
pyworkflowkit.serialization
pyworkflowkit.lineage
pyworkflowkit.diagnostics
pyworkflowkit.plugins
pyworkflowkit.integrations.pyingestkit
pyworkflowkit.integrations.pytransformkit
~~~

Provider-specific or advanced executor implementations live under qualified namespaces.

---

# 6. Import-time safety

Importing pyworkflowkit MUST NOT:

- launch work;
- create threads or processes;
- open databases;
- resolve credentials;
- activate plugins;
- import sibling frameworks;
- start telemetry exporters;
- mutate mandatory global registries;
- recover unfinished workflows automatically.

Core import must succeed with base dependencies only.

---

# 7. Constructor safety

Public domain constructors MUST be side-effect free.

Constructing WorkflowDefinition, TaskDefinition, RetryPolicy, TimeoutPolicy or ExecutionPlan declarations MUST NOT launch workloads, create WorkflowRun identities or connect to metadata stores.

Runtime effects begin only through explicit planning or run operations.

---

# 8. WorkflowDefinition

WorkflowDefinition is the canonical authoring root.

The preferred ergonomic style MAY use a builder:

~~~python
workflow = WorkflowDefinition.builder(
    name="customer_360",
)
~~~

The builder is authoring convenience, not a separate semantic architecture layer.

---

# 9. WorkflowDefinitionBuilder

WorkflowDefinitionBuilder MAY be public under pyworkflowkit.authoring while remaining absent from root exports.

build() returns an immutable canonical WorkflowDefinition.

Builder mutation is allowed for ergonomics; the built definition is immutable.

---

# 10. TaskDefinition

TaskDefinition represents one workload boundary.

Representative direct construction:

~~~python
task = TaskDefinition(
    key="ingest_customers",
    workload=workload,
)
~~~

In builder-based authoring, builder.task MAY create TaskDefinition values.

---

# 11. TaskDefinition stable properties

Stable properties SHOULD include:

~~~text
key
workload
dependencies
retry_policy
timeout_policy
trigger_rule / condition
input declarations
output declarations
metadata
~~~

TaskDefinition contains no current attempt ID, provider run ID or mutable execution state.

---

# 12. Task key semantics

Task keys are unique within a WorkflowDefinition.

Task keys are stable authoring identities and MAY appear in:

~~~text
dependency declarations
ExecutionPlan
TaskRun records
diagnostics
manifests
events
~~~

Changing a task key changes workflow authoring semantics and may change workflow fingerprints.

---

# 13. Workload declaration

TaskDefinition workload may represent:

~~~text
trusted local callable
async callable
subprocess command descriptor
registered executor workload descriptor
PyIngestKit ingestion workload
PyTransformKit transformation workload
external provider workload descriptor
~~~

The workload form does not change WorkflowKit ownership of TaskRun and TaskAttempt semantics.

---

# 14. Portable workload descriptors

Portable workload descriptors SHOULD be immutable schema-driven values.

A portable workload descriptor MUST NOT require arbitrary Python object reconstruction.

Representative portable descriptors include:

~~~text
registered callable ID + validated parameters
subprocess executable + argv
PyIngestKit IngestionDefinition reference/payload
PyTransformKit TransformationPlan reference/payload
external provider job descriptor
~~~

---

# 15. Local callable workload

A trusted Python callable MAY be accepted for local execution.

Representative authoring:

~~~python
def refresh_cache():
    ...

task = TaskDefinition(
    key="refresh_cache",
    workload=refresh_cache,
)
~~~

Such a callable is process-local unless explicitly registered through a portable workload registry.

The framework MUST NOT imply durable portability for arbitrary closures or lambdas.

---

# 16. Decorator ergonomics

Decorators MAY be supported:

~~~python
from pyworkflowkit import task

@task(
    retry=RetryPolicy(
        max_attempts=3,
    ),
)
def ingest():
    ...
~~~

and:

~~~python
from pyworkflowkit import workflow

@workflow
def customer_360():
    ...
~~~

Decorators are syntax sugar and MUST compile into canonical TaskDefinition and WorkflowDefinition values.

They MUST NOT create a parallel runtime model.

---

# 17. Workflow dependencies

Dependencies SHOULD be explicit.

Builder example:

~~~python
ingest_customers = builder.task(
    "ingest_customers",
    workload=customers_workload,
)

ingest_orders = builder.task(
    "ingest_orders",
    workload=orders_workload,
)

transform = builder.task(
    "transform",
    workload=transform_workload,
    depends_on=(
        ingest_customers,
        ingest_orders,
    ),
)
~~~

Dependencies represent workload ordering, not automatic data lineage.

---

# 18. Dependency declarations by key

An alternate stable form MAY use keys:

~~~python
builder.task(
    "publish",
    workload=publish_workload,
    depends_on=(
        "transform",
    ),
)
~~~

Unknown dependency keys fail validation.

---

# 19. No public WorkflowGraph requirement

Users MUST NOT be required to construct a WorkflowGraph or DependencyGraph.

WorkflowDefinition owns declared topology.

Internal graph representations remain implementation details.

---

# 20. WorkflowDefinition inspection

Stable properties SHOULD include:

~~~text
name
tasks
metadata
~~~

Stable methods SHOULD include:

~~~python
workflow.validate()
workflow.fingerprint()
workflow.explain()
~~~

validate performs structural and semantic validation only.

---

# 21. WorkflowDefinition immutability

WorkflowDefinition is immutable after build.

Runtime execution MUST NOT mutate task dependencies, policies or authoring metadata.

Executing the same definition multiple times creates separate WorkflowRun identities.

---

# 22. RetryPolicy

RetryPolicy is an immutable workload-retry declaration.

Representative API:

~~~python
retry = RetryPolicy(
    max_attempts=3,
    backoff="exponential",
    initial_delay=1.0,
    max_delay=30.0,
)
~~~

Exact policy fields MAY use typed duration/backoff values.

---

# 23. RetryPolicy stable semantics

RetryPolicy SHOULD represent at least:

~~~text
maximum attempts
backoff strategy
initial delay
maximum delay
jitter policy
retryable failure categories
total retry budget / deadline when configured
reconciliation requirement
~~~

Retry matching MUST use structured failure semantics, not raw message regex as the primary contract.

---

# 24. Backoff strategy

Backoff SHOULD use typed values or stable strategy classes/enums.

Representative forms:

~~~text
NONE
FIXED
LINEAR
EXPONENTIAL
~~~

Custom backoff MAY be provisional or qualified.

Runtime diagnostics should expose the computed retry decision and delay.

---

# 25. TimeoutPolicy

TimeoutPolicy is an immutable declaration.

Representative API:

~~~python
timeout = TimeoutPolicy(
    execution_timeout=300.0,
)
~~~

Timeout semantics MUST distinguish local waiting deadline from confirmed external termination.

---

# 26. Trigger rules

Task readiness MAY use typed trigger rules.

Stable concepts SHOULD include semantics equivalent to:

~~~text
ALL_SUCCESS
ALL_DONE
ANY_SUCCESS
ANY_FAILED
NONE_FAILED
ALWAYS
~~~

Exact names are frozen by conformance tests.

Trigger rules evaluate upstream TaskRun terminal states, not provider internals.

---

# 27. Conditions

Conditional task execution MAY be represented by portable condition descriptors or trusted local predicates.

A condition result may cause SKIPPED without implying workload failure.

Portable conditions MUST be non-executable wire contracts unless intentionally registered by trusted code.

---

# 28. Workflow planning

Public planning lives under pyworkflowkit.planning.

Representative API:

~~~python
from pyworkflowkit.planning import (
    WorkflowPlanner,
)

planner = WorkflowPlanner()

plan = planner.compile(
    workflow
)
~~~

compile and plan are semantic equivalents when exposed; one canonical public verb SHOULD be selected for stable API.

---

# 29. Preferred planning verb

The preferred stable verb is compile:

~~~python
plan = planner.compile(
    workflow
)
~~~

because it maps user declaration into an executable representation without running work.

A plan alias MAY exist only if it does not create vocabulary ambiguity.

---

# 30. ExecutionPlan

ExecutionPlan is the public compiled workflow representation.

Stable inspection SHOULD expose:

~~~text
workflow name
task plan entries
validated topology
topological order
effective retry policies
effective timeout policies
trigger rules
executor requirements
required integrations
diagnostics
fingerprint
~~~

ExecutionPlan contains no WorkflowRunId or attempt state.

---

# 31. ExecutionPlan inspection

Representative API:

~~~python
plan.explain()
plan.fingerprint()
plan.topological_order
plan.required_capabilities
plan.diagnostics
~~~

explain performs no workload execution.

---

# 32. ExecutionPlan determinism

For the same WorkflowDefinition and planner configuration:

~~~text
same semantic definition
    → same deterministic ExecutionPlan semantics
    → same plan fingerprint
~~~

Incidental dictionary ordering, process ID or memory address MUST NOT affect planning semantics.

---

# 33. Runtime construction

Canonical runtime construction SHOULD use dependency injection:

~~~python
runtime = WorkflowRuntime(
    executor=executor,
    metadata=metadata_store,
)
~~~

The runtime MAY additionally accept:

~~~text
executor registry
telemetry
clock
ID generator
plugin registry
integration registry
credential resolver
~~~

Hidden mandatory global singletons are prohibited.

---

# 34. Runtime run API

Canonical execution:

~~~python
result = runtime.run(
    workflow,
    correlation=correlation,
)
~~~

WorkflowRuntime.run SHOULD also accept ExecutionPlan:

~~~python
result = runtime.run(
    plan,
    correlation=correlation,
)
~~~

The two paths preserve equivalent execution semantics.

---

# 35. Runtime explicitness

run MUST NOT silently:

- select arbitrary remote schedulers;
- install plugins;
- activate sibling integrations;
- choose an unavailable executor fallback;
- retry uncertain side effects blindly;
- discard existing recovery state.

Runtime behavior is determined by explicit configuration and task policies.

---

# 36. WorkflowRunId

WorkflowRunId is an immutable typed identifier.

It SHOULD support:

~~~python
str(run_id)
WorkflowRunId.parse(value)
~~~

Each independent workflow execution receives a new WorkflowRunId.

Recovery preserves the existing ID.

---

# 37. TaskRunId

TaskRunId identifies one logical task execution within one WorkflowRun.

A TaskRunId remains stable across retries of that task.

TaskRun identity is distinct from TaskDefinition key.

---

# 38. TaskAttemptId

TaskAttemptId identifies one concrete attempt.

Each retry creates a new TaskAttemptId.

Representative hierarchy:

~~~text
WorkflowRunId W
    └── TaskRunId T
          ├── TaskAttemptId A1
          ├── TaskAttemptId A2
          └── TaskAttemptId A3
~~~

---

# 39. WorkflowRun

WorkflowRun is the public durable/inspectable runtime record.

Stable or semi-stable properties SHOULD include:

~~~text
id
status
definition fingerprint
plan fingerprint
correlation
task runs
failure
diagnostics
timestamps
manifest reference
~~~

Private persistence fields need not be public.

---

# 40. TaskRun

TaskRun represents one logical task execution.

Stable properties SHOULD include:

~~~text
id
task_key
status
attempts
selected output references
failure summary
timestamps
~~~

TaskRun is not replaced when retry occurs.

---

# 41. TaskAttempt

TaskAttempt represents one concrete workload attempt.

Stable properties SHOULD include:

~~~text
id
task_run_id
attempt_number
status
executor
external_runs
outputs
failure
diagnostics
started_at
ended_at
~~~

TaskAttempt preserves uncertainty and cancellation state when needed.

---

# 42. State enums

Public state enums SHOULD distinguish authoring-independent runtime semantics.

Candidate stable WorkflowRunStatus values:

~~~text
PENDING
RUNNING
SUCCEEDED
FAILED
CANCELLATION_REQUESTED
CANCELLED
TIMED_OUT
UNKNOWN_OUTCOME
~~~

Exact transitional values may be refined before implementation freeze.

---

# 43. TaskRunStatus

Candidate stable semantics:

~~~text
PENDING
READY
RUNNING
SUCCEEDED
FAILED
SKIPPED
CANCELLED
TIMED_OUT
BLOCKED
UNKNOWN_OUTCOME
~~~

TaskRun status summarizes logical task state across attempts.

---

# 44. TaskAttemptStatus

Candidate stable semantics:

~~~text
PENDING
STARTING
RUNNING
SUCCEEDED
FAILED
TIMED_OUT
CANCELLATION_REQUESTED
CANCELLED
CANCELLATION_UNCONFIRMED
UNKNOWN_OUTCOME
REQUIRES_RECONCILIATION
~~~

Uncertainty MUST remain representable.

---

# 45. State transition APIs

Consumers SHOULD normally not mutate states directly.

State transitions belong to WorkflowRuntime and state-machine services.

If advanced administrative APIs exist, they MUST use validated commands rather than arbitrary property assignment.

Rejected pattern:

~~~text
attempt.status = SUCCEEDED
~~~

---

# 46. Result model

WorkflowResult is the caller-facing immutable outcome.

It SHOULD expose:

~~~text
run_id
status
task outcomes
portable outputs
diagnostics
failure
correlation
manifest reference
~~~

WorkflowResult remains smaller than full persisted WorkflowRun state.

---

# 47. Task outcome summary

WorkflowResult SHOULD provide task outcome lookup:

~~~python
outcome = result.task(
    "transform"
)

outcome.status
outcome.outputs
outcome.failure
~~~

Task outcome is a read-only projection, not TaskRun mutation API.

---

# 48. Durable outputs

Durable task outputs SHOULD be:

~~~text
small JSON-compatible values
ResourceReference
ArtifactReference
DatasetVersionReference
IngestionExecutionReference
TransformationExecutionReference
ExternalRunRef
other versioned portable references
~~~

Large native DataFrames, open connections, subprocess objects and provider clients MUST NOT become durable task output state.

---

# 49. Process-local outputs

A local executor MAY expose process-local convenience outputs for immediate callers.

Such values MUST be explicitly marked non-portable and MUST NOT be required for durable recovery.

---

# 50. ExternalRunRef

ExternalRunRef is the stable portable link to execution owned outside WorkflowKit.

Representative construction is provider/integration-owned rather than manually required by users.

Stable properties SHOULD include:

~~~text
provider/framework
execution kind
external execution ID
status hint when available
correlation/causation metadata
portable locator/reference data
~~~

Possessing ExternalRunRef does not imply cancellation authority.

---

# 51. External execution list

A TaskAttempt MAY expose:

~~~python
attempt.external_runs
~~~

as an immutable sequence of ExternalRunRef values.

Zero external runs is valid for purely local workloads.

---

# 52. Retry decision API

Retry evaluation SHOULD return a typed decision.

Representative values:

~~~text
RETRY
DO_NOT_RETRY
RECONCILE
ABORT
CANCEL
ESCALATE
~~~

A RetryDecision SHOULD carry reason, delay and policy evidence.

---

# 53. Retry execution semantics

When a retry decision is RETRY:

~~~text
same TaskRunId
    ↓
new TaskAttemptId
    ↓
new workload execution
~~~

If the workload is PyIngestKit or PyTransformKit, the new attempt generally produces a new native sibling execution ID.

---

# 54. UNKNOWN_OUTCOME retry rule

If a TaskAttempt ends with uncertain external side-effect status:

~~~text
UNKNOWN_OUTCOME
    ↓
RECONCILE
    ↓
only then decide retry / success / failure
~~~

The public runtime MUST NOT silently schedule a retry first.

---

# 55. Timeout semantics

Timeout means the local runtime exceeded a configured deadline.

Timeout MAY result in:

~~~text
confirmed cancellation
cancellation requested
external work still running
unknown outcome
reconciliation required
~~~

Timeout is therefore not identical to failure.

---

# 56. Cancellation API

Representative API:

~~~python
runtime.cancel(
    workflow_run_id
)
~~~

or:

~~~python
runtime.cancel_task(
    task_run_id
)
~~~

Exact administrative method shape may be refined, but cancellation request and cancellation confirmation remain distinct semantics.

---

# 57. Cancellation result

A cancellation command SHOULD return structured status such as:

~~~text
REQUESTED
CONFIRMED
UNSUPPORTED
UNCONFIRMED
ALREADY_TERMINAL
~~~

A boolean is insufficient for all cases.

---

# 58. Recovery API

Recovery is explicit.

Representative API:

~~~python
result = runtime.recover(
    workflow_run_id
)
~~~

Recovery reloads durable state and reconciles existing work.

It does not automatically create a new WorkflowRunId.

---

# 59. Recovery discovery

MetadataStore or runtime MAY provide discovery:

~~~python
unfinished = runtime.list_recoverable()
~~~

or equivalent.

Automatic recovery at package import time is prohibited.

---

# 60. Reconciliation API

Representative forms:

~~~python
result = runtime.reconcile(
    workflow_run_id
)
~~~

and optionally:

~~~python
attempt = runtime.reconcile_attempt(
    task_attempt_id
)
~~~

Reconciliation uses persisted ExternalRunRef and provider/integration capabilities.

---

# 61. Recovery versus rerun

The public API MUST preserve:

~~~text
recover(existing WorkflowRunId)
    !=
run(WorkflowDefinition)
~~~

run creates new workflow execution identity.

recover continues existing workflow execution identity.

---

# 62. Rerun API

A convenience rerun MAY exist:

~~~python
new_result = runtime.rerun(
    workflow_run_id
)
~~~

If exposed, rerun creates a new WorkflowRunId and records causal/origin relationship.

It MUST NOT be confused with recovery.

---

# 63. Executor Protocol

The stable executor extension Protocol SHOULD conceptually expose:

~~~python
class Executor(Protocol):

    @property
    def descriptor(
        self,
    ) -> ExecutorDescriptor:
        ...

    def execute(
        self,
        request: TaskExecutionRequest,
    ) -> TaskExecutionResult:
        ...

    def cancel(
        self,
        request: TaskCancellationRequest,
    ) -> TaskCancellationResult:
        ...

    def reconcile(
        self,
        request: TaskReconciliationRequest,
    ) -> TaskReconciliationResult:
        ...
~~~

cancel and reconcile may be capability-dependent.

---

# 64. ExecutorDescriptor

ExecutorDescriptor SHOULD expose:

~~~text
id
display_name
executor_version
capabilities
execution modes
portability constraints
~~~

Published executor IDs become compatibility surfaces.

---

# 65. ExecutorRegistry

When multiple executors are configured, registration SHOULD be explicit:

~~~python
from pyworkflowkit.executors import (
    ExecutorRegistry,
)

registry = ExecutorRegistry()

registry.register(
    InlineExecutor()
)

registry.register(
    ThreadExecutor()
)
~~~

Importing an executor must not mutate mandatory global state.

---

# 66. Executor selection

TaskDefinition MAY explicitly select an executor:

~~~python
task = TaskDefinition(
    key="transform",
    workload=workload,
    executor="thread",
)
~~~

or runtime policy MAY select one according to explicit declared capabilities.

Installed-package presence alone MUST NOT silently determine executor semantics.

---

# 67. InlineExecutor

InlineExecutor SHOULD be the baseline local executor.

Stable import:

~~~python
from pyworkflowkit.executors import (
    InlineExecutor,
)
~~~

It executes trusted local workloads in the current process and provides the reference semantics for state-machine conformance.

---

# 68. ThreadExecutor

ThreadExecutor MAY be a stable V2 executor if conformance is green.

Representative import:

~~~python
from pyworkflowkit.executors import (
    ThreadExecutor,
)
~~~

Its documentation MUST state cancellation limitations and thread-safety requirements.

---

# 69. ProcessExecutor

ProcessExecutor MAY be stable or provisional depending on serialization and cancellation conformance.

It MUST NOT require durable workflow state to be arbitrary pickled Python objects.

Process-local transport mechanics remain implementation details.

---

# 70. AsyncExecutor

AsyncExecutor MAY support coroutine workloads.

Async execution uses the same TaskAttempt state model.

It does not create separate retry or recovery semantics.

---

# 71. SubprocessExecutor

Representative import:

~~~python
from pyworkflowkit.executors import (
    SubprocessExecutor,
)
~~~

Subprocess workload descriptors SHOULD use executable plus argv.

Shell mode requires explicit opt-in.

---

# 72. Subprocess workload descriptor

Representative portable workload:

~~~python
from pyworkflowkit.executors import (
    SubprocessCommand,
)

workload = SubprocessCommand(
    executable="python",
    args=(
        "-m",
        "my_app.job",
    ),
)
~~~

Environment variables, working directory and output limits are explicit runtime configuration.

---

# 73. MetadataStore Protocol

The stable persistence port SHOULD conceptually expose operations for:

~~~text
create/read/update WorkflowRun
create/read/update TaskRun
append/read TaskAttempt
persist ExternalRunRef
validated state transition
query unfinished runs
persist/retrieve manifests
schema/version inspection
~~~

Exact transactional methods are frozen during implementation.

---

# 74. Metadata store construction

Store implementations live in qualified namespaces.

Representative local durable store:

~~~python
from pyworkflowkit.persistence.sqlite import (
    SQLiteMetadataStore,
)

metadata = SQLiteMetadataStore(
    "./workflow.db"
)
~~~

The store constructor SHOULD avoid expensive external actions beyond explicit local initialization policy.

---

# 75. InMemoryMetadataStore

Stable or reference import:

~~~python
from pyworkflowkit.persistence.memory import (
    InMemoryMetadataStore,
)
~~~

It is suitable for tests and simple local execution.

It does not claim crash recovery.

---

# 76. SQLiteMetadataStore

SQLite is the preferred local durable reference implementation.

It SHOULD support:

~~~text
durable WorkflowRun state
TaskRun state
attempt history
ExternalRunRef
restart recovery
schema migration
Customer 360 local profile
~~~

---

# 77. PostgreSQLMetadataStore

PostgreSQL MAY be available behind an optional extra such as:

~~~text
pip install pyworkflowkit[postgres]
~~~

Representative import MAY be:

~~~python
from pyworkflowkit.persistence.postgres import (
    PostgreSQLMetadataStore,
)
~~~

PostgreSQL schema details remain infrastructure-private.

---

# 78. Atomic state transition API

MetadataStore implementations MUST protect state transitions.

Advanced store APIs SHOULD expose conditional update/version semantics rather than arbitrary overwrite.

Critical state MUST NOT use last-write-wins without concurrency protection when concurrent runtimes are supported.

---

# 79. Runtime persistence policy

WorkflowRuntime SHOULD persist state at semantic boundaries such as:

~~~text
WorkflowRun created
TaskRun readiness change
TaskAttempt created
external execution reference obtained
TaskAttempt terminal/uncertain update
retry scheduled
WorkflowRun terminal update
~~~

This enables recovery without pretending that logs are authoritative state.

---

# 80. Manifest API

Workflow manifests SHOULD be available through versioned contracts.

Representative access:

~~~python
manifest_ref = result.manifest
~~~

A manifest SHOULD capture:

~~~text
WorkflowRunId
definition fingerprint
ExecutionPlan fingerprint
CorrelationContext
TaskRun summaries
TaskAttempt references
ExternalRunRef values
terminal status
FailureEvidence
timestamps
contract version
~~~

Raw secrets and active handles are prohibited.

---

# 81. Diagnostics

A structured Diagnostic SHOULD include:

~~~text
code
severity
summary
details
workflow/task/attempt context
decision context
related policy
~~~

Diagnostic codes used by automation become compatibility contracts.

---

# 82. Exception hierarchy

Target public hierarchy:

~~~text
PyWorkflowKitError
    DefinitionValidationError
    PlanningError
    StateTransitionError
    ExecutorCapabilityError
    ExecutionError
    PersistenceError
    RecoveryError
    ReconciliationError
    SerializationError
    PluginError
    IntegrationError
~~~

Exact class names may be adjusted before freeze, but the semantic hierarchy is normative.

---

# 83. Structured exception evidence

Operational exceptions SHOULD expose:

~~~text
category
code
failure_evidence
workflow_run_id when allocated
task_run_id when relevant
task_attempt_id when relevant
correlation
diagnostics
cause
~~~

Executor/provider-native exceptions may remain available as cause without becoming stable semantic contracts.

---

# 84. FailureEvidence

FailureEvidence follows the shared ecosystem contract.

WorkflowKit SHOULD preserve provider/sibling failure category, retryability, uncertainty and native execution reference.

Adapters MUST NOT flatten provider truth into generic string errors.

---

# 85. Execution lineage API

Workflow execution lineage SHOULD be queryable under pyworkflowkit.lineage.

Representative concepts:

~~~text
WorkflowRun
    → TaskRun
    → TaskAttempt
    → ExternalRunRef
~~~

Workflow dependency alone does not automatically imply data lineage.

---

# 86. Task output lineage

WorkflowKit MAY record portable input/output references associated with TaskAttempt.

This is execution lineage.

It does not replace PyIngestKit provenance or PyTransformKit field lineage.

---

# 87. Serialization API

Portable serialization uses explicit codecs.

Representative API:

~~~python
from pyworkflowkit.serialization import (
    ExecutionPlanCodec,
    WorkflowDefinitionCodec,
    WorkflowManifestCodec,
)

payload = (
    WorkflowDefinitionCodec
    .to_json(workflow)
)

workflow2 = (
    WorkflowDefinitionCodec
    .from_json(payload)
)
~~~

All stable payloads contain contract and contract_version.

---

# 88. Portable WorkflowDefinition restrictions

WorkflowDefinitionCodec MUST reject or explicitly mark definitions containing non-portable workloads such as:

~~~text
anonymous lambda
closure capturing process state
open connection
thread/process object
unregistered local callable
raw secret
provider SDK client
~~~

Serialization never falls back to pickle-like durable contracts.

---

# 89. ExecutionPlan serialization

ExecutionPlanCodec MAY be stable when plan semantics are portable.

It MUST preserve deterministic topology, effective policies, executor requirements and fingerprint.

It MUST NOT serialize WorkflowRun state.

---

# 90. Runtime state serialization

Durable WorkflowRun/TaskRun/TaskAttempt state uses schema-driven persistence/wire contracts.

Recovery MUST NOT require arbitrary Python module/class reconstruction.

---

# 91. Plugin API

Discovery and activation are separate.

Representative usage:

~~~python
from pyworkflowkit.plugins import (
    PluginRegistry,
)

plugins = (
    PluginRegistry
    .discover()
)

plugins.activate(
    "my-executor-plugin"
)
~~~

Discovery alone does not grant execution authority.

---

# 92. Plugin categories

Stable plugin categories MAY include:

~~~text
Executor
MetadataStore
telemetry sink
external workload adapter
policy provider when explicitly supported
~~~

Plugins declare protocol/package compatibility.

---

# 93. Optional extras

Candidate extras include:

~~~text
[postgres]
[otel]
[ingest]
[transform]
~~~

Base pyworkflowkit import must not require any sibling framework.

---

# 94. PyIngestKit integration install

Official optional integration SHOULD use:

~~~text
pip install pyworkflowkit[ingest]
~~~

The integration lives under:

~~~text
pyworkflowkit.integrations.pyingestkit
~~~

---

# 95. PyIngestKit workload authoring

Representative integration authoring MAY be:

~~~python
from pyworkflowkit.integrations.pyingestkit import (
    IngestionWorkload,
)

ingest_task = TaskDefinition(
    key="ingest_customers",
    workload=IngestionWorkload(
        definition=customers_ingestion,
    ),
)
~~~

Exact class names are finalized after implementation evidence.

The semantic boundary is stable.

---

# 96. PyIngestKit execution mapping

Canonical runtime mapping:

~~~text
TaskAttempt
    ↓
IngestionWorkload
    ↓
IngestionRuntime.run
    ↓
IngestionRun
    ↓
IngestionExecutionReference
    ↓
ExternalRunRef
~~~

WorkflowKit does not inspect acquisition, RAW, decode, DatasetVersion or publication internals.

---

# 97. PyTransformKit integration install

Official optional integration SHOULD use:

~~~text
pip install pyworkflowkit[transform]
~~~

The integration lives under:

~~~text
pyworkflowkit.integrations.pytransformkit
~~~

---

# 98. PyTransformKit workload authoring

Representative form MAY be:

~~~python
from pyworkflowkit.integrations.pytransformkit import (
    TransformationWorkload,
)

transform_task = TaskDefinition(
    key="transform",
    workload=TransformationWorkload(
        plan=transformation_plan,
        engine="polars",
    ),
)
~~~

Exact helper names are refined after Customer 360 implementation.

---

# 99. PyTransformKit execution mapping

Canonical runtime mapping:

~~~text
TaskAttempt
    ↓
TransformationWorkload
    ↓
TransformationRuntime.execute
    ↓
TransformationExecution
    ↓
TransformationExecutionReference
    ↓
ExternalRunRef
~~~

WorkflowKit does not inspect or schedule TransformationPlan nodes.

---

# 100. Sibling retry boundary

The integration API MUST preserve:

~~~text
WorkflowKit retry
    → new TaskAttempt
    → normally new sibling execution

sibling internal retry
    → same sibling execution identity
~~~

Recovery may reconnect to existing sibling execution through ExternalRunRef.

---

# 101. Sibling uncertainty boundary

If PyIngestKit or PyTransformKit returns UNKNOWN_OUTCOME:

~~~text
sibling UNKNOWN_OUTCOME
    ↓
WorkflowKit TaskAttempt uncertainty
    ↓
reconcile through integration
~~~

The adapter MUST NOT map uncertainty to ordinary FAILED solely for convenience.

---

# 102. Sibling cancellation boundary

WorkflowKit MAY request cancellation when the sibling runtime exposes a supported cancellation API.

The adapter preserves:

~~~text
requested
confirmed
unsupported
unconfirmed
~~~

Cancellation authority is explicit and not implied by possession of ExternalRunRef.

---

# 103. Security

PyWorkflowKit follows the ecosystem trust baseline.

It MUST preserve:

~~~text
identity != authorization
explicit executable-code surfaces
CredentialReference instead of raw secrets
non-executable durable serialization
explicit plugin activation
controlled subprocess execution
redacted telemetry
reference possession != control authority
~~~

---

# 104. Credential handling

WorkflowDefinition, ExecutionPlan, manifests and ExternalRunRef MUST NOT embed raw secret values.

Task workloads may reference credentials through CredentialReference or deployment-specific runtime binding.

Credential resolution occurs at execution boundaries.

---

# 105. Subprocess security

Subprocess APIs SHOULD default to executable + argv.

Shell execution requires explicit opt-in.

Environment forwarding MUST be configurable.

stdout/stderr capture MUST be bounded and subject to redaction.

Subprocess execution is not described as a full sandbox.

---

# 106. Thread/process safety

Every stable runtime service, executor and MetadataStore documents:

~~~text
thread safety
process safety
async compatibility
resource ownership
cleanup semantics
concurrent update behavior
~~~

Normal use must not require hidden global mutable runtime state.

---

# 107. Clock API

Time-dependent behavior SHOULD use an injectable clock abstraction.

Representative testing setup:

~~~python
runtime = WorkflowRuntime(
    executor=executor,
    metadata=metadata,
    clock=fake_clock,
)
~~~

This supports deterministic retry, timeout and deadline tests.

---

# 108. ID generator API

Execution ID generation SHOULD be injectable for deterministic tests.

Production default generation must provide collision-resistant identities without process-local counter assumptions.

---

# 109. Stability tiers

At 2.0:

~~~text
STABLE
    WorkflowDefinition / TaskDefinition
    ExecutionPlan
    WorkflowRuntime
    WorkflowRun / TaskRun / TaskAttempt identities
    RetryPolicy / TimeoutPolicy
    InlineExecutor contract
    MetadataStore contract
    stable serialization/reference contracts
    official sibling adapter contracts when declared

PROVISIONAL
    emerging executors
    advanced remote-provider adapters
    optional control-plane-oriented APIs

INTERNAL
    DependencyGraph
    scheduler graph structures
    persistence ORM entities
    execution-loop internals
    plugin loader internals
~~~

Stability status must be visible in documentation.

---

# 110. V1 migration posture

WorkflowKit 2.0 is a clean-slate major line.

Semantic migration:

~~~text
legacy workflow/job
    → WorkflowDefinition

legacy task/step
    → TaskDefinition

legacy run
    → WorkflowRun

legacy retry occurrence
    → TaskAttempt

legacy provider execution tracking
    → ExternalRunRef
~~~

Aliases are not introduced automatically.

---

# 111. Legacy decorator migration

Existing decorators MAY remain if they produce V2 canonical models.

A legacy decorator that embeds execution state or bypasses WorkflowRuntime must be rewritten.

---

# 112. Legacy executor migration

Existing thread, process, async and subprocess executors may be reused when they implement the stable Executor Protocol and conform to TaskAttempt semantics.

Provider-specific behavior remains behind qualified executors.

---

# 113. Legacy metadata-store migration

Existing memory, SQLite and PostgreSQL persistence may be reused after alignment with:

~~~text
WorkflowRunId
TaskRunId
TaskAttemptId
ExternalRunRef
validated state transitions
recovery queries
versioned schema migrations
~~~

Private V1 table shape is not a permanent V2 public contract.

---

# 114. Legacy recovery migration

Any V1 behavior equivalent to:

~~~text
process restart
    → create fresh task execution immediately
~~~

must be replaced when prior external work may still exist.

V2 recovery first reloads and reconciles existing execution evidence.

---

# 115. Local workflow example

~~~python
from pyworkflowkit import (
    RetryPolicy,
    TaskDefinition,
    WorkflowDefinition,
    WorkflowRuntime,
)

from pyworkflowkit.executors import (
    InlineExecutor,
)

from pyworkflowkit.persistence.sqlite import (
    SQLiteMetadataStore,
)

def extract():
    return {
        "resource": "input.json",
    }

def transform():
    return {
        "resource": "output.json",
    }

builder = WorkflowDefinition.builder(
    "example"
)

extract_task = builder.task(
    "extract",
    workload=extract,
    retry_policy=RetryPolicy(
        max_attempts=3,
    ),
)

transform_task = builder.task(
    "transform",
    workload=transform,
    depends_on=(
        extract_task,
    ),
)

workflow = builder.build()

runtime = WorkflowRuntime(
    executor=InlineExecutor(),
    metadata=SQLiteMetadataStore(
        "./workflow.db"
    ),
)

result = runtime.run(
    workflow
)
~~~

This example is normative in architectural shape.

---

# 116. Compile and inspect example

~~~python
from pyworkflowkit.planning import (
    WorkflowPlanner,
)

plan = (
    WorkflowPlanner()
    .compile(workflow)
)

print(
    plan.explain()
)

print(
    plan.topological_order
)

print(
    plan.fingerprint()
)
~~~

No task is executed during compilation.

---

# 117. Recovery example

~~~python
original = runtime.run(
    workflow
)

# After a process restart:
runtime2 = WorkflowRuntime(
    executor=InlineExecutor(),
    metadata=SQLiteMetadataStore(
        "./workflow.db"
    ),
)

recovered = runtime2.recover(
    original.run_id
)
~~~

Recovery preserves the WorkflowRunId.

A new TaskAttempt is created only if retry semantics require it.

---

# 118. PyIngestKit integration example

~~~python
from pyworkflowkit import (
    TaskDefinition,
)

from pyworkflowkit.integrations.pyingestkit import (
    IngestionWorkload,
)

ingest = TaskDefinition(
    key="ingest_customers",
    workload=IngestionWorkload(
        definition=customers_ingestion,
    ),
)
~~~

The resulting TaskAttempt stores portable execution reference/evidence rather than PyIngestKit private runtime objects.

---

# 119. PyTransformKit integration example

~~~python
from pyworkflowkit.integrations.pytransformkit import (
    TransformationWorkload,
)

transform = TaskDefinition(
    key="transform_customer_mart",
    workload=TransformationWorkload(
        plan=customer_mart_plan,
        engine="polars",
    ),
)
~~~

The workflow dependency graph contains one transform workload task, not each internal transformation node.

---

# 120. API anti-patterns

Rejected patterns include:

~~~text
WorkflowDefinition.run() as the only/primary execution model
public WorkflowGraph required for normal authoring
public DependencyGraph as canonical domain state
retry mutating the same TaskAttempt identity
restart implemented as blind rerun
timeout interpreted as confirmed external failure
cancellation request interpreted as confirmed cancellation
large DataFrame stored in durable TaskRun output
pickle-based durable WorkflowDefinition state
automatic plugin activation
sibling runtime internals copied into WorkflowKit
cron scheduler treated as required core architecture
mandatory global executor registry
~~~

---

# 121. Root exclusion list

The root package MUST NOT export by default:

~~~text
WorkflowGraph
DependencyGraph
private planner node classes
execution-loop internals
private persistence models
SQLAlchemy entities
executor worker internals
plugin loader internals
remote control-plane internals
~~~

---

# 122. Compatibility tests

Release CI MUST snapshot and compare at least:

~~~text
root exports
qualified stable exports
public signatures
constructors
Protocol members
state enum members
exception hierarchy
stable executor IDs
stable extra names
stable plugin entry-point groups
wire contract versions
sibling integration contract versions
~~~

Unexpected stable-surface drift blocks release.

---

# 123. Public API acceptance criteria

PyWorkflowKit V2 public API is accepted when:

1. root import works with base dependencies only;
2. WorkflowDefinition is the canonical authoring root;
3. TaskDefinition represents one workload boundary;
4. no public WorkflowGraph is required;
5. no public DependencyGraph is required;
6. WorkflowPlanner compiles to deterministic ExecutionPlan without execution;
7. WorkflowRun, TaskRun and TaskAttempt expose distinct typed identities;
8. retry creates a new TaskAttemptId;
9. timeout does not imply confirmed external failure;
10. cancellation request and confirmation remain distinct;
11. UNKNOWN_OUTCOME survives into public state;
12. ExternalRunRef is portable and durable;
13. recovery preserves WorkflowRunId and reconciles before rerun;
14. durable task output uses portable references/small values;
15. InlineExecutor implements the stable Executor contract;
16. MetadataStore protects durable execution state;
17. serialization is schema-driven and non-executable;
18. PyIngestKit/PyTransformKit integrations remain optional;
19. V1 migration does not reintroduce generic ambiguous aliases;
20. API freeze tests pass against built wheels.

---

# 124. Normative API invariants

### PWK-API-INV-01 — Root API is curated

Only canonical workflow concepts are promoted to package root.

### PWK-API-INV-02 — WorkflowDefinition is declarative

Construction and compilation do not execute workloads.

### PWK-API-INV-03 — Workflow topology belongs to WorkflowDefinition

WorkflowGraph and DependencyGraph remain internal.

### PWK-API-INV-04 — ExecutionPlan is compiled semantics

It contains deterministic validated workflow meaning, not runtime state.

### PWK-API-INV-05 — Runtime identities are layered

WorkflowRunId, TaskRunId and TaskAttemptId remain distinct.

### PWK-API-INV-06 — Retry creates a new TaskAttempt

Attempt identity never mutates across retry.

### PWK-API-INV-07 — Recovery is not rerun

Recovery preserves existing execution identity and reconciles external work first.

### PWK-API-INV-08 — Uncertainty is public

UNKNOWN_OUTCOME and cancellation uncertainty cannot be collapsed into generic failure.

### PWK-API-INV-09 — Durable outputs are portable

Large native objects and active handles do not become durable workflow state.

### PWK-API-INV-10 — Sibling runtimes remain opaque

WorkflowKit integrates through public workload adapters and execution references.

### PWK-API-INV-11 — Serialization is explicit and safe

Durable workflow state never depends on arbitrary executable Python serialization.

### PWK-API-INV-12 — Stable API is machine-checkable

Exports, signatures, states, protocols, IDs, extras and contracts are protected continuously in CI.

---

# 125. Canonical API surface summary

~~~text
AUTHORING
    WorkflowDefinition
    TaskDefinition
    builder / decorators
    RetryPolicy
    TimeoutPolicy
    trigger rules

PLANNING
    WorkflowPlanner
    ExecutionPlan

RUNTIME
    WorkflowRuntime
    WorkflowRun / WorkflowRunId
    TaskRun / TaskRunId
    TaskAttempt / TaskAttemptId
    WorkflowResult

EXECUTION
    Executor
    ExecutorRegistry
    InlineExecutor
    optional Thread / Process / Async / Subprocess executors

PERSISTENCE
    MetadataStore
    InMemoryMetadataStore
    SQLiteMetadataStore
    optional PostgreSQLMetadataStore

RELIABILITY
    RetryDecision
    ExternalRunRef
    recovery
    reconciliation
    cancellation

PORTABLE BOUNDARIES
    CorrelationContext
    FailureEvidence
    portable references
    manifests
    explicit codecs

OPTIONAL INTEGRATIONS
    pyworkflowkit.integrations.pyingestkit
    pyworkflowkit.integrations.pytransformkit
~~~

---

# 126. Final API statement

PyWorkflowKit 2.0 exposes one coherent progression from declarative workload dependencies to durable execution evidence:

~~~text
TaskDefinition
        ↓
WorkflowDefinition
        ↓
ExecutionPlan
        ↓
WorkflowRuntime.run
        ↓
WorkflowRun
    └── TaskRun
          └── TaskAttempt
                ↓
          ExternalRunRef
        ↓
WorkflowResult
~~~

> **The stable API makes dependency planning explicit, retry attempt-scoped, recovery identity-preserving, external execution traceable and sibling workload semantics opaque.**

This specification is the normative baseline for:

~~~text
PYWORKFLOWKIT_V2_IMPLEMENTATION_ROADMAP.md
~~~
