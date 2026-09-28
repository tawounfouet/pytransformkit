# PyKit Ecosystem V2 - Reference Application Specification

> **Status:** NORMATIVE REFERENCE APPLICATION BASELINE
> **Architecture generation:** V2
> **Date:** 2026-09-28
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit
> **Reference scenario:** Customer 360
> **Purpose:** executable proof of ecosystem composition

## 1. Purpose

This document defines the canonical V2 reference application used to prove that PyIngestKit, PyTransformKit and PyWorkflowKit compose correctly without collapsing their bounded contexts.

The reference application is not merely a tutorial. It is executable architecture evidence.

> **The reference application must demonstrate composition through public contracts while preserving each framework's semantic ownership.**

## 2. Reference domain

The application ingests two source datasets, customers and orders, and produces a customer_mart dataset.

~~~text
customers source -> PyIngestKit -> customers DatasetVersion
orders source    -> PyIngestKit -> orders DatasetVersion
                               |
                               v
                        PyTransformKit
                               |
                               v
                    customer_mart Resource
                               |
                               v
                         PyIngestKit
                           Publish
                               |
                               v
                 customer_mart DatasetVersion
~~~

The full sequence is coordinated by PyWorkflowKit.

## 3. Canonical responsibility split

~~~text
PyIngestKit
    HOW TO INGEST

PyTransformKit
    HOW TO TRANSFORM DATA

PyWorkflowKit
    HOW TO EXECUTE WORKLOAD DEPENDENCIES RELIABLY
~~~

The example MUST NOT move these responsibilities between frameworks for convenience.

## 4. Workflow-level view

~~~text
WorkflowDefinition daily_customer_mart
    |-- ingest_customers
    |-- ingest_orders
    |-- build_customer_mart
    `-- publish_customer_mart

ingest_customers --+
                   +--> build_customer_mart --> publish_customer_mart
ingest_orders -----+
~~~

WorkflowKit owns this workload DAG. It does not own internal ingestion lifecycle stages or transformation nodes.

## 5. Canonical repository layout

~~~text
examples/customer_360/
|-- README.md
|-- pyproject.toml
|-- config/
|   |-- local.toml
|   `-- test.toml
|-- data/input/
|   |-- customers.csv
|   `-- orders.csv
|-- ingestion/
|   |-- customers.py
|   `-- orders.py
|-- transformations/
|   `-- customer_mart.py
|-- workflows/
|   `-- daily_customer_mart.py
|-- runtime/
|   |-- bootstrap.py
|   `-- resources.py
|-- scripts/
|   |-- run_local.py
|   |-- inspect_lineage.py
|   `-- replay_demo.py
|-- fixtures/
|   |-- contracts/
|   |-- expected/
|   `-- failures/
`-- tests/
    |-- test_happy_path.py
    |-- test_retry.py
    |-- test_unknown_outcome.py
    |-- test_recovery.py
    |-- test_serialization.py
    |-- test_lineage.py
    |-- test_observability.py
    `-- test_security_boundaries.py
~~~

## 6. Source datasets

The customers source SHOULD contain customer_id, email, country, created_at and status.

The orders source SHOULD contain order_id, customer_id, ordered_at, amount, currency and status.

All fixture data MUST be synthetic, deterministic and non-sensitive.

## 7. Customer mart output

The logical output SHOULD expose:

~~~text
customer_id
email
country
customer_status
first_order_at
last_order_at
paid_order_count
paid_revenue
has_paid_order
~~~

The transformation SHOULD project customer fields, select paid orders, aggregate orders by customer, derive first and last paid-order timestamps, calculate count and revenue, left join aggregates onto customers, derive has_paid_order and apply explicit null/default semantics.

## 8. Ingestion ownership

customers and orders are authored as PyIngestKit IngestionDefinition objects.

Each IngestionRun owns source acquisition, RAW capture, decode, ingestion validation, DatasetVersion creation, source publication and provenance.

Business transformation logic MUST NOT be implemented inside ingestion core.

## 9. Transformation ownership

customer_mart is authored as a PyTransformKit TransformationPlan.

It owns logical input requirements, projection, filtering, aggregation, join, derivation, logical schema and logical lineage.

It does not own workflow retry, scheduling, RAW or DatasetVersion lifecycle.

## 10. Workflow ownership

daily_customer_mart is authored as a PyWorkflowKit WorkflowDefinition.

WorkflowKit owns task dependencies, TaskRun, TaskAttempt, workload retry, timeout, cancellation, recovery and workflow outcome.

It does not own ingestion provenance or transformation expressions.

## 11. Canonical public authoring vocabulary

~~~python
from pyingestkit import IngestionDefinition
from pytransformkit import TransformationPlan
from pyworkflowkit import WorkflowDefinition
~~~

The reference application is a proving ground for public API ergonomics.

## 12. Public contracts only

The application MUST NOT depend on private framework modules, private graph nodes, private persistence entities or internal repositories.

Only package public APIs and official integration namespaces may cross framework boundaries.

## 13. Ingestion result handoff

A successful source ingestion SHOULD expose at least IngestionRunId, DatasetVersionReference, relevant ResourceReference or ArtifactReference, CorrelationContext, diagnostics and provenance references.

Workflow state stores portable references, not decoded DataFrames.

Canonical handoff:

~~~text
PyIngestKit
    -> DatasetVersionReference
    -> PyTransformKit integration ACL
    -> InputBinding
~~~

## 14. Transformation plan and engine neutrality

The same customer_mart TransformationPlan SHOULD run on at least two official engines when capabilities permit.

The initial reference target SHOULD be Pandas and Polars.

The comparison oracle is normalized logical output, not native object equality.

## 15. Transformation result

A successful transformation execution SHOULD expose TransformationExecutionId, status, output ResourceReference or ArtifactReference, lineage references, diagnostics, engine identity, plan fingerprint and CorrelationContext.

It SHOULD NOT automatically create a governed DatasetVersion.

## 16. Write versus publish

~~~text
Transformation output write
    !=
Dataset publication
~~~

PyTransformKit produces a physical output. PyIngestKit then publishes that output as a customer_mart DatasetVersion.

## 17. Publication step

publish_customer_mart SHOULD validate the transformation output reference, preserve TransformationExecutionReference, create a governed DatasetVersion, emit publication provenance and return DatasetVersionReference.

## 18. Workflow integration adapters

WorkflowKit invokes sibling runtimes through official adapters:

~~~text
PyWorkflowKit -> PyIngestKit
PyWorkflowKit -> PyTransformKit
~~~

Sibling executions are treated as workloads. WorkflowKit does not inspect their internal DAGs or lifecycle stages.

## 19. Durable task outputs

Preferred task outputs are DatasetVersionReference, IngestionExecutionReference, TransformationExecutionReference, ExternalRunRef, ArtifactReference and ResourceReference.

DataFrames, open connections, engine sessions and provider clients MUST NOT become durable workflow outputs.

## 20. Execution identity

A happy-path run SHOULD create distinct WorkflowRunId, TaskRunId, TaskAttemptId, IngestionRunId and TransformationExecutionId values.

These identities MUST never be collapsed into one universal run ID.

## 21. Correlation and causation

One CorrelationId SHOULD connect the complete end-to-end operation while native execution IDs remain distinct.

When a TaskAttempt directly launches a sibling execution, causation SHOULD link the child execution to that TaskAttempt.

## 22. End-to-end provenance

~~~text
customers source -> RAW -> customers DatasetVersion
orders source    -> RAW -> orders DatasetVersion

customers DatasetVersion --+
                           +--> TransformationExecution
orders DatasetVersion -----+          |
                                      v
                              customer_mart Resource
                                      |
                                      v
                                  publication
                                      |
                                      v
                         customer_mart DatasetVersion
~~~

## 23. Workflow execution lineage

The application SHOULD preserve WorkflowRun -> TaskRun -> TaskAttempt -> ExternalRunRef -> native sibling execution.

Data lineage and execution lineage compose through stable references without one universal lineage owner.

## 24. Field lineage

The transformation SHOULD prove lineage for customer_id, email, country, paid_order_count, paid_revenue, first_order_at, last_order_at and has_paid_order.

For example, orders.amount -> SUM -> customer_mart.paid_revenue and orders.order_id -> COUNT -> customer_mart.paid_order_count.

The suite SHOULD distinguish value derivation, row-selection dependency, grouping dependency and join dependency.

## 25. Observability

The happy path SHOULD emit structured evidence for workflow start, task attempts, ingestion runs, DatasetVersion creation, transformation planning/execution, publication and workflow completion.

Metrics MUST avoid high-cardinality execution IDs by default. Trace IDs remain observational and never replace native execution IDs.

## 26. Manifests and wire fixtures

The example SHOULD retain portable fixtures for DatasetVersionReference, ResourceReference, execution references, ExternalRunRef, CorrelationContext, FailureEvidence, EventEnvelope, LineageRecord and execution manifests.

At least one test SHOULD serialize, persist, restart, decode and resume or reconcile using only durable contracts.

Pickle, cloudpickle and dill MUST NOT be required for durable cross-framework state.

## 27. Happy-path acceptance scenario

Given valid customers and orders fixtures:

1. both sources are ingested;
2. two DatasetVersions are produced;
3. the transformation consumes those exact versions;
4. customer_mart is computed;
5. transformation output is written;
6. PyIngestKit publishes the output;
7. customer_mart DatasetVersion is created;
8. WorkflowRun succeeds;
9. all native execution IDs remain inspectable;
10. end-to-end lineage is traversable.

## 28. Transient ingestion failure

The suite SHOULD simulate a transient acquisition failure.

PyIngestKit may perform only bounded safe provider retry. WorkflowKit retries the ingestion workload only when the IngestionRun itself fails according to WorkflowKit policy.

Nested retry counts must remain observable.

## 29. Transformation failure

A controlled unsupported-capability scenario SHOULD demonstrate:

~~~text
engine lacks capability
    -> PyTransformKit structured failure
    -> WorkflowKit TaskAttempt failure
~~~

No hidden engine fallback is allowed unless explicitly configured.

## 30. Unknown publication outcome

The reference application MUST demonstrate:

~~~text
publication request sent
    -> provider may have committed
    -> acknowledgement lost
    -> UNKNOWN_OUTCOME
    -> reconciliation
~~~

Blind re-publication before reconciliation is a conformance failure.

## 31. Recovery

The suite SHOULD simulate process loss after a sibling execution starts.

WorkflowRun state and ExternalRunRef are persisted, the process is restarted, and the runtime inspects or reconciles the existing external execution before deciding whether new work is safe.

Recovery is not rerun.

## 32. Cancellation

A controlled long-running workload SHOULD exercise cancellation requested, accepted, confirmed, unsupported and unconfirmed states.

Cancellation request is not equivalent to confirmed cancellation.

## 33. Replay

PyIngestKit replay SHOULD demonstrate:

~~~text
original IngestionRun
    -> preserved RAW
    -> new replay IngestionRun
~~~

Replay creates a new execution identity while preserving replay provenance.

## 34. Security scenarios

Negative cases SHOULD include credential-bearing locator rejection or redaction, path traversal rejection, unknown plugin non-activation, non-executable wire decoding and absence of secrets from logs/manifests.

All credentials used by fixtures must be synthetic or ephemeral.

## 35. Local reference profile

The baseline SHOULD run without external SaaS dependencies.

A suitable local profile may use CSV fixtures, local filesystem resource/artifact storage, Pandas or Polars, in-memory or SQLite workflow metadata and local JSON manifests.

## 36. Optional provider profile

A secondary profile MAY add PostgreSQL, S3-compatible storage, Snowflake, remote HTTP sources or OpenTelemetry.

These profiles supplement rather than replace deterministic local conformance.

## 37. Built-artifact proof

At least one CI path SHOULD build framework wheels, install them in a clean environment, install required extras and execute customer_360.

The reference application validates the real consumer installation path.

## 38. Public API feedback loop

If the reference application repeatedly requires private imports or awkward internal conversions, that is evidence that the public API or integration contract is incomplete.

The reference application may therefore drive API refinement before stable release.

## 39. No artificial symmetry

The example MUST NOT instantiate public TransformationGraph, WorkflowGraph or IngestionLifecycle types merely to satisfy vocabulary symmetry.

A public object is used only when it owns independent semantics, lifecycle or behavior.

## 40. Minimum CI scenarios

~~~text
happy path
Pandas execution
Polars execution
wire round trip
lineage query
transient retry
unknown publication outcome
recovery after process loss
security negative cases
built-wheel installation
~~~

## 41. Acceptance criteria

The reference application is conformant when:

1. customers and orders ingest through PyIngestKit;
2. immutable DatasetVersionReferences are produced;
3. PyTransformKit consumes those references through an official integration boundary;
4. one TransformationPlan computes customer_mart;
5. at least two engines produce equivalent logical results;
6. transformation output remains distinct from publication;
7. PyIngestKit publishes customer_mart as a new DatasetVersion;
8. PyWorkflowKit coordinates the workload DAG;
9. WorkflowKit does not inspect sibling internal DAGs;
10. native execution IDs remain distinct;
11. one CorrelationId connects the operation;
12. data lineage and execution lineage compose;
13. wire contracts survive process restart;
14. large data travels by reference;
15. retry is bounded and observable;
16. UNKNOWN_OUTCOME triggers reconciliation before unsafe retry;
17. recovery preserves existing execution identity;
18. secrets never appear in durable references or telemetry;
19. the scenario runs against built package artifacts;
20. CI continuously proves happy and critical failure paths.

## 42. Normative invariants

### REF-INV-01 - Public contracts only

The reference application integrates through public contracts, never private internals.

### REF-INV-02 - Semantic ownership is preserved

Ingestion, transformation and workflow semantics remain in their owning frameworks.

### REF-INV-03 - Data crosses boundaries by reference

Large native data objects do not become durable workflow state.

### REF-INV-04 - Transformation output is not publication

Physical compute output and governed DatasetVersion publication remain distinct.

### REF-INV-05 - WorkflowKit treats siblings as workloads

It does not schedule their internal stages or transformation nodes.

### REF-INV-06 - Native execution identities remain distinct

Workflow, task, ingestion and transformation IDs are never collapsed.

### REF-INV-07 - Correlation spans the ecosystem

One broader CorrelationId links the operation without replacing local identity.

### REF-INV-08 - Retry ownership remains singular

Adapters do not introduce hidden whole-workload retry amplification.

### REF-INV-09 - Uncertainty is preserved

UNKNOWN_OUTCOME is reconciled before unsafe replay.

### REF-INV-10 - Recovery is not rerun

Existing external execution references are reused during recovery.

### REF-INV-11 - Lineage composes without universal ownership

Framework-owned lineage models are linked through stable references.

### REF-INV-12 - The example is release evidence

The reference application runs continuously in CI against built artifacts.

## 43. Final architecture statement

The Customer 360 reference application is the executable proof that PyKit V2 is an ecosystem rather than three adjacent libraries.

~~~text
PyIngestKit
    produces governed data versions

PyTransformKit
    consumes data references and produces transformation outputs

PyWorkflowKit
    coordinates reliable workload execution

Application composition
    connects them through public contracts
~~~

without shared private models, dependency cycles or semantic duplication.

> **If the architecture cannot be demonstrated cleanly in the reference application using only public contracts, the architecture is not ready to freeze.**

This specification is the baseline for:

- PYKIT_ECOSYSTEM_V2_RELEASE_COMPATIBILITY_AND_VERSIONING_POLICY.md
- PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md
- PYKIT_ECOSYSTEM_V2_END_TO_END_ACCEPTANCE_CRITERIA.md
- PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md
- PYINGESTKIT_V2_TARGET_ARCHITECTURE.md
- PYWORKFLOWKIT_V2_TARGET_ARCHITECTURE.md