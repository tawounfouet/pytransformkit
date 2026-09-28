# PyKit Ecosystem V2 — Lineage, Provenance and Traceability Model

> **Status:** NORMATIVE LINEAGE AND PROVENANCE BASELINE
> **Architecture generation:** V2
> **Date:** 2026-09-28
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit
> **Compatibility posture:** clean-slate lineage model
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_SHARED_CONTRACTS_AND_REFERENCE_MODEL.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_EXECUTION_IDENTITY_AND_CORRELATION_MODEL.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_ERROR_FAILURE_RETRY_AND_UNCERTAINTY_MODEL.md
> **Depends on:** PYKIT_ECOSYSTEM_V2_DATASET_RESOURCE_AND_ARTIFACT_INTEROPERABILITY.md

---

# 1. Purpose

This document defines the V2 model for:

- lineage;
- provenance;
- execution traceability;
- source-to-dataset traceability;
- transformation derivation;
- field-level lineage;
- workflow/task execution lineage;
- cross-framework lineage composition;
- replay/recovery traceability;
- lineage persistence and interchange.

The governing principle is:

> **Each framework owns the lineage semantics of its own bounded context; the ecosystem composes lineage through stable references rather than one universal lineage graph.**

---

# 2. Why lineage must remain domain-specific

The word lineage is frequently used to describe several different questions.

Examples:

~~~text
Where did this DatasetVersion come from?

Which RAW artifact produced it?

Which transformation created this output?

Which input columns contributed to this field?

Which TaskAttempt launched this transformation?

Which WorkflowRun published this dataset?

Which external query physically executed the computation?
~~~

These are related questions, but they do not belong to one single semantic model.

The V2 ecosystem distinguishes at least three primary lineage domains:

~~~text
PyIngestKit
    source / artifact / dataset provenance

PyTransformKit
    logical / dataset / field transformation lineage

PyWorkflowKit
    workflow / task / attempt execution lineage
~~~

---

# 3. Canonical lineage domains

The ecosystem defines:

~~~text
INGESTION PROVENANCE
TRANSFORMATION LINEAGE
EXECUTION LINEAGE
~~~

These domains may be connected.

They MUST NOT be collapsed into one generic graph whose edges lose domain meaning.

---

# 4. PyIngestKit provenance

PyIngestKit owns provenance describing how external source evidence became a governed dataset version.

Canonical shape:

~~~text
External Source
      ↓ acquire
Source Resource
      ↓
RAW Artifact
      ↓ decode
Decoded Dataset
      ↓ validate
Accepted Data
      ↓ version
DatasetVersion
      ↓ publish
PublishedDataset
~~~

PyIngestKit provenance answers questions such as:

- which source was acquired;
- when it was acquired;
- which RAW artifact preserves source evidence;
- which checksum identifies that evidence;
- which ingestion run created the version;
- which validation decisions applied;
- which DatasetVersion was produced;
- which publication target received it.

---

# 5. PyTransformKit lineage

PyTransformKit owns logical derivation lineage.

Canonical shape:

~~~text
Input Dataset(s)
      ↓
TransformationPlan
      ↓
TransformationGraph
      ↓
LogicalPlan
      ↓
TransformationExecution
      ↓
Output Dataset(s)
~~~

It also owns field-level derivation:

~~~text
customers.customer_id ─────┐
                           ├── expression ──► customer_key
customers.country ─────────┘
~~~

PyTransformKit answers questions such as:

- which logical datasets feed this output;
- which transformations were applied;
- which expressions produced a field;
- which columns were dropped, renamed, cast or derived;
- which joins connected inputs;
- which aggregations/window operations influenced output;
- which logical plan fingerprint describes the execution.

---

# 6. PyWorkflowKit execution lineage

PyWorkflowKit owns operational lineage.

Canonical shape:

~~~text
WorkflowDefinition
      ↓
WorkflowRun
      ↓
TaskRun
      ↓
TaskAttempt
      ↓
ExternalRunRef
~~~

It answers questions such as:

- which workflow started the workload;
- which task represented the work;
- which attempt actually executed;
- which retry produced the successful attempt;
- which external run was invoked;
- which task caused another task to become ready;
- which task outputs/references were handed downstream.

---

# 7. Provenance versus lineage

The ecosystem uses the terms deliberately.

## Provenance

Primarily answers:

> Where did this object come from?

Typical PyIngestKit example:

~~~text
DatasetVersion customers@52
    came from
RAW artifact A-10
    acquired from
HTTP source S-1
~~~

## Lineage

Primarily answers:

> How was this object derived or operationally produced?

Typical PyTransformKit example:

~~~text
customer_mart.country_code
    derived from
customers.country
    through
normalize_country()
~~~

## Traceability

Answers:

> Can we connect the relevant evidence end-to-end?

Example:

~~~text
WorkflowRun
    → TaskAttempt
    → IngestionRun
    → DatasetVersion
    → TransformationExecution
    → PublishedDataset
~~~

---

# 8. Traceability is composition

Traceability is not a fourth universal domain model.

It is the ability to traverse links across multiple owned models.

Conceptually:

~~~text
PyWorkflowKit execution evidence
        ↕
PyIngestKit provenance
        ↕
PyTransformKit lineage
~~~

Composition occurs through references and correlation.

---

# 9. Canonical provenance chain

For ingestion, a canonical chain is:

~~~text
SourceReference
    ↓
AcquisitionEvidence
    ↓
RawArtifactReference
    ↓
DecodeEvidence
    ↓
ValidationEvidence
    ↓
DatasetVersionReference
    ↓
PublicationEvidence
~~~

Not every implementation must persist a concrete object for every intermediate step, but the semantics must remain representable.

---

# 10. Canonical transformation lineage chain

For transformation:

~~~text
Input DatasetReference(s)
    ↓
TransformationPlan fingerprint
    ↓
Transformation node(s)
    ↓
Logical Dataset(s)
    ↓
TransformationExecutionReference
    ↓
Output ResourceReference(s)
~~~

Field-level lineage may additionally connect input fields to output fields.

---

# 11. Canonical workflow lineage chain

For workflow execution:

~~~text
WorkflowRunReference
    ↓
TaskRunReference
    ↓
TaskAttemptReference
    ↓
ExternalRunRef
    ↓
Provider execution reference
~~~

This chain describes operational causality, not data derivation.

---

# 12. Lineage entity taxonomy

The ecosystem recognizes lineage-capable entities such as:

~~~text
SourceReference
ResourceReference
ArtifactReference
DatasetReference
DatasetVersionReference

TransformationPlanReference / fingerprint
TransformationExecutionReference

WorkflowExecutionReference
TaskRunReference
TaskAttemptReference
ExternalRunRef

FieldReference
ExpressionReference
~~~

Exact DTOs may differ by framework.

Semantic ownership remains explicit.

---

# 13. Lineage edge taxonomy

Lineage edges MUST have meaning.

Recommended semantic relationships include:

~~~text
ACQUIRED_FROM
PRESERVED_AS
DECODED_FROM
VALIDATED_AS
VERSIONED_AS
PUBLISHED_AS

CONSUMED
PRODUCED
DERIVED_FROM
RENAMED_FROM
CAST_FROM
FILTERED_BY
JOINED_WITH
AGGREGATED_FROM
WINDOWED_FROM

EXECUTED_BY
ATTEMPT_OF
CAUSED
RETRIED_AS
RESUMED_AS
REPLAYED_FROM
OBSERVES
RECONCILES
~~~

A generic edge named RELATED_TO is insufficient for normative lineage.

---

# 14. Edge ownership

The producer of lineage owns the meaning of its edges.

Examples:

~~~text
PyIngestKit
    ACQUIRED_FROM
    PRESERVED_AS
    VERSIONED_AS
    PUBLISHED_AS

PyTransformKit
    CONSUMED
    PRODUCED
    DERIVED_FROM
    JOINED_WITH
    AGGREGATED_FROM

PyWorkflowKit
    ATTEMPT_OF
    EXECUTED_BY
    RETRIED_AS
~~~

Cross-framework viewers may compose these edge sets.

They should not redefine them.

---

# 15. No universal graph schema

The V2 architecture deliberately rejects a mandatory universal LineageGraph domain object shared by all frameworks.

A shared presentation layer MAY aggregate:

~~~text
LineageNode
LineageEdge
~~~

for visualization.

That representation is a projection.

It is not the canonical source model for all frameworks.

---

# 16. Lineage references, not object embedding

Cross-framework lineage links SHOULD use portable references.

Preferred:

~~~text
TransformationExecution
    input = DatasetVersionReference customers@52
~~~

Rejected:

~~~text
TransformationExecution
    input = PyIngestKit ORM DatasetVersion instance
~~~

The same rule applies to workflow and artifact links.

---

# 17. Ingestion source provenance

Source provenance SHOULD preserve enough information to identify the acquisition origin.

Typical evidence:

~~~text
source identity
source kind
resource reference
acquisition timestamp
provider metadata
watermark/cursor?
source version/etag?
checksum?
IngestionRunId
CorrelationId
~~~

Credential material MUST NOT be persisted in provenance.

---

# 18. RAW provenance

A RAW artifact SHOULD link to:

~~~text
SourceReference
IngestionRunId
AcquisitionEvidence
ArtifactReference
checksum
capture timestamp
~~~

RAW provenance SHOULD be immutable once established.

---

# 19. Decode provenance

Decode provenance MAY record:

~~~text
input RAW artifact
decoder/parser kind
format
encoding
schema mapping
decode policy
output schema fingerprint
diagnostics
~~~

The purpose is to explain interpretation of source representation.

It does not describe business transformation semantics.

---

# 20. Validation provenance

Validation evidence SHOULD capture:

~~~text
validation contract/policy identifier
input reference
validation result
quality metrics
accepted/rejected status
report artifact reference?
~~~

If validation policy changes, historical DatasetVersion provenance should retain which policy/version was applied.

---

# 21. DatasetVersion provenance

DatasetVersion SHOULD be traceable to:

~~~text
IngestionRunId
input source/artifact references
schema fingerprint
content fingerprint
validation evidence
publication evidence
optional transformation execution reference
~~~

If data was transformed before publication, the transformation execution reference should be preserved.

---

# 22. Publication provenance

Publication SHOULD record:

~~~text
DatasetVersionReference
publication target
publication execution reference
publication timestamp
published locator/reference
publication policy
correlation ID
~~~

Where publication outcome was reconciled after uncertainty, that reconciliation evidence SHOULD also be linkable.

---

# 23. Replay provenance

Replay creates new execution lineage.

Example:

~~~text
RAW Artifact A-10
    ↓ replayed by
IngestionRun I-205
    ↓
DatasetVersion customers@53
~~~

The replay run SHOULD preserve:

~~~text
REPLAYED_FROM → A-10
optional original IngestionRunReference
~~~

Replay must not erase the original acquisition history.

---

# 24. Reacquisition provenance

Reacquiring a source is not the same as replay.

~~~text
same SourceSpec
    ↓ new external acquisition
new RAW Artifact
~~~

This creates new acquisition provenance even if source content is identical.

Content fingerprints MAY show equivalence.

---

# 25. Transformation dataset lineage

PyTransformKit SHOULD capture dataset-level edges:

~~~text
input Dataset A
input Dataset B
      ↓
JoinTransformation
      ↓
Dataset C
      ↓
FilterTransformation
      ↓
Dataset D
~~~

This graph represents logical derivation.

It is independent from whether A/B/C/D are physically materialized.

---

# 26. FieldReference

Field-level lineage requires stable field references.

Conceptually:

~~~text
FieldReference
    dataset_id
    field_path
    schema_fingerprint?
~~~

Nested structures may require field paths such as:

~~~text
customer.address.country
items[].product_id
~~~

Exact path syntax must be frozen in a field-lineage contract before stable serialization.

---

# 27. Field lineage

PyTransformKit SHOULD represent field derivation when semantically knowable.

Examples:

~~~text
output.customer_key
    DERIVED_FROM
input.customer_id

output.full_name
    DERIVED_FROM
input.first_name
input.last_name
~~~

Field lineage may be one-to-one, many-to-one, one-to-many or unknown.

---

# 28. Direct lineage

Direct lineage means an output field directly preserves input semantics.

Example:

~~~text
select customer_id
~~~

Relationship:

~~~text
output.customer_id
    DERIVED_FROM
input.customer_id
~~~

A projection should not unnecessarily lose direct lineage.

---

# 29. Rename lineage

Rename should preserve derivation explicitly.

~~~text
input.customer_id
    ↓ rename
output.customer_key
~~~

Recommended relationship:

~~~text
RENAMED_FROM
~~~

with fallback semantic relation:

~~~text
DERIVED_FROM
~~~

---

# 30. Cast lineage

A cast preserves source-field dependency while changing logical type.

~~~text
input.amount STRING
    ↓ cast DECIMAL
output.amount DECIMAL
~~~

Lineage should preserve:

~~~text
CAST_FROM
input.amount
~~~

and optionally the cast expression/type metadata.

---

# 31. Derived expression lineage

For:

~~~text
total = quantity * unit_price
~~~

lineage is:

~~~text
output.total
    DERIVED_FROM
input.quantity
input.unit_price
~~~

The expression AST MAY be referenced or fingerprinted for richer traceability.

---

# 32. Filter lineage

Filtering changes row membership rather than field derivation.

Example:

~~~text
filter country == "FR"
~~~

Dataset lineage SHOULD record the filter operation.

Field lineage does not necessarily add country as a source for every output field.

A separate row-selection dependency MAY indicate:

~~~text
Dataset D
    FILTERED_BY
field country
~~~

This distinction matters.

---

# 33. Join lineage

Join produces lineage from multiple input datasets.

Example:

~~~text
customers
orders
    ↓ join on customer_id
customer_orders
~~~

Dataset lineage records both inputs.

Field lineage records each output field's originating side or expression.

Join predicate fields may also be recorded as operational dependencies.

---

# 34. Aggregation lineage

Aggregation has field and grouping dependencies.

Example:

~~~text
group by country
sum(revenue) as revenue_total
~~~

Lineage should represent:

~~~text
output.country
    DERIVED_FROM input.country

output.revenue_total
    AGGREGATED_FROM input.revenue

dataset grouping dependency
    input.country
~~~

---

# 35. Window lineage

Window functions require:

~~~text
value input
partition-by fields
order-by fields
frame semantics
~~~

Field-level lineage MAY distinguish value derivation from ordering/partition dependencies.

At minimum, all semantically required dependencies should be discoverable.

---

# 36. Deduplication lineage

Deduplication changes row selection.

Key fields used to determine duplicates are operational dependencies.

Output fields may remain direct derivations from the surviving input rows.

Lineage should not falsely claim that every output field was computed from deduplication key fields.

---

# 37. Sort lineage

Sort affects row order, not field values.

Lineage SHOULD distinguish ordering dependency from value derivation.

This helps avoid over-reporting field ancestry.

---

# 38. Pivot and unpivot lineage

Reshape operations may generate output fields dynamically.

The lineage model SHOULD support:

- source value field;
- pivot key field;
- generated output field;
- aggregation when applicable.

Where static field-level lineage cannot be fully known before execution, lineage MAY be marked dynamic.

---

# 39. Dynamic lineage

Some transformations cannot determine exact field lineage statically.

Examples:

~~~text
dynamic pivot
runtime-discovered JSON keys
user-defined function with opaque logic
external SQL fragment
plugin transformation
~~~

Canonical lineage confidence values MAY include:

~~~text
EXACT
DECLARED
INFERRED
DYNAMIC
UNKNOWN
~~~

Unknown lineage MUST be represented honestly rather than fabricated.

---

# 40. UDF lineage

A user-defined function SHOULD declare field dependencies where possible.

Example:

~~~text
udf inputs = first_name, last_name
output = normalized_name
~~~

If the function is opaque and dependencies cannot be proven, lineage should fall back to declared or unknown confidence.

---

# 41. External SQL lineage

If PyTransformKit permits SQL expressions or external SQL plans, lineage extraction MAY be partial.

The system SHOULD record:

- SQL/reference fingerprint;
- declared inputs;
- parsed field lineage where reliable;
- confidence.

It MUST NOT claim exact lineage when parser semantics are incomplete.

---

# 42. Logical versus physical lineage

Logical lineage describes semantic derivation.

Physical lineage describes where computation ran or which physical resources were read/written.

Example:

~~~text
Logical:
customers + orders → customer_mart

Physical:
Snowflake table A + Snowflake table B
    → query Q-88
    → table C
~~~

PyTransformKit owns logical lineage.

Engine adapters MAY add physical lineage evidence.

---

# 43. Plan lineage versus execution lineage

TransformationPlan lineage describes intended derivation.

TransformationExecution lineage describes what actually executed.

The two may differ in physical details due to:

- optimization;
- pushdown;
- engine selection;
- cache reuse;
- pruning.

The logical semantic lineage MUST remain equivalent.

---

# 44. Optimization lineage

Optimizer rewrites MUST preserve semantic lineage.

For example:

~~~text
Filter pushed before Join
~~~

may change physical execution order.

It MUST NOT change declared logical derivation semantics.

Optimizer diagnostics MAY explain rewrite lineage separately.

---

# 45. Cache lineage

If a cached output is reused:

~~~text
TransformationExecution T-100
    ↓ cache hit
Artifact A-55
~~~

The current execution SHOULD still record:

- intended plan fingerprint;
- input references;
- cache reference;
- source execution/reference that produced cache if known.

Cache reuse does not erase transformation lineage.

---

# 46. Workflow execution lineage

PyWorkflowKit SHOULD record:

~~~text
WorkflowRun
    contains TaskRuns

TaskRun
    has TaskAttempts

TaskAttempt
    invokes ExternalRunRefs

Task dependency edges
    define readiness/execution order
~~~

This is operational lineage.

---

# 47. Workflow dependency lineage

A workflow dependency such as:

~~~text
ingest_customers
      ↓
build_customer_mart
~~~

means operational ordering/dependency.

It does not automatically mean data flowed from the first task to the second.

Data lineage requires an explicit output/input reference link.

---

# 48. Workflow data handoff lineage

If Task A outputs DatasetVersionReference V-52 and Task B consumes it, WorkflowKit MAY record:

~~~text
TaskRun A
    PRODUCED_REFERENCE
DatasetVersion V-52

TaskRun B
    CONSUMED_REFERENCE
DatasetVersion V-52
~~~

The data object remains PyIngestKit-owned.

WorkflowKit records the handoff evidence.

---

# 49. TaskAttempt and ExternalRunRef

A TaskAttempt invoking PyTransformKit may record:

~~~text
TaskAttempt TA-12.2
    EXECUTED_BY
TransformationExecutionReference T-913
~~~

This connects workflow execution lineage with transformation execution.

It does not make WorkflowKit the owner of T-913.

---

# 50. Retry lineage

Retries SHOULD remain traceable.

~~~text
TaskRun TR-12
├── TaskAttempt TA-12.1 FAILED
└── TaskAttempt TA-12.2 SUCCEEDED
~~~

Recommended relationship:

~~~text
TA-12.2 RETRIED_AS successor of TA-12.1
~~~

or equivalent attempt ordering evidence.

Historical failed attempts MUST NOT disappear after success.

---

# 51. Recovery lineage

Recovery SHOULD preserve:

~~~text
existing WorkflowRunId
existing TaskRunId
existing external execution references where applicable
~~~

Recovery events MAY indicate:

~~~text
RECOVERED
REATTACHED_TO
RECONCILED
RESUMED
~~~

but do not create false new lineage identities.

---

# 52. Reconciliation lineage

When uncertain execution is reconciled:

~~~text
TransformationExecution T-913
    UNKNOWN_OUTCOME
      ↓
Reconciliation R-7
      ↓
CONFIRMED_SUCCEEDED
~~~

Traceability SHOULD retain the reconciliation evidence and final status transition.

The reconciliation operation does not replace T-913.

---

# 53. Correlation and lineage

CorrelationId helps locate related executions.

It is not a lineage edge by itself.

Two objects sharing CorrelationId are not necessarily in a direct provenance or derivation relationship.

Canonical rule:

~~~text
correlation
    groups

lineage edge
    explains relationship
~~~

---

# 54. Causation and lineage

CausationId MAY support execution lineage.

Example:

~~~text
TaskAttempt TA-3
    causes
TransformationExecution T-913
~~~

However, data lineage still requires explicit data references.

Causation does not prove data consumption.

---

# 55. Artifact lineage

Artifacts SHOULD support producer/consumer links.

Examples:

~~~text
IngestionRun I-288
    PRODUCED
RAW Artifact A-10

TransformationExecution T-913
    PRODUCED
Artifact A-20

DatasetVersion customers@52
    DESCRIBED_BY
Manifest Artifact M-52
~~~

The exact edge names are domain-owned.

---

# 56. DatasetVersion and transformation linkage

When a DatasetVersion feeds a transformation:

~~~text
DatasetVersion customers@52
    CONSUMED_BY
TransformationExecution T-913
~~~

When transformed output is published:

~~~text
TransformationExecution T-913
    PRODUCED
ResourceReference R-90
        ↓
PyIngestKit publication
        ↓
DatasetVersion customer_mart@8
~~~

This provides end-to-end traceability without merging domains.

---

# 57. Canonical end-to-end trace

~~~text
WorkflowRun W-42
│
├── TaskRun ingest_customers
│   └── TaskAttempt TA-1
│       └── IngestionRun I-288
│           ├── ACQUIRED_FROM Source S-customers
│           ├── PRESERVED_AS RAW A-10
│           └── VERSIONED_AS customers@52
│
├── TaskRun ingest_orders
│   └── TaskAttempt TA-2
│       └── IngestionRun I-289
│           └── VERSIONED_AS orders@117
│
├── TaskRun build_customer_mart
│   └── TaskAttempt TA-3
│       └── TransformationExecution T-913
│           ├── CONSUMED customers@52
│           ├── CONSUMED orders@117
│           ├── plan_fingerprint = P-55
│           └── PRODUCED Resource R-90
│
└── TaskRun publish_customer_mart
    └── TaskAttempt TA-4
        └── IngestionRun I-290
            ├── consumed Resource R-90
            └── PUBLISHED_AS customer_mart@8
~~~

This is one composed traceability view built from multiple owned lineage models.

---

# 58. Lineage timestamps

Lineage/provenance records MAY include timestamps.

Examples:

~~~text
observed_at
produced_at
acquired_at
published_at
recorded_at
~~~

Timestamps are supporting evidence.

They MUST NOT be used to infer lineage relationships when explicit references are available.

---

# 59. Lineage identity

A durable lineage record MAY have its own identifier.

Examples:

~~~text
LineageEventId
ProvenanceRecordId
~~~

Such IDs identify the evidence record, not the underlying DatasetVersion or execution.

---

# 60. Event-based lineage capture

Lineage MAY be captured from runtime events.

Example:

~~~text
DatasetVersionCreated
TransformationInputBound
TransformationOutputProduced
TaskAttemptStarted
PublicationCompleted
~~~

Event-driven capture is an implementation strategy.

The canonical lineage semantics remain domain-defined.

---

# 61. Snapshot lineage

Systems MAY periodically persist lineage snapshots or graph projections for querying.

A snapshot is derived data.

The authoritative evidence remains the domain-owned source records/events/references.

---

# 62. Lineage persistence

Each framework may persist lineage differently.

~~~text
PyIngestKit
    metadata database + artifact manifests

PyTransformKit
    execution manifest + portable lineage IR

PyWorkflowKit
    workflow metadata store + events
~~~

The ecosystem does not mandate one shared lineage database.

---

# 63. External lineage backend

A deployment MAY export lineage to systems such as:

~~~text
OpenLineage-compatible backend
data catalog
metadata graph
observability platform
custom lineage store
~~~

Export adapters are projections.

External backends do not become the semantic owner of native PyKit lineage.

---

# 64. OpenLineage interoperability

If OpenLineage interoperability is implemented, mapping SHOULD preserve PyKit distinctions where possible.

For example:

~~~text
WorkflowRun / TaskAttempt
    operational job/run mapping

DatasetVersionReference
    dataset/version facet

Transformation field lineage
    column-lineage facet
~~~

Mapping loss or unsupported semantics should be documented.

The PyKit domain model MUST NOT be distorted solely to fit an external standard.

---

# 65. Data catalog integration

Catalogs MAY consume:

- DatasetReference;
- DatasetVersionReference;
- schema;
- ownership metadata;
- field lineage;
- publication provenance.

Catalog integration remains optional.

PyWorkflowKit core must not depend on a catalog.

---

# 66. Lineage confidence

Lineage statements SHOULD declare confidence when not exact.

Possible values:

~~~text
EXACT
DECLARED
INFERRED
PARTIAL
UNKNOWN
~~~

Static AST-derived lineage may be EXACT.

Plugin-declared lineage may be DECLARED.

SQL-parser-derived lineage may be INFERRED/PARTIAL depending on support.

Fabricated certainty is prohibited.

---

# 67. Unknown lineage

Unknown lineage is a valid result.

Example:

~~~text
output.field_x
    lineage = UNKNOWN
~~~

The framework should preserve the transformation/execution reference so later analysis may enrich it.

Unknown is preferable to incorrect lineage.

---

# 68. Lineage completeness

A lineage record MAY declare completeness scope.

Examples:

~~~text
DATASET_LEVEL_COMPLETE
FIELD_LEVEL_PARTIAL
PHYSICAL_LINEAGE_UNKNOWN
EXECUTION_LINEAGE_COMPLETE
~~~

Consumers should not assume full lineage merely because some edges exist.

---

# 69. Lineage versioning

Persisted lineage contracts require explicit schema versions.

Lineage contract version is independent from:

- package version;
- DatasetVersion;
- WorkflowDefinition version;
- TransformationPlan version.

---

# 70. Lineage immutability

Historical provenance should be append-only where practical.

Corrections SHOULD be represented through:

- superseding records;
- reconciliation records;
- amendment events;
- explicit administrative updates with audit.

Silent rewriting of historical lineage is discouraged.

---

# 71. Lineage and deleted resources

A deleted/tombstoned resource may remain present in historical lineage.

Example:

~~~text
DatasetVersion customers@52
    consumed Resource R-10
    R-10 later expired
~~~

Traceability remains meaningful even when materialization is no longer possible.

---

# 72. Lineage and sensitive data

Lineage SHOULD avoid embedding raw data values.

Field names, dataset names and URIs may themselves be sensitive.

Redaction/security policies must apply to:

- locators;
- query text;
- raw expressions;
- metadata;
- labels.

Lineage is metadata, but metadata can still be sensitive.

---

# 73. SQL and expression privacy

Full SQL text or expression source SHOULD NOT be persisted automatically if it may expose sensitive literals.

Prefer:

~~~text
fingerprint
normalized representation
redacted expression
structured AST without sensitive values
~~~

when sufficient.

---

# 74. User-defined metadata

Custom lineage metadata MAY be attached through namespaced extension fields.

It MUST NOT redefine required lineage semantics.

Example:

~~~text
company.cost_center
company.data_owner
~~~

is acceptable supplementary metadata.

---

# 75. Lineage graph traversal

Consumers MAY offer queries such as:

~~~text
upstream(dataset_version)
downstream(dataset_version)
field_upstream(field)
workflow_for(dataset_version)
executions_for(plan_fingerprint)
artifacts_for(ingestion_run)
~~~

Traversal APIs are derived services.

They should respect domain ownership and access controls.

---

# 76. Impact analysis

PyTransformKit lineage may support impact analysis.

Example:

~~~text
change customers.country
    ↓
affected fields
    ↓
affected transformations
    ↓
affected output datasets
~~~

When composed with workflow and publication lineage, impact analysis may continue to:

~~~text
affected tasks
affected published datasets
~~~

Cross-framework impact analysis remains a projection over native lineage.

---

# 77. Upstream analysis

Upstream traversal can answer:

~~~text
Which source and RAW artifact ultimately contributed to customer_mart@8?
~~~

Canonical path:

~~~text
customer_mart@8
    ← publication
TransformationExecution T-913
    ← customers@52
    ← RAW A-10
    ← Source S-customers
~~~

---

# 78. Downstream analysis

Downstream traversal can answer:

~~~text
Which published datasets depend on Source S-customers?
~~~

This may traverse ingestion and transformation edges.

The traversal engine must preserve edge types so users can distinguish data derivation from workflow ordering.

---

# 79. Execution-to-data traceability

The ecosystem SHOULD support both directions:

~~~text
execution → data
data → execution
~~~

Examples:

~~~text
TransformationExecution T-913
    → inputs
    → outputs

DatasetVersion customer_mart@8
    → publication run
    → transformation execution
    → source versions
~~~

---

# 80. Workflow-to-data traceability

WorkflowKit SHOULD expose enough references to answer:

~~~text
Which DatasetVersions were produced during WorkflowRun W-42?
~~~

without owning DatasetVersion semantics.

This is achieved by task output references and ExternalRunRef links.

---

# 81. Data-to-workflow traceability

The inverse query should also be possible when evidence was retained:

~~~text
Which WorkflowRun caused customer_mart@8 to be published?
~~~

The answer is obtained by following:

~~~text
DatasetVersion provenance
    → IngestionRun
    → Correlation / upstream TaskAttempt
    → WorkflowRun
~~~

---

# 82. Multiple workflows

The same DatasetVersion may be observed/consumed by multiple workflows.

Consumption lineage and creation provenance must remain distinct.

A consumer workflow does not become the producer of the DatasetVersion.

---

# 83. Multiple producers

A single governed dataset logical identity may have versions produced by different workflows or manual processes.

Each DatasetVersion retains its own production provenance.

Do not attach lineage only at the mutable PublishedDataset pointer level.

---

# 84. Manual/external production

Not all data originates from PyKit runtimes.

External/manual lineage MAY be represented through:

~~~text
ExternalRunRef
external producer reference
external source reference
declared provenance
~~~

Confidence should indicate DECLARED or external provenance where exact native evidence is unavailable.

---

# 85. Importing lineage

External lineage imports MUST NOT silently become native authoritative PyKit lineage.

Imported evidence should retain:

~~~text
source_system
import_timestamp
confidence
external_reference
~~~

---

# 86. Lineage merge rules

When multiple evidence sources describe the same relation:

- exact native evidence should not be overwritten by weaker inferred evidence;
- duplicate equivalent edges may be deduplicated;
- contradictory evidence should remain visible or trigger validation;
- provenance of the lineage statement itself should be retained where needed.

---

# 87. Contradictory lineage

If one source says:

~~~text
field A derived from X
~~~

and another says:

~~~text
field A derived from Y
~~~

the system MUST NOT silently pick one without policy.

It may:

- preserve both with confidence/source;
- mark conflict;
- prefer authoritative owner;
- require reconciliation.

---

# 88. Lineage authority

Canonical authority is:

~~~text
PyIngestKit
    source/artifact/version provenance

PyTransformKit
    logical transformation/field lineage

PyWorkflowKit
    operational execution lineage
~~~

When a cross-framework projection conflicts with the native owner, the owner's record is authoritative for that semantic domain.

---

# 89. Lineage events and correlation

Every lineage-producing event SHOULD carry CorrelationId and native execution reference where available.

This allows lineage records from different stores to be joined without identity conflation.

---

# 90. Failure lineage

Failed executions may still produce useful lineage.

Examples:

~~~text
RAW acquired before decode failure
partial transformation output artifact
external run reference before timeout
~~~

Lineage MUST distinguish produced-and-committed effects from merely attempted effects.

---

# 91. Partial output lineage

If an execution produces partial outputs, lineage should label their state.

Possible states:

~~~text
COMMITTED
PARTIAL
UNCONFIRMED
ROLLED_BACK
DISCARDED
~~~

Do not expose an unconfirmed output as a successful lineage edge without uncertainty metadata.

---

# 92. Uncertainty and lineage

UNKNOWN_OUTCOME affects traceability.

Example:

~~~text
TransformationExecution T-913
    may have produced Resource R-90
~~~

The lineage relation should be marked uncertain until reconciliation.

After confirmation, a reconciliation event may promote the relationship to confirmed.

---

# 93. Cancellation lineage

A cancelled execution may have consumed inputs but not produced committed outputs.

The lineage model SHOULD be able to preserve:

~~~text
input consumed/attempted
execution cancelled
no confirmed output
~~~

This distinction matters for audit.

---

# 94. Retry lineage and duplicate effects

If a retry follows an uncertain attempt, lineage must preserve both attempts/executions until reconciliation proves whether duplicate side effects occurred.

Never collapse retries simply because the final task succeeded.

---

# 95. Lineage capture timing

Lineage may be captured at:

~~~text
PLAN TIME
EXECUTION START
RUNTIME
EXECUTION END
RECONCILIATION
PUBLICATION
~~~

Static logical lineage may exist before execution.

Physical/provenance evidence often becomes known only at runtime.

The model should allow incremental enrichment.

---

# 96. Static lineage

Static lineage can be derived from immutable definitions/plans.

Advantages:

- available before execution;
- useful for impact analysis;
- deterministic;
- independent of runtime provider.

Limitations:

- may not know dynamic fields;
- may not know actual physical resources;
- may not know runtime branch decisions.

---

# 97. Runtime lineage

Runtime lineage records actual bindings and outputs.

Examples:

~~~text
DatasetVersion customers@52 actually bound
engine = polars
output Resource R-90 actually written
~~~

Runtime lineage complements static lineage.

---

# 98. Planned versus actual inputs

A TransformationPlan may declare logical input customers.

At runtime that input may resolve to:

~~~text
DatasetVersion customers@52
~~~

Lineage SHOULD distinguish:

~~~text
planned logical input
actual resolved input
~~~

This is essential for reproducibility.

---

# 99. Planned versus actual workflow execution

A WorkflowDefinition describes possible tasks/dependencies.

A WorkflowRun records which tasks/attempts actually ran.

Branches/skips mean runtime execution lineage may be a subset of the definition graph.

---

# 100. Skipped tasks

Skipped TaskRun values remain part of execution traceability.

They SHOULD record why they were skipped.

Examples:

~~~text
upstream failure
condition false
cancelled workflow
cached result
manual skip
~~~

A skipped task should not be represented as if it executed.

---

# 101. Cached task lineage

If WorkflowKit later supports task-level cache/reuse, the task should record:

~~~text
cache hit
source result/reference
original execution reference?
~~~

Reuse lineage must distinguish execution avoidance from fresh execution.

---

# 102. Lineage API shape

Framework-specific APIs MAY expose operations such as:

~~~text
get_lineage()
get_provenance()
upstream()
downstream()
explain_lineage()
export_lineage()
~~~

The exact APIs belong to framework-specific specifications.

The ecosystem does not require one shared Python LineageService.

---

# 103. Portable lineage DTO

A future portable projection MAY use:

~~~text
LineageRecord
    subject_reference
    relationship
    object_reference
    producer
    confidence
    execution_reference?
    correlation_id?
    metadata?
    contract_version
~~~

This is a boundary DTO.

It is not a replacement for native lineage models.

---

# 104. Relationship direction

Lineage relationship direction MUST be documented.

Example:

~~~text
output DERIVED_FROM input
~~~

not ambiguously:

~~~text
input DERIVED_FROM output
~~~

Directional consistency is required for traversal.

---

# 105. Canonical edge examples

Recommended direction:

~~~text
RAW PRESERVED_FROM Source

DatasetVersion VERSIONED_FROM RAW

OutputDataset DERIVED_FROM InputDataset

OutputField DERIVED_FROM InputField

TaskAttempt ATTEMPT_OF TaskRun

TransformationExecution EXECUTED_BY TaskAttempt

DatasetVersion PUBLISHED_FROM ResourceReference
~~~

Exact names may be refined, but direction must remain explicit.

---

# 106. Lineage identifiers are references

Nodes in portable lineage SHOULD use stable references rather than arbitrary labels.

Good:

~~~text
DatasetVersionReference(dataset_id="customers", version_id="52")
~~~

Weak:

~~~text
"customers"
~~~

unless the label itself is a canonical stable identifier in that context.

---

# 107. Schema evolution lineage

When schema changes across DatasetVersions:

~~~text
customers@52 schema S1
customers@53 schema S2
~~~

provenance SHOULD preserve each schema reference/fingerprint.

Transformation lineage may then explain which downstream outputs depend on changed fields.

---

# 108. Version-to-version derivation

If one DatasetVersion is created from another without external reacquisition, provenance MAY include:

~~~text
customer_mart@8
    DERIVED_FROM
customers@52
orders@117
~~~

The detailed transformation remains PyTransformKit-owned.

PyIngestKit may retain high-level input version references.

---

# 109. Source-to-field traceability

End-to-end field traceability may combine multiple layers.

Example:

~~~text
Source CSV column customer_id
    ↓ decode
DatasetVersion customers@52.customer_id
    ↓ transformation
customer_mart@8.customer_key
~~~

PyIngestKit owns source mapping.

PyTransformKit owns logical derivation.

The composed view connects them.

---

# 110. Quality lineage

Quality rules MAY produce evidence linked to:

~~~text
input DatasetVersion
TransformationExecution
output Dataset
publication decision
~~~

A quality failure may explain why publication did not occur.

Quality evidence remains distinct from transformation field lineage.

---

# 111. Governance lineage

Governance metadata may include:

~~~text
publisher
approval reference
classification
retention policy
publication namespace
~~~

These fields belong to governance/publication semantics, not the core PyTransformKit lineage model.

---

# 112. Actor traceability

Where an actor/principal triggers or approves operations, audit records MAY link:

~~~text
principal
    ↓ triggered
WorkflowRun / IngestionRun / Publication
~~~

Actor identity belongs to security/audit semantics.

It is not data lineage.

---

# 113. Lineage retention

Lineage retention SHOULD normally outlive short-lived runtime logs when audit/reproducibility requires it.

Retention requirements may differ across:

~~~text
RAW provenance
DatasetVersion lineage
Transformation execution lineage
Workflow attempt history
telemetry traces
~~~

Do not assume one retention policy fits all.

---

# 114. Deletion requests and lineage

If payload data must be deleted while lineage metadata is retained, references may become tombstoned/redacted.

The system SHOULD preserve only metadata legally/operationally permitted by policy.

This document does not override privacy/security retention rules.

---

# 115. Lineage portability

Portable lineage records SHOULD remain interpretable without importing concrete provider libraries.

Engine-specific physical metadata may be namespaced extensions.

Core semantic relationships remain provider-neutral.

---

# 116. Lineage serialization

Persisted lineage MUST use explicit versioned schemas.

Avoid:

~~~text
pickle of native graph object
~~~

Prefer schema-driven records or manifests.

Exact wire contracts belong to the serialization specification.

---

# 117. Lineage conformance testing

Each framework SHOULD test its owned lineage.

PyIngestKit tests:

~~~text
Source → RAW → DatasetVersion provenance
replay provenance
publication provenance
~~~

PyTransformKit tests:

~~~text
dataset lineage
field lineage
join/aggregate/window semantics
optimizer lineage preservation
~~~

PyWorkflowKit tests:

~~~text
WorkflowRun → TaskRun → TaskAttempt
retry history
ExternalRunRef links
skipped/cancelled behavior
~~~

---

# 118. Cross-framework lineage tests

Required end-to-end scenarios SHOULD verify:

~~~text
Source
  → RAW
  → DatasetVersion
  → TransformationExecution
  → output Resource
  → new DatasetVersion

plus

WorkflowRun
  → TaskAttempt
  → each external execution
~~~

The test should prove that all links can be traversed without importing sibling private objects.

---

# 119. Lineage correctness over completeness

When forced to choose:

> **Correct partial lineage is preferable to complete-looking incorrect lineage.**

The system MUST NOT invent field dependencies merely to render a complete graph.

---

# 120. Acceptance criteria

This specification is implemented correctly when:

1. ingestion provenance, transformation lineage and workflow execution lineage remain separate owned models;
2. Source, RAW, Artifact and DatasetVersion provenance is traceable in PyIngestKit;
3. PyTransformKit records dataset-level derivation;
4. PyTransformKit can represent field-level lineage where semantically knowable;
5. workflow retries preserve TaskAttempt history;
6. ExternalRunRef connects TaskAttempt to sibling/provider execution;
7. CorrelationId assists discovery but is not treated as a lineage edge;
8. data handoff uses portable references;
9. publication lineage links transformed output to new DatasetVersion;
10. replay preserves historical source evidence and creates new execution lineage;
11. recovery does not fabricate new execution identities;
12. planned and actual inputs can be distinguished;
13. logical and physical lineage remain distinguishable;
14. uncertain outputs can be represented as uncertain lineage;
15. lineage confidence can be expressed when exact derivation is unavailable;
16. native owner evidence remains authoritative over derived projections;
17. lineage persistence does not require one shared database;
18. external catalog/OpenLineage export remains optional;
19. sensitive values are not embedded indiscriminately in lineage;
20. end-to-end traversal can reconstruct source-to-publication and workflow-to-data traceability.

---

# 121. Normative invariants

### LIN-INV-01 — Each bounded context owns its lineage semantics

Ingestion, transformation and workflow lineage are not one universal model.

### LIN-INV-02 — Traceability composes references

Cross-framework traceability uses stable references and correlation.

### LIN-INV-03 — Correlation is not lineage

Shared CorrelationId does not prove derivation or causation.

### LIN-INV-04 — Logical lineage is distinct from physical lineage

Semantic derivation and engine execution evidence remain distinguishable.

### LIN-INV-05 — Planned lineage is distinct from actual runtime binding

Definitions/plans do not prove which concrete data version executed.

### LIN-INV-06 — Field lineage must not fabricate certainty

Unknown or partial lineage is explicit.

### LIN-INV-07 — Replay creates new execution provenance

Historical inputs remain linked without identity reuse.

### LIN-INV-08 — Retry history is preserved

Successful retry does not erase failed attempts.

### LIN-INV-09 — Publication closes the governance lineage loop

Transformation output becomes governed DatasetVersion only through explicit PyIngestKit publication.

### LIN-INV-10 — Native owner evidence is authoritative

Cross-framework projections do not override source-domain truth.

### LIN-INV-11 — Historical lineage is append-oriented

Corrections and reconciliation are explicit.

### LIN-INV-12 — Data values are not lineage metadata by default

Lineage remains metadata-first and sensitivity-aware.

---

# 122. Canonical end-to-end model

~~~text
                          WorkflowRun W-42
                                 │
                  ┌──────────────┼──────────────┐
                  │              │              │
                  ▼              ▼              ▼
             TaskAttempt    TaskAttempt    TaskAttempt
                  │              │              │
                  ▼              ▼              ▼
           IngestionRun    IngestionRun   TransformationExecution
                  │              │              │
                  ▼              ▼              │
              RAW A-10        RAW A-11          │
                  │              │              │
                  ▼              ▼              │
           customers@52     orders@117          │
                  └──────────────┬───────────────┘
                                 ▼
                        Transformation lineage
                                 │
                                 ▼
                          output Resource R-90
                                 │
                                 ▼
                           Ingestion publication
                                 │
                                 ▼
                        customer_mart@8
~~~

Three lineage domains remain visible:

~~~text
PyIngestKit
    source → RAW → DatasetVersion → publication

PyTransformKit
    input datasets/fields → transformations → output

PyWorkflowKit
    WorkflowRun → TaskRun → TaskAttempt → external execution
~~~

The composed trace is end-to-end without erasing ownership.

---

# 123. Final architecture statement

The PyKit V2 ecosystem does not need one universal lineage engine to achieve end-to-end traceability.

It needs:

~~~text
clear semantic ownership
stable references
explicit lineage relationships
execution identity
correlation
portable evidence
~~~

The central rule is:

> **Preserve lineage where meaning is known, preserve provenance where origin matters, and compose traceability without flattening bounded contexts.**

This specification is the baseline for:

~~~text
PYKIT_ECOSYSTEM_V2_OBSERVABILITY_EVENTS_AND_TELEMETRY_MODEL.md
PYKIT_ECOSYSTEM_V2_INTEGRATION_AND_ANTI_CORRUPTION_LAYER_MODEL.md
PYKIT_ECOSYSTEM_V2_SERIALIZATION_AND_WIRE_CONTRACTS.md
PYKIT_ECOSYSTEM_V2_ARCHITECTURE_CONFORMANCE_AND_TEST_STRATEGY.md
~~~
