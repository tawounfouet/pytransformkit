# PyKit Ecosystem V2 — Public API Design Principles

> **Status:** NORMATIVE API DESIGN BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit  
> **Compatibility posture:** clean-slate public API design; no legacy API preservation requirement  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md  
> **Related:** PYTRANSFORMKIT_PYINGESTKIT_PYWORKFLOWKIT_BOUNDARIES_AND_INTEGRATION.md

---

# 1. Purpose

This document defines the public API design principles shared by the V2 PyKit ecosystem.

It does not freeze every final class or method signature. It defines the rules from which the concrete public APIs of PyIngestKit 2.0, PyTransformKit before 1.0, and PyWorkflowKit 2.0 must be derived.

The objective is to ensure that the three frameworks feel like members of one coherent ecosystem without erasing their bounded contexts.

> **Consistency of API grammar must not become uniformity of domain semantics.**

The ecosystem therefore shares naming, lifecycle, mutation, validation, import, result, error and reference conventions while preserving distinct domain vocabularies:

~~~text
Ingestion*
Transformation*
Workflow* / Task*
~~~

---

# 2. API design goals

The V2 public APIs MUST optimize for:

- semantic clarity;
- explicit execution;
- predictable immutability;
- small package-root facades;
- strong typing;
- independent usability;
- composability;
- inspectability;
- deterministic behavior where semantics permit it.

A user should understand the domain role of a public type from its name.

Preferred:

~~~python
from pyingestkit import IngestionDefinition
from pytransformkit import TransformationPlan
from pyworkflowkit import WorkflowDefinition
~~~

Discouraged:

~~~python
from pyingestkit import Pipeline
from pytransformkit import Pipeline
from pyworkflowkit import Pipeline
~~~

---

# 3. Public API layers

Each framework SHOULD conceptually separate four public layers:

~~~text
AUTHORING API
    ↓
DOMAIN API
    ↓
APPLICATION / RUNTIME API
    ↓
INTEGRATION API
~~~

These layers may live in the same Python distribution, but their responsibilities must remain distinguishable.

## 3.1 Authoring API

The Authoring API is the developer-facing DSL used to create domain definitions.

Examples:

~~~text
IngestionDefinition(...)
TransformationPlan(...)
WorkflowDefinition(...)
~~~

Optional helpers may include:

~~~text
col(...)
lit(...)
source(...)
task(...)
workflow(...)
~~~

The Authoring API SHOULD be concise, strongly typed, side-effect free, deterministic, and usable in scripts, tests and notebooks.

Authoring convenience MUST NOT create separate domain semantics.

## 3.2 Domain API

The Domain API contains canonical values and rules.

Typical examples:

**PyIngestKit**

~~~text
IngestionDefinition
IngestionLifecycle
IngestionStage
SourceSpec
DatasetVersion
PublishedDataset
~~~

**PyTransformKit**

~~~text
TransformationPlan
TransformationGraph
Transformation
Expression
Schema
Dataset
LogicalPlan
~~~

**PyWorkflowKit**

~~~text
WorkflowDefinition
WorkflowGraph
TaskDefinition
WorkflowRun
TaskRun
TaskAttempt
~~~

The Domain API MUST NOT depend on CLI libraries, web frameworks, active database sessions, sibling framework internals, or optional physical engines unless that engine is explicitly part of the owned infrastructure layer.

## 3.3 Application / Runtime API

Runtime APIs perform work.

Conceptually:

~~~text
IngestionRuntime
TransformationRuntime
WorkflowRuntime
~~~

Exact final names may be refined in framework-specific API specifications.

The distinction is normative:

~~~text
Definition / Plan
    !=
Runtime / Service
~~~

A declarative value describes intent. A runtime component performs computation or side effects.

## 3.4 Integration API

Integration APIs connect bounded contexts through public contracts.

Recommended surfaces include:

~~~text
pyingestkit.integrations.pytransformkit

pyworkflowkit.integrations.pyingestkit
pyworkflowkit.integrations.pytransformkit
~~~

Integration APIs SHOULD operate on public definitions, results, references, protocols and stable error categories.

They MUST NOT depend on private module paths of sibling packages.

---

# 4. Root concepts

Each framework has one primary authoring/root concept.

~~~text
PyIngestKit
    IngestionDefinition

PyTransformKit
    TransformationPlan

PyWorkflowKit
    WorkflowDefinition
~~~

These types MUST remain conceptually different.

The ecosystem does not define a shared BaseDefinition, BasePlan, BasePipeline or BaseExecutable solely for visual symmetry.

Shared inheritance may be introduced only if repeated implementation evidence proves one real semantic contract.

---

# 5. Definition semantics

A public type ending in Definition represents declarative user intent.

A Definition SHOULD:

- be immutable;
- be side-effect free;
- have stable equality semantics where practical;
- validate local structural invariants;
- support inspection;
- avoid active external resources.

A Definition MUST NOT:

- execute work in its constructor;
- start threads or processes;
- mutate external state;
- resolve secrets automatically;
- open network connections;
- perform plugin activation as an import side effect.

---

# 6. Plan semantics

A type ending in Plan represents user-authored compute intent or a derived executable representation.

Every Plan MUST have a documented level.

Examples:

~~~text
TransformationPlan
LogicalPlan
OptimizedLogicalPlan
PhysicalPlan
ExecutionPlan
IngestionPlan
~~~

A public root type named only Plan is prohibited.

The canonical PyTransformKit planning chain is:

~~~text
TransformationPlan
        ↓
TransformationGraph
        ↓
LogicalPlan
        ↓
OptimizedLogicalPlan
        ↓
PhysicalPlan
~~~

The canonical PyWorkflowKit planning chain is:

~~~text
WorkflowDefinition
        ↓
WorkflowGraph
        ↓
ExecutionPlan
~~~

---

# 7. Graph semantics

A public Graph describes domain relationships.

Examples:

~~~text
TransformationGraph
WorkflowGraph
~~~

Graph APIs SHOULD expose semantic operations such as:

- dependency inspection;
- roots;
- leaves;
- predecessors;
- successors;
- deterministic ordering;
- validation.

They SHOULD NOT force ordinary users to manipulate low-level adjacency dictionaries.

DAG remains a structural property, not a preferred root domain type.

---

# 8. Spec semantics

Spec is reserved for subordinate declarative component specifications.

Examples:

~~~text
SourceSpec
SinkSpec
WindowSpec
ValidationSpec
RetrySpec
ExecutorSpec
~~~

A Spec is not normally the top-level aggregate root.

It describes one configurable component within a broader domain definition.

---

# 9. Policy semantics

Policy defines explicit behavioral rules or decision strategy.

Examples:

~~~text
RetryPolicy
ValidationPolicy
ConversionPolicy
PublicationPolicy
RedactionPolicy
~~~

Policies SHOULD be explicit, inspectable, immutable where practical, and independently testable.

A policy SHOULD NOT silently load environment variables or global configuration.

---

# 10. Reference semantics

Reference or Ref represents a portable identity/location boundary.

References SHOULD be:

- immutable;
- serializable;
- safe to log after redaction;
- independent of process memory;
- free from active resources.

A reference MUST NOT embed:

- open connections;
- DataFrames;
- sessions;
- callbacks;
- arbitrary Python objects;
- plaintext credentials.

Preferred examples include:

~~~text
ResourceReference
ArtifactReference
DatasetReference
DatasetVersionReference
TransformationExecutionReference
ExternalRunRef
~~~

---

# 11. Config semantics

Config is reserved for runtime/environment composition.

Examples:

~~~text
IngestionRuntimeConfig
TransformationRuntimeConfig
WorkflowRuntimeConfig
~~~

Config is distinct from domain intent.

For example:

~~~text
TransformationPlan
    !=
TransformationRuntimeConfig
~~~

A logical transformation must not change meaning merely because configuration comes from a different file or environment.

---

# 12. Runtime semantics

A Runtime owns active execution composition.

Typical responsibilities may include:

- adapter resolution;
- registry composition;
- resource ownership;
- execution;
- persistence coordination;
- telemetry dispatch;
- lifecycle management.

Runtime objects MAY be mutable internally when necessary.

Their public state transitions MUST remain explicit.

---

# 13. Service semantics

Service MAY be used in the application layer for focused use cases.

Examples:

~~~text
PlanCompilationService
PublicationService
RecoveryService
~~~

A generic package-root Service is prohibited.

A service name MUST identify its use case.

---

# 14. Builder semantics

Builders are permitted but not mandatory.

Use a builder when construction is multi-step or ergonomically difficult with one constructor.

Example:

~~~python
plan = (
    TransformationPlanBuilder()
    .input("customers")
    .derive(...)
    .filter(...)
    .build()
)
~~~

The final TransformationPlan SHOULD remain immutable.

A builder MUST NOT also become the runtime.

This is conceptually wrong:

~~~python
builder.run()
~~~

unless the object is not really a builder and should be renamed.

---

# 15. Fluent APIs

Fluent APIs MAY be used when they preserve readability.

Example:

~~~python
plan = (
    TransformationPlan.from_dataset(customers)
    .derive(...)
    .filter(...)
    .select(...)
)
~~~

If the root value is immutable, every fluent operation SHOULD conceptually return a new value.

A fluent API MUST NOT hide external side effects during declaration.

---

# 16. Decorator APIs

Decorators are allowed as authoring sugar, not as the sole canonical model.

Example:

~~~python
@workflow(...)
def daily_customer_mart():
    ...
~~~

must compile into the same canonical domain representation as a non-decorator API.

The invariant is:

~~~text
Decorator DSL
      ↓
Canonical Domain Model
~~~

not:

~~~text
Decorator DSL
      ↓
Separate execution semantics
~~~

Every decorator-based feature SHOULD have a canonical non-decorator representation.

---

# 17. Constructor rules

Constructors SHOULD perform only:

- local type validation;
- structural invariant validation;
- deterministic normalization independent from external state.

Constructors SHOULD NOT perform:

- HTTP requests;
- filesystem scans;
- database access;
- engine discovery;
- plugin activation;
- secret resolution.

Object construction should remain deterministic and cheap.

---

# 18. Validation model

Validation is divided into three layers:

~~~text
STRUCTURAL VALIDATION
        ↓
SEMANTIC VALIDATION
        ↓
RUNTIME PREFLIGHT
~~~

## 18.1 Structural validation

Checks intrinsic object correctness.

Examples:

- duplicate identifiers;
- impossible enum combinations;
- missing required fields;
- cycles where prohibited.

This may happen eagerly during construction.

## 18.2 Semantic validation

Checks domain consistency without external side effects.

Examples:

- incompatible transformation expression types;
- invalid workflow dependency semantics;
- contradictory ingestion lifecycle configuration.

This may happen through validate() or an explicit validator service.

## 18.3 Runtime preflight

Checks environment-dependent requirements.

Examples:

- engine installed;
- connector available;
- database reachable;
- plugin compatible;
- credential reference resolvable.

Runtime preflight MUST NOT be confused with domain validation.

---

# 19. Validation result style

Expected data/domain violations SHOULD preferably be represented through structured reports or results.

Programming errors and impossible API states SHOULD raise exceptions.

Examples:

~~~text
invalid Python argument
    → exception

dataset fails declared quality rule
    → structured ValidationResult

required engine unavailable
    → explicit capability/configuration error
~~~

---

# 20. Canonical verbs

The ecosystem standardizes the semantic intent of common verbs.

## build()

Converts a builder or authoring DSL into a canonical domain value.

~~~text
Builder → Definition / Plan
~~~

## validate()

Checks structural or semantic correctness without performing the primary external side effect.

## compile()

Transforms one representation into another executable representation.

Examples:

~~~text
TransformationPlan → LogicalPlan
LogicalPlan → PhysicalPlan
WorkflowDefinition → ExecutionPlan
~~~

compile() MUST NOT silently execute compiled work.

## plan()

May produce a derived plan where compile terminology would be misleading. Its meaning MUST be documented through a domain-qualified return type.

## execute()

Performs computation-oriented execution.

Primary intended use:

~~~text
PyTransformKit
TransformationRuntime.execute(...)
~~~

## run()

Performs lifecycle-oriented execution.

Preferred use:

~~~text
PyIngestKit
IngestionRuntime.run(...)

PyWorkflowKit
WorkflowRuntime.run(...)
~~~

The ecosystem deliberately distinguishes:

~~~text
transform → execute

ingestion/workflow lifecycle → run
~~~

## inspect()

Returns structured information without changing state.

## explain()

Produces plan/execution explanation where supported without changing logical semantics.

---

# 21. Definition objects do not own execution

The canonical architecture SHOULD avoid making declarative values the only execution entry point.

Avoid making this the primary design:

~~~python
definition.run()
plan.execute()
workflow.run()
~~~

Preferred separation:

~~~python
runtime.run(definition)
runtime.execute(plan)
~~~

This keeps domain intent, environment composition, resource ownership and execution lifecycle separate.

Convenience methods MAY later exist as thin facades only if they do not hide configuration or ownership.

---

# 22. Canonical execution shapes

## 22.1 PyIngestKit

~~~python
definition = IngestionDefinition(...)

runtime = IngestionRuntime(...)
result = runtime.run(definition)
~~~

## 22.2 PyTransformKit

~~~python
plan = TransformationPlan(...)

runtime = TransformationRuntime(...)
result = runtime.execute(plan)
~~~

## 22.3 PyWorkflowKit

~~~python
definition = WorkflowDefinition(...)

runtime = WorkflowRuntime(...)
result = runtime.run(definition)
~~~

These examples define API grammar, not final signatures.

---

# 23. Result objects

Runtime methods MUST return explicit domain result types when lifecycle evidence matters.

Examples:

~~~text
IngestionResult
TransformationResult
WorkflowResult
~~~

Result objects SHOULD contain:

- stable execution identity;
- terminal outcome/status;
- relevant output references;
- diagnostics;
- correlation information;
- timestamps where meaningful;
- structured warnings.

They SHOULD NOT expose private runtime implementation objects.

---

# 24. Native physical outputs

PyTransformKit MAY expose native physical output through an explicit adapter-owned handle.

Conceptually:

~~~text
TransformationResult
    ├── output_reference
    ├── schema
    ├── execution metadata
    └── physical_handle
~~~

The physical handle must have explicit engine coupling and ownership semantics.

PyWorkflowKit SHOULD normally treat sibling outputs as opaque references/results rather than physical DataFrames or database objects.

---

# 25. Status models

Status enums MUST be domain-owned and domain-qualified where public.

Examples:

~~~text
IngestionRunStatus
TransformationExecutionStatus
WorkflowRunStatus
TaskRunStatus
TaskAttemptStatus
~~~

A global public Status type is prohibited.

Even if values overlap, transition semantics may differ.

---

# 26. Error model

Each package MUST expose one documented root exception.

Conceptually:

~~~text
PyIngestKitError
PyTransformKitError
PyWorkflowKitError
~~~

Domain-specific errors derive beneath those roots.

Cross-framework adapters MUST preserve:

- source framework;
- stable error code where available;
- failure category;
- retryability metadata where meaningful;
- uncertainty state where meaningful.

Adapters MUST NOT flatten every failure into one generic exception.

Human-readable messages are not stable machine contracts. Machine decisions SHOULD rely on exception type, stable error code, structured result fields or enum categories.

---

# 27. Structured warnings

Warnings that are part of runtime evidence SHOULD be structured.

Prefer:

~~~text
DiagnosticWarning(
    code=...,
    category=...,
    message=...,
)
~~~

over only emitting strings.

Python warnings remain appropriate for developer-facing deprecations and API misuse.

---

# 28. Package-root facade

Each project MUST explicitly curate its package-root exports.

The package root SHOULD contain:

- primary authoring types;
- primary domain values;
- primary runtime facade;
- common errors;
- common enums;
- high-frequency helpers.

It SHOULD NOT expose:

- ORM models;
- migration internals;
- persistence implementation classes;
- low-level graph algorithms;
- implementation-only adapters;
- test utilities.

A symbol is not public merely because Python can import it.

---

# 29. Public API manifest

Each package SHOULD maintain a machine-checkable public API manifest.

Possible mechanisms include:

- explicit __all__;
- generated API snapshots;
- public-symbol contract tests;
- documented package-root export lists.

Stable releases MUST make accidental public API drift detectable.

---

# 30. Deep imports

Deep imports MAY be public, but only when explicitly documented.

The project MUST distinguish:

~~~text
documented public module
    vs
implementation module
~~~

Private modules SHOULD use a leading underscore, an internal namespace, or another explicit non-public convention.

Private objects MUST NOT accidentally enter package-root exports.

---

# 31. Protocols and ports

Integration and infrastructure contracts SHOULD prefer small typed Protocols or ports where structural typing is useful.

Examples:

~~~text
ArtifactStore
EngineAdapter
MetadataStore
ObservabilitySink
Executor
~~~

Protocols SHOULD model one capability.

Avoid universal interfaces such as:

~~~text
PyKitBackend
UniversalAdapter
EverythingProvider
~~~

---

# 32. Abstract base classes

ABCs MAY be used when lifecycle enforcement or shared runtime behavior is genuinely part of the contract.

They SHOULD NOT be introduced merely to make sibling framework class hierarchies look similar.

---

# 33. Enums and value objects

Bounded semantic strings SHOULD become enums or value objects when:

- the set is finite;
- validation matters;
- machine compatibility matters.

Examples:

~~~text
JoinType
WriteMode
RetryDisposition
WorkflowRunStatus
ValidationMode
~~~

Free-form strings remain appropriate for labels, extension namespaces, identifiers and descriptive metadata.

---

# 34. Identifiers

Identifiers SHOULD use domain-specific value types when identity semantics matter.

Examples:

~~~text
WorkflowRunId
TaskRunId
IngestionRunId
TransformationExecutionId
DatasetVersionId
~~~

Internally these may wrap strings or UUIDs.

The public type should preserve domain identity.

---

# 35. Equality and hashing

Immutable domain values SHOULD provide meaningful value equality.

Runtime objects representing active resources SHOULD NOT imply value equality unless explicitly documented.

Examples:

~~~text
Schema == Schema
    meaningful

TransformationPlan == TransformationPlan
    potentially meaningful

WorkflowRuntime == WorkflowRuntime
    generally not meaningful
~~~

---

# 36. Serialization

Portable domain objects MAY support explicit serialization.

Durable serialization MUST be:

- versioned;
- deterministic where required;
- safe from arbitrary code execution;
- independent from Python pickle.

Generic to_dict()/from_dict() helpers MAY exist, but durable compatibility MUST NOT depend on undocumented dictionary shape.

Persisted formats require explicit schema/version contracts.

---

# 37. Optional dependencies

Importing a package root MUST NOT require optional backends.

For example:

~~~python
import pytransformkit
~~~

must not require Pandas, Polars, PyArrow or DuckDB unless one becomes an intentional core dependency.

Sibling frameworks MUST remain optional.

Backend-specific imports SHOULD live in explicit namespaces or be resolved through a runtime registry/builder.

---

# 38. No implicit global registry mutation

Importing a module MUST NOT silently mutate a process-global registry merely because the package was imported.

Plugin and adapter registration SHOULD be explicit or performed by a documented runtime builder.

Plugin discovery SHOULD be opt-in, metadata-first where possible, side-effect controlled, and separated from activation.

---

# 39. Runtime builders

A RuntimeBuilder MAY be introduced when runtime composition becomes genuinely complex.

Example:

~~~python
runtime = (
    TransformationRuntimeBuilder()
    .with_engine(...)
    .with_observability(...)
    .build()
)
~~~

The builder creates a runtime.

It does not define transformation semantics.

---

# 40. Sync and async APIs

A framework MUST NOT expose async APIs merely for symmetry.

Async support should exist only where runtime behavior benefits from it.

If both sync and async entry points exist, semantics MUST be explicit, for example:

~~~text
run()
run_async()
~~~

or separate runtime types if cleaner.

No universal async convention is frozen until concrete framework needs justify one.

---

# 41. Context managers and resource ownership

Resources with explicit lifecycle SHOULD support context manager semantics where appropriate.

Example:

~~~python
with TransformationRuntime(...) as runtime:
    result = runtime.execute(plan)
~~~

Every public API accepting an external resource such as a database connection, file handle, pool, cloud client or event loop MUST document ownership as one of:

~~~text
BORROWED
OWNED
TRANSFERRED
~~~

A runtime MUST NOT close user-owned resources unless ownership was explicitly transferred.

---

# 42. Secret handling

Secrets SHOULD be represented through references or providers rather than embedded directly in serializable domain definitions.

Preferred:

~~~text
CredentialReference
SecretReference
~~~

Secret-bearing values MUST not leak through serialization, repr(), logging, diagnostics or manifests.

---

# 43. Logging

Libraries MUST NOT configure root logging at import time.

Core APIs should:

- use package loggers;
- avoid direct print statements;
- provide structured diagnostics through results/events where appropriate;
- redact sensitive values.

---

# 44. CLI relationship

CLI is an adapter over the public API.

Canonical direction:

~~~text
CLI
 ↓
Public API
 ↓
Domain / Runtime
~~~

Not:

~~~text
Public Python API
 ↓
CLI subprocess
~~~

CLI behavior must derive from the same contracts as Python usage.

---

# 45. Notebook relationship

Notebook ergonomics SHOULD use the same public API as production applications.

No notebook-only hidden execution model should exist.

This is especially important for PyTransformKit.

---

# 46. Human vs machine outputs

CLI and inspection surfaces SHOULD distinguish human-readable presentation from machine-readable contracts.

Machine-readable outputs MUST have explicit versioning when stability matters.

repr() MUST remain safe and MUST NOT leak secrets or dump entire large datasets by default.

---

# 47. Defaults

Defaults are part of the public API contract.

Defaults SHOULD be:

- safe;
- deterministic;
- unsurprising;
- local where possible;
- free from hidden cloud/network assumptions.

Production-impacting behavior SHOULD require explicit configuration when ambiguity would be dangerous.

---

# 48. Fail closed

For semantic and operational safety:

- unsupported capability → explicit failure;
- unknown plugin compatibility → explicit failure unless overridden;
- unresolved credential reference → explicit failure;
- ambiguous write outcome → explicit uncertainty;
- unknown transformation semantics → explicit failure.

Silent fallback is discouraged.

---

# 49. No hidden backend fallback

PyTransformKit MUST NOT silently switch engines because the requested engine lacks a capability.

Examples of forbidden implicit behavior:

~~~text
DuckDB → Pandas
Polars → Pandas
Arrow → Pandas
~~~

Fallback, if ever supported, must be policy-controlled and visible in the plan/result.

---

# 50. No hidden cross-framework promotion

PyIngestKit or PyTransformKit MUST NOT silently promote internal operations into PyWorkflowKit tasks.

PyTransformKit physical scans MUST NOT silently create PyIngestKit RAW artifacts or DatasetVersions.

Cross-framework participation is always explicit.

---

# 51. Public extension points

Extension points become public only when lifecycle, errors, compatibility and testing contracts are defined.

Possible extension points include:

~~~text
EngineAdapter
Reader
Writer
ArtifactStore
MetadataStore
Executor
ObservabilitySink
~~~

A public extension point MUST be independently contract-testable.

---

# 52. API stability classes

Before stable release, public symbols SHOULD be classifiable as:

~~~text
EXPERIMENTAL
PROVISIONAL
STABLE
DEPRECATED
~~~

Stable release documentation MUST identify the stable public facade.

After stable release, removing a stable symbol requires a documented deprecation path unless urgent security concerns justify immediate removal.

---

# 53. Clean-slate compatibility posture

The V2 redesign deliberately does not preserve legacy aliases merely for compatibility.

Examples to avoid in the new canonical APIs:

~~~text
Pipeline = IngestionLifecycle
Pipeline = TransformationPlan
Job = IngestionDefinition
Step = IngestionStage
~~~

Legacy releases remain available through historical versions and tags.

Clean-slate redesign should produce a clean API, not a renamed architecture covered in aliases.

---

# 54. API-first development

Before implementing a major public API, each project MUST write usage examples first.

At minimum:

1. minimal example;
2. realistic example;
3. failure example;
4. inspection example.

API review should ask:

- Can ownership be understood from imports?
- Is side-effect timing obvious?
- Are runtime resources explicit?
- Are outputs typed?
- Does the API require aliasing sibling concepts?
- Does it expose unnecessary implementation details?
- Can the same concept be used consistently from script, notebook and application code?

---

# 55. Cross-framework readability

A composed application should remain readable without manual aliasing.

Conceptually:

~~~python
from pyingestkit import IngestionDefinition, IngestionRuntime
from pytransformkit import TransformationPlan, TransformationRuntime
from pyworkflowkit import WorkflowDefinition, WorkflowRuntime
~~~

The exact integration DSL may evolve, but sibling root concepts must remain distinguishable by name.

---

# 56. PyIngestKit V2 public API direction

Target grammar:

~~~text
IngestionDefinition
    contains
SourceSpec + ingestion policies
    validates/derives
IngestionLifecycle / IngestionPlan
    executed by
IngestionRuntime
    producing
IngestionRun + IngestionResult
    referencing
DatasetVersion / PublishedDataset
~~~

The V2 API SHOULD NOT restore a generic Job → Pipeline → Step model as its primary abstraction.

---

# 57. PyTransformKit public API direction

Target grammar:

~~~text
TransformationPlan
    contains
TransformationGraph
    compiled into
LogicalPlan
    optimized into
OptimizedLogicalPlan
    lowered into
PhysicalPlan
    executed by
TransformationRuntime / EngineAdapter
    producing
TransformationResult
~~~

This vocabulary SHOULD replace the current generic Pipeline terminology before 1.0.

---

# 58. PyWorkflowKit V2 public API direction

Target grammar:

~~~text
WorkflowDefinition
    contains
TaskDefinition
    forms
WorkflowGraph
    compiled into
ExecutionPlan
    executed by
WorkflowRuntime
    creating
WorkflowRun
    containing
TaskRun
    containing
TaskAttempt
~~~

This semantic chain SHOULD remain explicit throughout the V2 API.

---

# 59. API conformance tests

Each project MUST eventually verify:

- exact public exports;
- import isolation;
- optional dependency isolation;
- constructor side-effect freedom;
- immutable declarative objects;
- stable root exceptions;
- no forbidden sibling imports;
- canonical public naming;
- decorator equivalence where decorators exist;
- runtime separation;
- resource ownership behavior.

A future ecosystem naming test SHOULD flag ambiguous newly exported root names such as:

~~~text
Pipeline
DAG
Job
Step
Run
Result
Context
Manager
Service
Plan
~~~

unless explicitly approved and domain-qualified.

---

# 60. API review checklist

Every new public API MUST answer:

1. Which bounded context owns this symbol?
2. Why is it public?
3. Is the name domain-qualified?
4. Is it declarative, runtime, integration, or infrastructure?
5. Does construction cause side effects?
6. Is mutation required?
7. Who owns external resources?
8. What is returned on success?
9. What happens on failure?
10. Is retryability explicit where relevant?
11. Is serialization expected?
12. Is it stable across optional backends?
13. Does it introduce a sibling dependency?
14. Could a smaller API express the same capability?
15. Can it be demonstrated in one readable example?

If these questions cannot be answered, the API is not ready for public exposure.

---

# 61. Anti-patterns

## 61.1 Active Definition

Rejected as the only execution model:

~~~python
definition = IngestionDefinition(...)
definition.run()
~~~

when run() hides runtime composition and resource ownership.

## 61.2 Mutable canonical Plan

Rejected:

~~~python
plan = TransformationPlan()
plan.steps.append(...)
plan.engine = "pandas"
~~~

Logical intent and runtime choice must remain separated.

## 61.3 Generic ecosystem base type

Rejected:

~~~python
class BasePipeline:
    ...
~~~

shared across ingestion, transformation and workflow only because each has graph-like structure.

## 61.4 Import-time registration

Rejected:

~~~python
import plugin
# silently mutates global registry
~~~

unless importing that module is itself an explicit documented activation operation.

## 61.5 Hidden execution during validation

Rejected:

~~~python
definition.validate()
# unexpectedly downloads source data
~~~

Environment-dependent checks belong to runtime preflight.

## 61.6 Bare dictionary contract

Rejected for stable cross-framework APIs:

~~~python
{"status": "ok", "id": "..."}
~~~

when a stable typed Result or Reference should exist.

---

# 62. Minimal API examples

## 62.1 PyIngestKit

Illustrative only:

~~~python
definition = IngestionDefinition(
    id="customers",
    source=HttpSourceSpec(...),
)

runtime = IngestionRuntime(...)
result = runtime.run(definition)

print(result.dataset_version)
~~~

## 62.2 PyTransformKit

Illustrative only:

~~~python
plan = (
    TransformationPlan.from_dataset(customers)
    .filter(col("active") == True)
    .select("customer_id", "country")
)

runtime = TransformationRuntime(...)
result = runtime.execute(plan)
~~~

## 62.3 PyWorkflowKit

Illustrative only:

~~~python
workflow = WorkflowDefinition(
    id="daily_customer_mart",
    tasks=(ingest_customers, transform_customers, publish_customers),
)

runtime = WorkflowRuntime(...)
result = runtime.run(workflow)
~~~

These examples define intended readability, not frozen signatures.

---

# 63. Advanced capabilities

Advanced APIs SHOULD be additive rather than replacing the simple path.

A beginner should not need to understand plugin registries, persistence repositories, optimizer rules, executor capability objects or physical-plan internals to run a minimal example.

Advanced users MAY receive explicit escape hatches such as:

- native engine handle access;
- custom adapter registration;
- custom executor;
- custom artifact store;
- raw plan inspection.

Escape hatches MUST be clearly labeled and MUST NOT silently weaken core invariants.

---

# 64. Machine-readable inspection

Major definitions, plans and runs SHOULD support structured inspection where useful.

Possible verbs include:

~~~text
describe()
inspect()
explain()
to_manifest()
~~~

Persisted machine formats require explicit versioning.

Method names must reflect semantics and must not imply execution when none occurs.

---

# 65. Documentation requirement

Every stable root-level public type MUST document:

- purpose;
- bounded-context ownership;
- lifecycle;
- construction;
- execution relationship;
- thread/process safety where relevant;
- serialization status;
- resource ownership;
- stability status;
- at least one usage example.

---

# 66. Definition of ecosystem API coherence

The ecosystem is coherent when a user can predict meaning from naming:

~~~text
IngestionDefinition
    declarative ingestion intent

TransformationPlan
    declarative transformation intent

WorkflowDefinition
    declarative workflow intent

IngestionRun
    ingestion lifecycle instance

TransformationExecution
    transformation compute execution

WorkflowRun
    workflow lifecycle instance
~~~

Users should not need repository knowledge to distinguish these concepts.

---

# 67. Normative API invariants

### API-INV-01 — Authoring is side-effect free

Creating definitions and plans does not execute workloads.

### API-INV-02 — Runtime is explicit

Execution occurs through runtime/application services.

### API-INV-03 — Declarative domain values are immutable by default

Mutation requires explicit justification.

### API-INV-04 — Public names reveal bounded context

Generic ambiguous package-root names are discouraged.

### API-INV-05 — Decorators are syntax, not semantics

Decorator APIs compile into canonical domain models.

### API-INV-06 — Optional dependencies remain optional

Core import never requires optional engines or sibling frameworks.

### API-INV-07 — Public results are typed

Stable lifecycle APIs do not return undocumented dictionaries.

### API-INV-08 — Errors preserve origin

Cross-framework adapters never erase failure provenance.

### API-INV-09 — Resource ownership is explicit

Borrowed, owned and transferred resources are distinguishable.

### API-INV-10 — Validation is layered

Structural validation, semantic validation and runtime preflight remain distinct.

### API-INV-11 — Execution verbs are intentional

execute is compute-oriented; run is lifecycle-oriented.

### API-INV-12 — Root exports are curated

Implementation details do not become public accidentally.

### API-INV-13 — No hidden fallback

Backends and sibling integrations remain explicit.

### API-INV-14 — Serialization is explicit and versioned

Durable compatibility does not depend on pickle or accidental dictionary shape.

### API-INV-15 — Clean-slate means clean API

Legacy aliases are not reintroduced unless they serve a new semantic purpose.

---

# 68. Acceptance criteria

This specification is successfully reflected in implementation when:

1. the three packages expose domain-specific root concepts;
2. constructors are side-effect free;
3. canonical declarative objects are immutable;
4. runtime execution is separated from definitions and plans;
5. package-root exports are explicitly tested;
6. optional dependencies are isolated;
7. no sibling framework is required for core import;
8. cross-framework adapters use public contracts only;
9. public result types are structured and typed;
10. root exception hierarchies are documented;
11. resource ownership is explicit;
12. runtime preflight is distinct from semantic validation;
13. decorator APIs compile into canonical domain values;
14. no generic Pipeline root type is required;
15. PyTransformKit uses TransformationPlan and TransformationGraph;
16. PyIngestKit V2 uses IngestionDefinition and IngestionLifecycle;
17. PyWorkflowKit V2 uses WorkflowDefinition and WorkflowGraph;
18. public API examples execute in CI;
19. architecture tests detect forbidden imports and ambiguous exports;
20. stable releases publish a machine-checkable public API manifest.

---

# 69. Final design statement

The PyKit V2 public API should feel coherent because its grammar is predictable, not because every framework exposes identical abstractions.

The target experience is:

~~~text
DEFINE ingestion
EXECUTE transformation
RUN workflow

while preserving:

IngestionDefinition
TransformationPlan
WorkflowDefinition
~~~

The most important API boundary is:

~~~text
DECLARATION
    !=
EXECUTION
~~~

and the most important naming rule is:

> **A public type should tell the user what it means before the user has to discover where it came from.**

This specification is the baseline for the future concrete documents:

~~~text
PYINGESTKIT_V2_PUBLIC_API_SPEC.md
PYTRANSFORMKIT_V1_PUBLIC_API_SPEC.md
PYWORKFLOWKIT_V2_PUBLIC_API_SPEC.md
~~~
