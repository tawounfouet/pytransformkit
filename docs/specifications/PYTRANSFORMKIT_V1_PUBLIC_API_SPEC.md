# PyTransformKit V1 — Public API Specification

> **Status:** NORMATIVE PUBLIC API BASELINE  
> **Target release:** PyTransformKit 1.0.0  
> **Date:** 2026-09-29  
> **Architecture generation:** PyKit Ecosystem V2  
> **Depends on:** PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_DECLARATION_PLAN_RUNTIME_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_RELEASE_COMPATIBILITY_AND_VERSIONING_POLICY.md

---

# 1. Purpose

This document freezes the target public Python API of PyTransformKit 1.0.

It defines stable vocabulary, import paths, construction patterns, authoring flow, compilation, runtime execution, engine registration, bindings, results, diagnostics, exceptions, serialization boundaries, extension protocols and compatibility rules.

> **The public API makes transformation intent portable, compilation inspectable, engine choice explicit and runtime state separate from the logical model.**

---

# 2. Canonical lifecycle

~~~text
declare Dataset / Schema / Expression
        ↓
build TransformationPlan
        ↓
compile to LogicalPlan when inspection is needed
        ↓
bind physical inputs and outputs
        ↓
TransformationRuntime.execute(...)
        ↓
TransformationResult
~~~

Compilation is optional in the common path because TransformationRuntime may compile a TransformationPlan internally.

---

# 3. Canonical root imports

PyTransformKit 1.0 SHOULD support:

~~~python
from pytransformkit import (
    DataType,
    Dataset,
    Expression,
    Field,
    InputBinding,
    LogicalPlan,
    OutputBinding,
    ResourceReference,
    Schema,
    TransformationExecutionId,
    TransformationPlan,
    TransformationResult,
    TransformationRuntime,
    col,
    lit,
)
~~~

The root API remains curated rather than exhaustive.

---

# 4. Stable root surface

The following categories are target STABLE surfaces for 1.0:

~~~text
DataType / Field / Schema / Dataset
Expression / col / lit
TransformationPlan
LogicalPlan
TransformationRuntime
TransformationExecutionId
TransformationResult
InputBinding
OutputBinding
ResourceReference
selected transformation primitives
selected public exceptions
~~~

Internal graph types, optimizer implementation classes, native engine helpers and private serializers are not root exports.

---

# 5. Public qualified namespaces

Intended public namespaces include:

~~~text
pytransformkit.authoring
pytransformkit.expressions
pytransformkit.functions
pytransformkit.transformations
pytransformkit.planning
pytransformkit.runtime
pytransformkit.engines
pytransformkit.lineage
pytransformkit.serialization
pytransformkit.diagnostics
pytransformkit.plugins
pytransformkit.adapters.pandas
pytransformkit.adapters.polars
~~~

PyArrow and DuckDB adapter namespaces MAY remain PROVISIONAL at 1.0 if their conformance surface is not ready to freeze.

---

# 6. Import-time safety

Importing pytransformkit MUST NOT:

- load every optional engine;
- contact external systems;
- resolve credentials;
- activate plugins;
- mutate mandatory global registries;
- open files;
- emit network telemetry;
- execute transformations.

The package root must import successfully with core-only dependencies.

---

# 7. Constructor safety

Public domain constructors are side-effect free.

Constructing Dataset, Schema, Expression, TransformationPlan, InputBinding declarations, OutputBinding declarations or policies MUST NOT perform physical I/O.

Resource resolution occurs only during explicit runtime operations.

---

# 8. DataType

DataType is the canonical logical type value.

Recommended constructors include:

~~~python
DataType.boolean()
DataType.int8()
DataType.int16()
DataType.int32()
DataType.int64()
DataType.uint8()
DataType.uint16()
DataType.uint32()
DataType.uint64()
DataType.float32()
DataType.float64()
DataType.decimal(precision=18, scale=2)
DataType.string()
DataType.binary()
DataType.date()
DataType.time()
DataType.timestamp(timezone="UTC")
DataType.duration(unit="ms")
DataType.list_of(DataType.string())
DataType.struct(fields=(...))
DataType.map_of(
    key=DataType.string(),
    value=DataType.string(),
)
DataType.null()
DataType.unknown()
~~~

DataType values are immutable, comparable and hashable.

Native engine dtype objects are not canonical DataType values.

---

# 9. Field

Canonical construction:

~~~python
Field(
    "customer_id",
    DataType.string(),
    nullable=False,
)
~~~

Stable properties SHOULD include:

~~~text
name
dtype
nullable
metadata
~~~

Field values are immutable.

---

# 10. Schema

Canonical construction:

~~~python
customer_schema = Schema(
    fields=(
        Field("customer_id", DataType.string(), nullable=False),
        Field("email", DataType.string()),
        Field("country", DataType.string()),
    )
)
~~~

Stable inspection SHOULD include:

~~~python
schema.field("customer_id")
schema.has_field("country")
schema.names
schema.fields
schema.fingerprint()
~~~

Field order is explicit and deterministic.

---

# 11. Dataset

Dataset is a logical declaration, never native data.

Canonical construction:

~~~python
customers = Dataset(
    name="customers",
    schema=customer_schema,
)
~~~

Stable properties SHOULD include:

~~~text
name
schema
metadata
~~~

Dataset MUST NOT expose a DataFrame, LazyFrame, Arrow Table or DuckDB relation as logical state.

---

# 12. Expression

Expression is the immutable logical AST.

Canonical authoring:

~~~python
amount = col("amount")
predicate = (
    (amount > lit(100))
    & (col("status") == lit("PAID"))
)
~~~

Operator overloading builds AST nodes and never executes data.

Python truth-value coercion of Expression SHOULD fail clearly.

---

# 13. Core expression semantics

Stable expression families SHOULD cover:

~~~text
comparison
boolean logic
arithmetic
null tests
cast
alias
conditional expressions
string/date helpers
aggregate expressions
window expressions
nested access where supported
~~~

Portable semantics are defined by PyTransformKit rather than native engine naming.

---

# 14. Functions namespace

Portable functions SHOULD use a qualified namespace:

~~~python
from pytransformkit import functions as fn

fn.lower(col("email"))
fn.sum(col("amount"))
fn.count(col("order_id"))
fn.min(col("ordered_at"))
fn.max(col("ordered_at"))
~~~

A function is stable only when semantics are covered by the cross-engine conformance suite.

---

# 15. Window namespace

Window functionality SHOULD use a dedicated namespace:

~~~python
from pytransformkit import window

spec = (
    window.partition_by("customer_id")
    .order_by("ordered_at")
)

rank = window.row_number().over(spec)
~~~

Window support remains engine-capability checked.

---

# 16. TransformationPlan

TransformationPlan is the canonical authoring root.

The preferred ergonomic path is:

~~~python
builder = TransformationPlan.builder(
    name="customer_mart"
)
~~~

The builder is an authoring helper, not a separate semantic architecture layer.

---

# 17. TransformationPlanBuilder

TransformationPlanBuilder MAY be public under pytransformkit.authoring while remaining absent from root exports.

build() returns an immutable canonical TransformationPlan.

Mutable builder internals are acceptable for ergonomics; the resulting plan is immutable.

---

# 18. Declaring inputs

Canonical plan inputs:

~~~python
builder = TransformationPlan.builder(
    "customer_mart"
)

customers = builder.input(
    "customers",
    schema=customer_schema,
)

orders = builder.input(
    "orders",
    schema=order_schema,
)
~~~

builder.input returns a logical Dataset representing one plan input.

---

# 19. Filter

~~~python
paid_orders = builder.filter(
    name="paid_orders",
    source=orders,
    where=(
        col("status")
        == lit("PAID")
    ),
)
~~~

The return value is the logical Dataset produced by the transformation.

---

# 20. Projection

~~~python
customers_core = builder.select(
    name="customers_core",
    source=customers,
    columns=(
        col("customer_id"),
        col("email"),
        col("country"),
        col("status").alias(
            "customer_status"
        ),
    ),
)
~~~

Projection order determines output field order.

---

# 21. Derivation

~~~python
enriched = builder.derive(
    name="enriched",
    source=customers_core,
    columns={
        "is_france": (
            col("country")
            == lit("FR")
        ),
    },
)
~~~

Derived expressions remain declarative.

---

# 22. Cast

Casting SHOULD normally use Expression.cast:

~~~python
casted = builder.derive(
    name="casted",
    source=orders,
    columns={
        "amount": (
            col("amount")
            .cast(
                DataType.decimal(
                    18,
                    2,
                )
            )
        ),
    },
)
~~~

A dedicated builder.cast helper MAY exist if it adds diagnostics without changing semantics.

---

# 23. Sort

~~~python
ordered = builder.sort(
    name="ordered",
    source=orders,
    by=(
        col("customer_id").asc(),
        col("ordered_at").desc(),
    ),
)
~~~

Null ordering and sort stability must be explicit where engine behavior differs.

---

# 24. Deduplication

~~~python
unique_orders = builder.deduplicate(
    name="unique_orders",
    source=orders,
    keys=("order_id",),
    keep="first",
)
~~~

When source order is not guaranteed, deterministic first/last semantics require explicit ordering.

---

# 25. Join

~~~python
joined = builder.join(
    name="customer_orders",
    left=customers_core,
    right=order_stats,
    how="left",
    on=(
        (
            "customer_id",
            "customer_id",
        ),
    ),
)
~~~

V1 stable join modes SHOULD include at least inner and left.

Additional modes become stable only after cross-engine semantic qualification.

---

# 26. Aggregation

~~~python
order_stats = builder.aggregate(
    name="order_stats",
    source=paid_orders,
    group_by=(
        col("customer_id"),
    ),
    metrics={
        "paid_order_count": (
            fn.count(
                col("order_id")
            )
        ),
        "paid_revenue": (
            fn.sum(
                col("amount")
            )
        ),
        "first_order_at": (
            fn.min(
                col("ordered_at")
            )
        ),
        "last_order_at": (
            fn.max(
                col("ordered_at")
            )
        ),
    },
)
~~~

Aggregate validity is checked during compilation.

---

# 27. Window derivation

~~~python
ranked = builder.derive(
    name="ranked",
    source=orders,
    columns={
        "order_rank": (
            window.row_number()
            .over(
                window
                .partition_by(
                    "customer_id"
                )
                .order_by(
                    "ordered_at"
                )
            )
        ),
    },
)
~~~

Unsupported window semantics fail explicitly through capability validation.

---

# 28. Outputs and build

~~~python
builder.output(
    "customer_mart",
    customer_mart,
)

plan = builder.build()
~~~

A plan MAY expose multiple named outputs.

Output names are stable within the plan.

---

# 29. TransformationPlan inspection

Stable properties SHOULD include:

~~~text
name
inputs
outputs
transformations
metadata
~~~

Stable methods SHOULD include:

~~~python
plan.validate()
plan.fingerprint()
plan.explain()
~~~

validate performs structural and semantic validation without physical execution.

---

# 30. Plan immutability

TransformationPlan is immutable after build.

Changing logical semantics produces a new plan value and potentially a new fingerprint.

Runtime execution never mutates the plan.

---

# 31. No plan-owned execution as primary model

The canonical execution style is:

~~~python
result = runtime.execute(
    plan,
    ...
)
~~~

TransformationPlan.run or TransformationPlan.execute MUST NOT be the only or primary execution model.

---

# 32. Compilation API

Public compilation lives in planning:

~~~python
from pytransformkit.planning import (
    TransformationCompiler,
)

compiler = TransformationCompiler()

logical_plan = compiler.compile(
    plan
)
~~~

Compilation is deterministic for the same semantic plan and compiler configuration.

Compilation does not read physical input data.

---

# 33. LogicalPlan

LogicalPlan is the public engine-neutral compiled representation.

Stable inspection SHOULD expose:

~~~text
name
inputs
outputs
nodes
required_capabilities
diagnostics
lineage
fingerprint
~~~

Node views may be read-only public logical views rather than private implementation classes.

---

# 34. LogicalPlan inspection

~~~python
logical_plan.explain()
logical_plan.fingerprint()
logical_plan.required_capabilities
logical_plan.lineage
~~~

explain performs no engine execution.

---

# 35. Optimizer

Optimization remains within the LogicalPlan contract:

~~~python
from pytransformkit.planning import (
    LogicalOptimizer,
)

optimized = (
    LogicalOptimizer()
    .optimize(
        logical_plan
    )
)
~~~

The return type is LogicalPlan.

There is no stable public OptimizedLogicalPlan type.

---

# 36. EngineRegistry

Canonical explicit engine registration:

~~~python
from pytransformkit.engines import (
    EngineRegistry,
)

from pytransformkit.adapters.pandas import (
    PandasEngineAdapter,
)

registry = EngineRegistry()

registry.register(
    PandasEngineAdapter()
)
~~~

Importing an adapter does not automatically mutate a global registry.

---

# 37. EngineRegistry behavior

Stable behavior SHOULD include:

~~~python
registry.register(adapter)
registry.unregister("pandas")
registry.get("pandas")
registry.has("pandas")
registry.list()
registry.capabilities(
    "pandas"
)
~~~

Duplicate registration fails unless explicit replacement is requested.

---

# 38. EngineAdapter protocol

The stable extension protocol is conceptually:

~~~python
class EngineAdapter(Protocol):

    @property
    def descriptor(
        self,
    ) -> EngineDescriptor:
        ...

    def validate(
        self,
        plan: LogicalPlan,
    ) -> EngineValidationResult:
        ...

    def execute(
        self,
        request: EngineExecutionRequest,
    ) -> EngineExecutionResult:
        ...
~~~

Exact request/result members are frozen through conformance tests and the implementation roadmap.

---

# 39. EngineDescriptor

EngineDescriptor SHOULD expose:

~~~text
id
display_name
engine_version
adapter_version
capabilities
execution_modes
~~~

Published engine IDs such as pandas and polars are stable identifiers.

---

# 40. Capability

Capabilities SHOULD be typed enum-like values.

Representative usage:

~~~python
from pytransformkit.engines import (
    Capability,
)

Capability.JOIN_LEFT
Capability.AGGREGATE
Capability.WINDOW
~~~

Unknown future capabilities are not interpreted as supported by older adapters.

---

# 41. InputBinding

InputBinding connects one logical plan input to physical data.

Portable resource binding:

~~~python
binding = InputBinding.from_resource(
    input_name="orders",
    resource=ResourceReference(
        scheme="file",
        locator=(
            "/data/orders.parquet"
        ),
        media_type=(
            "application/"
            "vnd.apache.parquet"
        ),
    ),
)
~~~

No file is opened during construction.

---

# 42. Native local binding

~~~python
binding = InputBinding.from_native(
    input_name="orders",
    value=orders_df,
    engine="pandas",
)
~~~

from_native is explicitly process-local.

The bound native value is not serializable as durable workflow or wire state.

---

# 43. InputBinding invariants

InputBinding validates:

~~~text
logical input name
binding kind
engine compatibility when native
ownership/lifetime
portable versus process-local status
optional schema evidence
~~~

InputBinding does not redefine Dataset semantics.

---

# 44. ResourceReference

ResourceReference is the portable physical-resource identity/location contract.

Conceptual construction:

~~~python
resource = ResourceReference(
    scheme="file",
    locator=(
        "/data/orders.parquet"
    ),
    media_type=(
        "application/"
        "vnd.apache.parquet"
    ),
)
~~~

Credential values MUST NOT be embedded.

---

# 45. OutputBinding

Canonical output materialization:

~~~python
output = OutputBinding.to_resource(
    output_name="customer_mart",
    resource=ResourceReference(
        scheme="file",
        locator=(
            "/data/"
            "customer_mart.parquet"
        ),
    ),
    mode="create_new",
)
~~~

OutputBinding controls physical materialization only.

It does not create a governed DatasetVersion.

---

# 46. PhysicalHandle

PhysicalHandle MAY be publicly available under pytransformkit.runtime for advanced local integrations.

It is process-local and non-portable by default.

It SHOULD remain absent from root exports unless broad user need is proven.

---

# 47. Runtime construction

Canonical construction:

~~~python
runtime = TransformationRuntime(
    engines=registry,
)
~~~

Runtime MAY additionally accept explicit resource resolver, telemetry, clock, ID generator and plugin registry dependencies.

Hidden mandatory singletons are prohibited.

---

# 48. execute API

Canonical execution:

~~~python
result = runtime.execute(
    plan,
    engine="pandas",
    inputs={
        "customers": (
            InputBinding
            .from_native(
                "customers",
                customers_df,
                engine="pandas",
            )
        ),
        "orders": (
            InputBinding
            .from_native(
                "orders",
                orders_df,
                engine="pandas",
            )
        ),
    },
    outputs={
        "customer_mart": (
            OutputBinding
            .to_resource(
                "customer_mart",
                ResourceReference(
                    scheme="file",
                    locator=(
                        "/data/"
                        "customer_mart"
                        ".parquet"
                    ),
                ),
            )
        ),
    },
    correlation=correlation,
)
~~~

Output bindings MAY be omitted for local in-memory result use.

---

# 49. Accepted plan types

TransformationRuntime.execute SHOULD accept:

~~~text
TransformationPlan
    runtime compiles internally

LogicalPlan
    runtime uses precompiled representation
~~~

The two paths preserve equivalent logical semantics.

---

# 50. Engine selection

The engine argument is explicit unless TransformationRuntime was constructed with an explicit default-engine policy.

Installed-package detection MUST NOT silently decide the engine.

Hidden cross-engine fallback is prohibited.

---

# 51. Correlation

TransformationRuntime accepts CorrelationContext.

If omitted, runtime MAY create one.

TransformationExecutionId always remains distinct from CorrelationId and TraceId.

---

# 52. TransformationExecutionId

TransformationExecutionId is an immutable typed identifier.

It SHOULD support string conversion and parsing.

The exact textual encoding is not the semantic contract unless separately frozen.

---

# 53. TransformationResult

TransformationResult SHOULD expose:

~~~text
execution_id
status
engine
outputs
schemas
diagnostics
lineage
failure
plan_fingerprint
correlation
~~~

The result is immutable.

---

# 54. ExecutionStatus

Stable terminal statuses SHOULD include:

~~~text
SUCCEEDED
FAILED
CANCELLED
TIMED_OUT
UNKNOWN_OUTCOME
~~~

Additional internal/transitional states belong to TransformationExecution records rather than final-result compatibility unless promoted intentionally.

---

# 55. Result outputs

Result outputs are keyed by plan output name.

An output MAY expose:

~~~text
ResourceReference
optional process-local PhysicalHandle
Schema
materialization metadata
~~~

Portable and process-local values must be distinguishable.

---

# 56. Failure behavior

Programmer/configuration errors normally raise typed exceptions.

Execution failures MUST expose structured FailureEvidence through the raised exception, result, or both according to runtime policy.

Consumers MUST NOT need to parse human exception messages.

---

# 57. Diagnostics

A structured Diagnostic SHOULD include:

~~~text
code
severity
summary
optional details
location/context
related node/field
~~~

Stable diagnostic codes used by automation become compatibility contracts.

---

# 58. Exception hierarchy

Target public hierarchy:

~~~text
PyTransformKitError
    ValidationError
    CompilationError
    UnsupportedCapabilityError
    BindingError
    ResourceResolutionError
    ExecutionError
    SerializationError
    PluginError
~~~

The hierarchy may gain additive subclasses after 1.0.

---

# 59. Structured exception evidence

Execution exceptions SHOULD expose:

~~~text
category
code
failure_evidence
execution_id when allocated
correlation
diagnostics
cause
~~~

Native engine errors may be retained as cause without becoming public semantic contracts.

---

# 60. Lineage API

Lineage values are available through pytransformkit.lineage.

A lineage graph/view is a projection of lineage semantics, not a TransformationGraph authoring object.

Representative query:

~~~python
record = (
    result
    .lineage
    .field(
        "customer_mart."
        "paid_revenue"
    )
)

record.sources
record.kind
record.confidence
~~~

---

# 61. Lineage confidence

Stable confidence values SHOULD include:

~~~text
EXACT
DECLARED
INFERRED
PARTIAL
UNKNOWN
~~~

Built-in declarative transformations SHOULD produce EXACT when derivation is provable.

---

# 62. Serialization

Serialization uses explicit codecs rather than generic object dumping.

Representative API:

~~~python
from pytransformkit.serialization import (
    LogicalPlanCodec,
    TransformationPlanCodec,
)

payload = (
    TransformationPlanCodec
    .to_json(plan)
)

plan2 = (
    TransformationPlanCodec
    .from_json(payload)
)
~~~

Wire envelopes contain contract and contract_version.

---

# 63. Portable plan restrictions

TransformationPlanCodec MUST reject or explicitly mark unsupported non-portable constructs such as:

~~~text
arbitrary Python closures
unregistered Python UDFs
native DataFrames
engine sessions
provider clients
raw credentials
~~~

Serialization never falls back to pickle, cloudpickle or dill.

---

# 64. LogicalPlan wire contract

LogicalPlanCodec SHOULD preserve:

~~~text
contract/version
logical nodes
expressions
schemas
input/output identities
semantic options
capability requirements
lineage metadata where declared
fingerprint
~~~

LogicalPlan contract version is independent from package version.

---

# 65. Explain

TransformationPlan and LogicalPlan SHOULD expose explain convenience:

~~~python
plan.explain()

logical_plan.explain(
    format="text"
)

logical_plan.explain(
    format="json"
)
~~~

Human-oriented formatting may evolve without being byte-stable.

Machine-readable explain formats require explicit versioning if declared stable.

---

# 66. Pandas adapter

Stable install surface:

~~~text
pip install pytransformkit[pandas]
~~~

Stable import:

~~~python
from pytransformkit.adapters.pandas import (
    PandasEngineAdapter,
)
~~~

Pandas is an official stable V1 engine target.

---

# 67. Polars adapter

Stable install surface:

~~~text
pip install pytransformkit[polars]
~~~

Stable import:

~~~python
from pytransformkit.adapters.polars import (
    PolarsEngineAdapter,
)
~~~

Polars is an official stable V1 engine target.

---

# 68. PyArrow and DuckDB

Target imports MAY be:

~~~python
from pytransformkit.adapters.pyarrow import (
    PyArrowEngineAdapter,
)

from pytransformkit.adapters.duckdb import (
    DuckDBEngineAdapter,
)
~~~

Their final 1.0 stability level depends on conformance readiness.

They may remain PROVISIONAL without weakening the Pandas/Polars contract.

---

# 69. Engine-specific escape hatches

Engine-specific APIs live under qualified adapter namespaces.

The root API MUST NOT grow pandas_* or polars_* authoring functions.

Using an engine-specific escape hatch must make reduced portability explicit.

---

# 70. Raw SQL

Raw SQL, if supported by SQL-capable adapters, is an explicit trust-sensitive escape hatch.

It SHOULD use qualified adapter APIs or a distinct trusted SQL expression type.

Raw SQL is not accepted silently as a generic portable Expression.

---

# 71. UDFs

The API distinguishes:

~~~text
portable named function
engine-specific function
trusted local Python callable
opaque external function
~~~

Arbitrary Python UDFs are not silently serializable or assumed portable.

---

# 72. Plugins

Discovery and activation are separate.

Representative API:

~~~python
from pytransformkit.plugins import (
    PluginRegistry,
)

plugins = (
    PluginRegistry
    .discover()
)

plugins.activate(
    "my-engine-plugin"
)
~~~

Untrusted payloads MUST NOT activate plugins.

---

# 73. Plugin compatibility

Stable plugin protocols declare compatible package/protocol ranges.

Incompatible plugins fail clearly during activation or registration.

Core import does not eagerly activate installed plugins.

---

# 74. Physical I/O API

Reader/Writer extension ports use ResourceReference and binding concepts.

They MUST NOT consume PyIngestKit DatasetVersion objects directly in PyTransformKit core.

Physical write modes SHOULD use typed values such as:

~~~text
CREATE_NEW
FAIL_IF_EXISTS
REPLACE
APPEND
~~~

These modes never imply governed publication.

---

# 75. Credentials

CredentialReference MAY appear in runtime resource configuration through the ecosystem contract.

Raw credentials MUST NOT appear in TransformationPlan, LogicalPlan, ResourceReference serialization, diagnostics or lineage.

---

# 76. Thread/process safety

Every stable adapter and runtime service documents:

~~~text
thread safety
reentrancy
process safety
async behavior
resource ownership
cleanup semantics
~~~

Normal use must not depend on hidden mutable globals.

---

# 77. Stability tiers

At 1.0:

~~~text
STABLE
    canonical root API
    Dataset/Schema/Expression
    TransformationPlan
    LogicalPlan
    TransformationRuntime
    InputBinding/OutputBinding
    Pandas/Polars engine contract
    stable codecs and errors

PROVISIONAL
    emerging adapters
    advanced plugin/optimizer surfaces not fully frozen

INTERNAL
    graph implementation
    physical lowering internals
    caches
    optimizer implementation details
~~~

Documentation must make stability level visible.

---

# 78. Legacy Pipeline migration

Legacy Pipeline is not the canonical 1.0 authoring root.

~~~text
Pipeline
    → TransformationPlan
~~~

A permanent root alias SHOULD NOT be added merely for convenience.

A temporary deprecation path MAY exist before 1.0 if needed.

---

# 79. Legacy RunPipelineService migration

~~~text
RunPipelineService
    → TransformationRuntime
~~~

Existing implementation may be reused internally, but stable public naming follows the target architecture.

---

# 80. Local Pandas example

~~~python
from pytransformkit import (
    DataType,
    Field,
    InputBinding,
    Schema,
    TransformationPlan,
    TransformationRuntime,
    col,
    lit,
)

from pytransformkit import (
    functions as fn,
)

from pytransformkit.engines import (
    EngineRegistry,
)

from pytransformkit.adapters.pandas import (
    PandasEngineAdapter,
)

customer_schema = Schema(
    fields=(
        Field(
            "customer_id",
            DataType.string(),
            nullable=False,
        ),
        Field(
            "country",
            DataType.string(),
        ),
    )
)

order_schema = Schema(
    fields=(
        Field(
            "order_id",
            DataType.string(),
            nullable=False,
        ),
        Field(
            "customer_id",
            DataType.string(),
            nullable=False,
        ),
        Field(
            "amount",
            DataType.decimal(
                18,
                2,
            ),
        ),
        Field(
            "status",
            DataType.string(),
        ),
    )
)

b = TransformationPlan.builder(
    "customer_mart"
)

customers = b.input(
    "customers",
    schema=customer_schema,
)

orders = b.input(
    "orders",
    schema=order_schema,
)

paid = b.filter(
    "paid_orders",
    source=orders,
    where=(
        col("status")
        == lit("PAID")
    ),
)

stats = b.aggregate(
    "order_stats",
    source=paid,
    group_by=(
        col("customer_id"),
    ),
    metrics={
        "paid_order_count": (
            fn.count(
                col("order_id")
            )
        ),
        "paid_revenue": (
            fn.sum(
                col("amount")
            )
        ),
    },
)

mart = b.join(
    "customer_mart_join",
    left=customers,
    right=stats,
    how="left",
    on=(
        (
            "customer_id",
            "customer_id",
        ),
    ),
)

plan = (
    b
    .output(
        "customer_mart",
        mart,
    )
    .build()
)

registry = EngineRegistry()

registry.register(
    PandasEngineAdapter()
)

runtime = TransformationRuntime(
    engines=registry
)

result = runtime.execute(
    plan,
    engine="pandas",
    inputs={
        "customers": (
            InputBinding
            .from_native(
                "customers",
                customers_df,
                engine="pandas",
            )
        ),
        "orders": (
            InputBinding
            .from_native(
                "orders",
                orders_df,
                engine="pandas",
            )
        ),
    },
)
~~~

This example is normative in architectural shape.

Minor convenience overloads may be added only when they preserve the same semantics.

---

# 81. Inspect before execution

~~~python
from pytransformkit.planning import (
    TransformationCompiler,
)

logical = (
    TransformationCompiler()
    .compile(plan)
)

print(
    logical.explain()
)

print(
    logical.required_capabilities
)

print(
    logical.fingerprint()
)
~~~

No physical data is executed during this sequence.

---

# 82. Same plan on Polars

~~~python
from pytransformkit.adapters.polars import (
    PolarsEngineAdapter,
)

registry.register(
    PolarsEngineAdapter()
)

result = runtime.execute(
    plan,
    engine="polars",
    inputs={
        "customers": (
            InputBinding
            .from_native(
                "customers",
                customers_pl,
                engine="polars",
            )
        ),
        "orders": (
            InputBinding
            .from_native(
                "orders",
                orders_pl,
                engine="polars",
            )
        ),
    },
)
~~~

The TransformationPlan does not change merely because the engine changes.

---

# 83. Sibling handoff

PyTransformKit itself does not import PyIngestKit.

A consumer-side integration adapts:

~~~text
DatasetVersionReference
    ↓
resolve ResourceReference
    ↓
InputBinding.from_resource(...)
    ↓
TransformationRuntime.execute(...)
~~~

TransformationResult exposes ResourceReference suitable for later PyIngestKit publication.

---

# 84. API anti-patterns

Rejected patterns include:

~~~text
native DataFrame stored inside logical Dataset
silent selection of whichever engine is installed
pickle as durable plan serialization
mandatory global engine registry
TransformationResult pretending to create DatasetVersion
root-level engine-specific transformation APIs
public TransformationGraph required for normal authoring
public OptimizedLogicalPlan as a duplicate logical contract
~~~

---

# 85. Root exclusion list

The root package MUST NOT export by default:

~~~text
TransformationGraph
OptimizedLogicalPlan
generic PhysicalPlan
private PlanNode classes
optimizer implementation classes
engine-native wrappers
private codec internals
plugin loader internals
cache implementation classes
~~~

---

# 86. Compatibility tests

Release CI MUST snapshot and compare at least:

~~~text
root exports
qualified stable exports
public signatures
constructors
Protocol members
exception hierarchy
enum members
stable extra names
stable engine IDs
wire contract versions
~~~

Unexpected stable-surface drift blocks release.

---

# 87. Acceptance criteria

PyTransformKit V1 public API is accepted when:

1. root imports work with core-only dependencies;
2. TransformationPlan is the canonical authoring root;
3. builder authoring produces immutable plans;
4. no public TransformationGraph is required;
5. TransformationCompiler produces LogicalPlan without execution;
6. LogicalPlan is inspectable and engine-neutral;
7. OptimizedLogicalPlan is not a distinct public type;
8. EngineRegistry registration is explicit;
9. Pandas and Polars implement one stable EngineAdapter contract;
10. engine selection is explicit;
11. InputBinding separates logical data from physical data;
12. ResourceReference remains portable;
13. native bindings are explicitly process-local;
14. TransformationRuntime.execute accepts TransformationPlan or LogicalPlan;
15. TransformationResult exposes structured output, diagnostics and failure;
16. core runtime never creates governed DatasetVersion;
17. serialization uses versioned non-executable codecs;
18. plugins require explicit activation;
19. legacy Pipeline and RunPipelineService migration is documented;
20. API freeze tests pass against built wheels.

---

# 88. Normative API invariants

### PTK-API-INV-01 — Root API is curated

Only canonical stable concepts are promoted to package root.

### PTK-API-INV-02 — Authoring is engine-neutral

TransformationPlan, Dataset, Schema and Expression contain no native engine objects.

### PTK-API-INV-03 — TransformationPlan is immutable after build

Runtime execution never mutates the logical declaration.

### PTK-API-INV-04 — LogicalPlan is compilation output

Compilation is deterministic and side-effect free with respect to physical execution.

### PTK-API-INV-05 — Engine selection is explicit

Installed libraries do not silently determine execution semantics.

### PTK-API-INV-06 — Bindings own physical association

Logical Dataset declarations do not transport native data.

### PTK-API-INV-07 — Results distinguish portable and process-local values

PhysicalHandle cannot masquerade as durable reference.

### PTK-API-INV-08 — Failure semantics are structured

Consumers do not parse exception strings to understand execution outcomes.

### PTK-API-INV-09 — Serialization is explicit and safe

No durable public API falls back to executable Python object serialization.

### PTK-API-INV-10 — Plugins are opt-in

Discovery does not equal activation.

### PTK-API-INV-11 — PyTransformKit does not publish DatasetVersion

Transformation output remains a resource/result until a different owner governs publication.

### PTK-API-INV-12 — Stable API is machine-checkable

Exports, signatures, protocols, enums and contracts are protected continuously in CI.

---

# 89. Canonical API summary

~~~text
AUTHORING
    DataType / Field / Schema / Dataset
    Expression / col / lit / functions
    TransformationPlan.builder(...)

PLANNING
    TransformationCompiler
    LogicalPlan
    LogicalOptimizer

RUNTIME
    TransformationRuntime
    InputBinding
    OutputBinding
    TransformationExecutionId
    TransformationResult

ENGINE EXTENSION
    EngineRegistry
    EngineAdapter
    EngineDescriptor
    Capability

PORTABLE BOUNDARIES
    ResourceReference
    CorrelationContext
    FailureEvidence
    explicit codecs
~~~

---

# 90. Final API statement

PyTransformKit 1.0 exposes one coherent progression:

~~~text
Dataset + Expression
        ↓
TransformationPlan
        ↓
LogicalPlan
        ↓
InputBinding + EngineAdapter
        ↓
TransformationRuntime.execute
        ↓
TransformationResult
~~~

> **The stable API lets users define transformation meaning independently from engines, inspect its compiled logical form, bind physical data explicitly and execute it without collapsing ingestion, publication or workflow semantics into PyTransformKit.**

This specification is the normative baseline for:

~~~text
PYTRANSFORMKIT_V1_REVISED_IMPLEMENTATION_ROADMAP.md
~~~
