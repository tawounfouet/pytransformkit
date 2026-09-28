# PyKit Ecosystem V2 - Declaration, Plan and Runtime Model

> **Status:** NORMATIVE PUBLIC-MODEL RATIONALIZATION BASELINE
> **Architecture generation:** V2
> **Date:** 2026-09-28
> **Scope:** PyTransformKit 1.0, PyIngestKit 2.0, PyWorkflowKit 2.0
> **Primary purpose:** close Phase 0 public-model rationalization

## 1. Purpose

This document resolves the remaining ambiguity around declaration, graph, plan, compiled representation and runtime objects across PyKit V2.

It establishes a shared architectural grammar without forcing the three frameworks into identical class hierarchies.

> **Shared architectural grammar does not require shared public object symmetry.**

> **A type becomes public because users need to reason about it independently, not because another framework has a type at the same conceptual level.**

## 2. Problem being resolved

Earlier drafts used vocabulary such as:

~~~text
IngestionDefinition
IngestionLifecycle
IngestionPlan

TransformationPlan
TransformationGraph
LogicalPlan
OptimizedLogicalPlan
PhysicalPlan

WorkflowDefinition
WorkflowGraph
DependencyGraph
ExecutionPlan
~~~

Some terms are useful conceptually or internally without deserving a stable public class.

Without rationalization, these layers would create conversion ceremony, duplicated state and compatibility obligations without independent user value.

## 3. Generic architectural grammar

~~~text
USER DECLARATION
      ↓
VALIDATION / COMPILATION
      ↓
INSPECTABLE OR EXECUTABLE PLAN
      ↓
RUNTIME EXECUTION
      ↓
RUNTIME RECORD / RESULT
~~~

Not every framework requires a public type at every line.

The grammar describes phases of meaning rather than a universal inheritance hierarchy.

## 4. Declaration

A declaration is an immutable or effectively immutable description of user intent.

A declaration SHOULD be constructible without external I/O, remain independent from runtime state and avoid active provider handles.

Canonical declarations include:

~~~text
IngestionDefinition
TransformationPlan
WorkflowDefinition
TaskDefinition
~~~

## 5. Plan

A plan is a representation derived from declaration semantics for validation, inspection, optimization or execution preparation.

A plan deserves a public type only when it owns independent value such as normalized semantics, deterministic ordering, capability requirements, compile-time diagnostics, a stable fingerprint, portable serialization or a public extension boundary.

If none of these apply, the plan remains internal.

## 6. Runtime

Runtime owns execution-time concerns such as:

~~~text
execution identity
state
attempts
resource binding
engine or provider interaction
failure evidence
diagnostics
cancellation
reconciliation
runtime lineage
~~~

Mutable runtime state MUST NOT be stored on immutable declarations.

## 7. Run versus result

~~~text
RUN
    durable or inspectable execution identity and state

RESULT
    caller-facing outcome view
~~~

A result may reference a run without exposing all persisted runtime state.

## 8. No universal base hierarchy

PyKit MUST NOT introduce public BaseDeclaration, BaseDefinition, BasePlan, BaseRun or BaseResult types merely for visual symmetry.

Cross-framework interoperability occurs through portable boundary contracts, not inheritance.

## 9. No universal graph abstraction

Transformation topology, workflow dependencies and ingestion lifecycle have different semantics.

A generic graph utility may exist internally, but no universal Graph becomes a shared domain model.

## 10. Public-type admission test

Before adding a public architecture type, maintainers MUST identify at least one strong independent responsibility:

1. independent invariants;
2. independent lifecycle;
3. independent inspection value;
4. independent serialization;
5. public extension boundary;
6. stable fingerprint or identity;
7. information not already owned by its source object;
8. independently testable behavior.

If none apply, the concept stays internal.

## 11. PyIngestKit canonical model

~~~text
IngestionDefinition
        ↓
IngestionRuntime.run(...)
        ↓
IngestionRun
        ↓
IngestionResult
~~~

Runtime may normalize or compile the definition internally without exposing a public IngestionPlan.

## 12. IngestionDefinition

IngestionDefinition is the canonical PyIngestKit V2 authoring root.

It owns declared source semantics, decode semantics, representation/schema expectations, validation policy, RAW policy, dataset identity and runtime-independent publication intent.

It MUST NOT own current run identity, active connection, retry counters, runtime status, resolved credentials, workflow scheduling or transformation topology.

## 13. IngestionLifecycle

IngestionLifecycle remains a normative conceptual lifecycle:

~~~text
Source
    ↓ Acquire
RAW
    ↓ Decode
Validate
    ↓ Version
DatasetVersion
    ↓ Publish
PublishedDataset
~~~

However, **IngestionLifecycle is not a required public class in V2**.

It may be promoted later only if independent inspection, extension or serialization requirements are proven.

## 14. IngestionPlan

PyIngestKit V2 does not initially expose a public IngestionPlan.

Runtime may internally derive a PreparedIngestion, CompiledIngestion or equivalent structure.

Public promotion requires evidence that users need to inspect, persist or extend that compiled representation independently.

## 15. IngestionRun and IngestionResult

IngestionRun is the runtime-domain record for one ingestion execution and owns IngestionRunId, state and durable execution evidence.

IngestionResult is the caller-facing outcome and may expose status, DatasetVersionReference, ArtifactReference, diagnostics and FailureEvidence.

Exact API shape is deferred to PYINGESTKIT_V2_PUBLIC_API_SPEC.md.

## 16. PyIngestKit decision

~~~text
PUBLIC
    IngestionDefinition
    IngestionRuntime
    IngestionRun / IngestionRunId
    IngestionResult

CONCEPTUAL OR INTERNAL
    IngestionLifecycle
    IngestionPlan
    lifecycle graph
    compiled ingestion representation
~~~

## 17. PyTransformKit canonical model

~~~text
TransformationPlan
        ↓
compile
        ↓
LogicalPlan
        ↓
engine-specific lowering
        ↓
TransformationExecution
        ↓
TransformationResult
~~~

TransformationPlan and LogicalPlan both own independent semantics and remain distinct.

## 18. TransformationPlan

TransformationPlan is the canonical public authoring root.

It owns user-declared logical transformation intent and may contain the immutable DAG of Transformation objects.

The transformation topology is therefore already part of TransformationPlan semantics.

## 19. TransformationGraph

TransformationGraph is not part of the initial stable public API.

Internal graph structures may support traversal, validation and planning, but a separate public graph wrapper would duplicate topology already owned by TransformationPlan.

A future read-only graph view may be added only if it has independent user value.

## 20. LogicalPlan

LogicalPlan remains a justified public compiled representation.

It may own normalized logical operations, resolved dependencies, propagated logical schema, capability requirements, compile-time diagnostics, canonical ordering, logical-plan fingerprint and portable logical IR.

Therefore:

> **TransformationPlan describes what the author declares; LogicalPlan describes the normalized logical program understood by the framework.**

Compilation MUST NOT execute the transformation against physical data.

## 21. OptimizedLogicalPlan

PyTransformKit V1 does not expose a distinct public OptimizedLogicalPlan type.

Optimization is modeled as:

~~~text
LogicalPlan
    ↓ optimizer
LogicalPlan
~~~

Optimization metadata and diagnostics may be attached or returned separately.

## 22. PhysicalPlan

A universal stable public PhysicalPlan is not part of the initial V1 target.

Physical lowering is engine-specific:

~~~text
LogicalPlan
    ↓ EngineAdapter
engine-specific compiled representation
    ↓ execute
physical output
~~~

Adapters may own internal physical plans.

A shared public PhysicalPlan may be reconsidered only after multiple engines demonstrate stable common semantics worth exposing.

## 23. TransformationExecution and TransformationResult

TransformationExecution is the runtime-domain record for one execution and owns TransformationExecutionId, CorrelationContext, engine identity, bindings, status, failure evidence, diagnostics and runtime lineage evidence.

TransformationResult is the caller-facing outcome and may expose portable output references, lineage evidence and diagnostics.

It MUST NOT implicitly create a PyIngestKit DatasetVersion.

## 24. PyTransformKit decision

~~~text
PUBLIC
    TransformationPlan
    LogicalPlan
    TransformationRuntime
    TransformationExecution / TransformationExecutionId
    TransformationResult

INTERNAL OR PROVISIONAL
    TransformationGraph
    OptimizedLogicalPlan
    generic PhysicalPlan
    engine-specific compiled representation
~~~

## 25. PyWorkflowKit canonical model

~~~text
WorkflowDefinition
        ↓
compile / plan
        ↓
ExecutionPlan
        ↓
WorkflowRuntime.run(...)
        ↓
WorkflowRun
    ├── TaskRun
    │     └── TaskAttempt
        ↓
WorkflowResult
~~~

WorkflowDefinition and ExecutionPlan both have independent semantics.

## 26. WorkflowDefinition

WorkflowDefinition is the canonical public authoring root.

It owns TaskDefinitions, workload dependency declarations, workflow-level policy, declared conditions and runtime-independent configuration.

It MUST NOT own TaskAttempt state, active workers, provider sessions, external run state or retry counters.

## 27. TaskDefinition

TaskDefinition remains public because one task owns independent workload semantics.

It may own task identity within the workflow definition, workload declaration, dependency declarations, timeout/retry policy references and input/output contract declarations.

TaskDefinition is not a universal cross-framework Step.

## 28. WorkflowGraph and DependencyGraph

WorkflowGraph is not a required public class because WorkflowDefinition already owns the declared workload topology.

DependencyGraph remains an internal algorithmic representation for cycle detection, topological sorting, reachability and readiness analysis.

Useful dependency inspection should be exposed through WorkflowDefinition or ExecutionPlan rather than raw graph internals.

## 29. ExecutionPlan

ExecutionPlan remains a justified public compiled representation.

It may own validated task topology, deterministic topological order, resolved conditions, readiness prerequisites, effective execution policies, executor requirements, plan fingerprint and compile-time diagnostics.

It MUST remain free from runtime IDs, attempt counters, active workers and resolved secret values.

## 30. Workflow runtime records

WorkflowRun represents one workflow execution.

TaskRun represents one logical task execution within that WorkflowRun.

TaskAttempt represents one concrete attempt.

Retries create new TaskAttemptId values while preserving TaskRunId.

TaskAttempt may retain ExternalRunRef, FailureEvidence, cancellation state and reconciliation evidence.

## 31. WorkflowResult

WorkflowResult is the caller-facing outcome and may summarize WorkflowRunId, status, task outcomes, portable output references, diagnostics and failure evidence.

The persisted WorkflowRun remains the richer execution record.

## 32. PyWorkflowKit decision

~~~text
PUBLIC
    WorkflowDefinition
    TaskDefinition
    ExecutionPlan
    WorkflowRuntime
    WorkflowRun / WorkflowRunId
    TaskRun / TaskRunId
    TaskAttempt / TaskAttemptId
    WorkflowResult

INTERNAL
    WorkflowGraph
    DependencyGraph
    scheduler graph internals
~~~

## 33. Cross-framework comparison

| Concern | PyIngestKit | PyTransformKit | PyWorkflowKit |
|---|---|---|---|
| Authoring root | IngestionDefinition | TransformationPlan | WorkflowDefinition |
| Public compiled form | none initially | LogicalPlan | ExecutionPlan |
| Public graph wrapper | none | none | none |
| Runtime service | IngestionRuntime | TransformationRuntime | WorkflowRuntime |
| Runtime identity | IngestionRunId | TransformationExecutionId | WorkflowRunId / TaskRunId / TaskAttemptId |
| Runtime record | IngestionRun | TransformationExecution | WorkflowRun / TaskRun / TaskAttempt |
| Caller result | IngestionResult | TransformationResult | WorkflowResult |

The asymmetry is deliberate and normative.

## 34. Why IngestKit has no public compiled plan initially

IngestionDefinition already expresses a lifecycle-oriented operation whose preparation is primarily resource/provider resolution.

Until significant independent planning semantics emerge, a public IngestionPlan would add ceremony without meaning.

Future multi-source planning, partition planning or schema-negotiation needs may justify revisiting this decision.

## 35. Why TransformKit has LogicalPlan

Transformation compilation creates an engine-neutral IR with independent inspection value for adapters, optimization, capability analysis, lineage, fingerprints and explainability.

That is sufficient semantic weight for a public LogicalPlan.

## 36. Why WorkflowKit has ExecutionPlan

Workflow planning creates independently useful validated execution semantics: deterministic dependency order, readiness prerequisites, effective policies and executor requirements.

That is sufficient semantic weight for a public ExecutionPlan.

## 37. Canonical verb semantics

~~~text
build()
    builder finalization into canonical declaration/value

validate()
    structural and semantic validation

compile()
    declaration → compiled representation without execution

execute()
    compute-oriented runtime action, preferred by PyTransformKit

run()
    lifecycle-oriented runtime action, preferred by PyIngestKit and PyWorkflowKit
~~~

A framework need not expose every verb directly on its authoring object.

## 38. Preferred runtime-oriented usage

~~~python
definition = IngestionDefinition(...)
result = IngestionRuntime(...).run(definition)

plan = TransformationPlan(...)
result = TransformationRuntime(...).execute(plan)

workflow = WorkflowDefinition(...)
result = WorkflowRuntime(...).run(workflow)
~~~

Declarations and plans are not required to own run() or execute() as their primary API.

## 39. Compilation ownership

Compilation SHOULD be implemented by dedicated compiler/planner/runtime services rather than hidden mutable state on declarations.

Conceptually:

~~~text
TransformationCompiler
    TransformationPlan → LogicalPlan

WorkflowPlanner
    WorkflowDefinition → ExecutionPlan
~~~

Exact class names remain deferred to framework-specific public API specifications.

## 40. Compilation purity

Compilation MUST NOT execute external workloads, publish datasets, create runtime execution IDs or mutate provider state.

Validation and explicit capability inspection may occur without turning compilation into execution.

## 41. Fingerprints

Fingerprints belong to semantic layers rather than runtime identity.

~~~text
TransformationPlan fingerprint
LogicalPlan fingerprint
WorkflowDefinition fingerprint
ExecutionPlan fingerprint
~~~

Runtime IDs are never plan fingerprints.

## 42. Runtime-state separation

Rejected patterns include:

~~~text
TransformationPlan.status = RUNNING
WorkflowDefinition.retry_count = 2
IngestionDefinition.run_id = ...
~~~

Declarations SHOULD be reusable across multiple executions with distinct runtime identities.

## 43. Explainability without public graph wrappers

Users may inspect or visualize topology through public declaration/plan APIs.

Examples:

~~~text
TransformationPlan or LogicalPlan
    → explain / inspect / visualize

WorkflowDefinition or ExecutionPlan
    → explain / inspect / visualize

IngestionDefinition
    → describe lifecycle / inspect declared intent
~~~

A visualization projection is not automatically a new domain type.

## 44. Builders and decorators

Builders and decorators are authoring ergonomics, not new semantic layers.

~~~text
Builder.build() → canonical declaration
@task → TaskDefinition
~~~

They MUST converge on the canonical domain model.

## 45. Runtime-local objects

The following remain non-portable runtime concerns by default:

~~~text
open connection
engine session
DataFrame
LazyFrame
Arrow Table
provider SDK client
thread/process handle
subprocess object
event loop
~~~

They remain behind adapters or handles and do not become durable declaration/plan state.

## 46. Earlier vocabulary interpretation

This document refines the public-API status of terms already used in earlier V2 specifications.

After this baseline:

~~~text
IngestionLifecycle
    conceptual lifecycle, not initial public class

TransformationGraph
    internal representation or conceptual topology

WorkflowGraph
    internal representation or conceptual topology

DependencyGraph
    internal algorithmic representation

OptimizedLogicalPlan
    optimization state, not distinct public type

PhysicalPlan
    adapter/runtime-specific; not initial stable universal type
~~~

The underlying concepts remain valid where earlier documents use them conceptually.

## 47. Target root vocabulary

~~~text
PyIngestKit
    IngestionDefinition
    IngestionRuntime
    IngestionRun
    IngestionResult

PyTransformKit
    TransformationPlan
    LogicalPlan
    TransformationRuntime
    TransformationExecution
    TransformationResult

PyWorkflowKit
    WorkflowDefinition
    TaskDefinition
    ExecutionPlan
    WorkflowRuntime
    WorkflowRun
    TaskRun
    TaskAttempt
    WorkflowResult
~~~

Supporting IDs, references, schemas, expressions, policies and errors are added by their owning framework.

## 48. Public API freeze rule

Framework-specific API specs MUST NOT reintroduce the following as stable public types without an explicit architecture amendment:

~~~text
IngestionLifecycle
IngestionPlan
TransformationGraph
OptimizedLogicalPlan
universal PhysicalPlan
WorkflowGraph
DependencyGraph
~~~

## 49. Customer 360 pressure test

Customer 360 MUST be implementable without constructing artificial graph wrapper objects.

Expected common path:

~~~text
IngestionDefinition → IngestionRuntime
TransformationPlan → TransformationRuntime
WorkflowDefinition → WorkflowRuntime
~~~

LogicalPlan and ExecutionPlan may be inspected when compilation visibility is useful.

## 50. Decision matrix

| Candidate | Initial status | Reason |
|---|---|---|
| IngestionDefinition | Public | canonical ingestion declaration |
| IngestionLifecycle | Conceptual/internal | lifecycle model, no independent public state |
| IngestionPlan | Internal/not required | no proven public compile semantics yet |
| IngestionRun | Public runtime | independent execution identity/state |
| TransformationPlan | Public | canonical transformation declaration |
| TransformationGraph | Internal | topology already owned by TransformationPlan |
| LogicalPlan | Public | normalized engine-neutral compiled IR |
| OptimizedLogicalPlan | Not distinct public type | optimizer preserves LogicalPlan contract |
| PhysicalPlan | Internal/provisional | engine-specific lowering |
| TransformationExecution | Public runtime | independent execution identity/state |
| WorkflowDefinition | Public | canonical workflow declaration |
| TaskDefinition | Public | independent workload semantics |
| WorkflowGraph | Internal | topology already owned by WorkflowDefinition |
| DependencyGraph | Internal | algorithmic representation |
| ExecutionPlan | Public | validated deterministic execution semantics |
| WorkflowRun | Public runtime | durable workflow execution |
| TaskRun | Public runtime | logical task execution |
| TaskAttempt | Public runtime | concrete retry attempt |

## 51. Acceptance criteria

This model is accepted when:

1. no framework exposes layers solely for naming symmetry;
2. IngestionDefinition is the PyIngestKit authoring root;
3. IngestionLifecycle remains conceptual unless future evidence justifies promotion;
4. IngestionPlan is not required in the initial V2 public API;
5. TransformationPlan owns transformation authoring topology;
6. TransformationGraph is not an initial stable public type;
7. LogicalPlan remains a distinct public compiled representation;
8. OptimizedLogicalPlan is not a distinct public type;
9. generic PhysicalPlan is not an initial stable universal type;
10. WorkflowDefinition owns declared workflow topology;
11. TaskDefinition remains public;
12. WorkflowGraph and DependencyGraph remain internal;
13. ExecutionPlan remains a distinct public compiled representation;
14. declarations contain no mutable runtime state;
15. runtime identities remain separate from fingerprints;
16. run/result distinctions remain explicit where useful;
17. common APIs do not require unnecessary intermediate object construction;
18. compilation remains free of workload execution side effects;
19. Customer 360 works with this vocabulary;
20. framework-specific target architectures follow this baseline.

## 52. Normative invariants

### DPR-INV-01 — Shared grammar does not require shared class symmetry

The frameworks align conceptually without copying public layers.

### DPR-INV-02 — Public types require independent semantics

No public type exists solely because an internal representation exists.

### DPR-INV-03 — Declarations are runtime-state free

Authoring values contain no mutable execution state.

### DPR-INV-04 — Compilation does not execute workloads

Compile/plan stages derive representations and diagnostics only.

### DPR-INV-05 — PyIngestKit exposes no mandatory public IngestionPlan initially

IngestionDefinition can run directly through IngestionRuntime.

### DPR-INV-06 — TransformationPlan owns authoring topology

A separate public TransformationGraph is unnecessary.

### DPR-INV-07 — LogicalPlan is a real public compiled contract

It owns normalized engine-neutral transformation semantics.

### DPR-INV-08 — Optimization does not create a second public logical-plan type

OptimizedLogicalPlan is not required.

### DPR-INV-09 — Physical planning remains adapter-owned initially

No premature universal PhysicalPlan contract is frozen.

### DPR-INV-10 — WorkflowDefinition owns declared workload topology

WorkflowGraph and DependencyGraph remain internal.

### DPR-INV-11 — ExecutionPlan is a real public workflow compilation contract

It owns validated deterministic execution semantics.

### DPR-INV-12 — Runtime records remain distinct from caller results

Execution state and ergonomic return values may evolve independently.

## 53. Canonical Phase 0 model

~~~text
PYINGESTKIT

IngestionDefinition
        ↓
IngestionRuntime.run()
        ↓
IngestionRun
        ↓
IngestionResult


PYTRANSFORMKIT

TransformationPlan
        ↓
LogicalPlan
        ↓
engine-specific lowering
        ↓
TransformationExecution
        ↓
TransformationResult


PYWORKFLOWKIT

WorkflowDefinition
        ↓
ExecutionPlan
        ↓
WorkflowRuntime.run()
        ↓
WorkflowRun
    ├── TaskRun
    │     └── TaskAttempt
        ↓
WorkflowResult
~~~

## 54. Final architecture statement

The ecosystem now has one shared conceptual grammar but three intentionally different public models.

> **Expose a declaration when users need to express intent, expose a plan when compiled semantics deserve independent inspection, and expose runtime records when execution has its own identity and lifecycle. Do not expose extra layers merely to make diagrams symmetrical.**

With this decision, Phase 0 of the V2 implementation sequence is architecturally closed, subject to validation by the framework-specific target architecture documents and Customer 360.

The next normative documents are:

~~~text
PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md
PYINGESTKIT_V2_TARGET_ARCHITECTURE.md
PYWORKFLOWKIT_V2_TARGET_ARCHITECTURE.md
~~~