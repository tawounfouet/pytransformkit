# Migrating to the PyTransformKit V1 API

This guide covers migration from the pre-V1 Pipeline-oriented surface to the
canonical TransformationPlan/TransformationRuntime model frozen by LOT-26.

## 1. Authoring root

Before:

~~~python
from pytransformkit import Pipeline

pipeline = Pipeline(...)
~~~

V1:

~~~python
from pytransformkit import TransformationPlan

builder = TransformationPlan.builder("customer_mart")
source = builder.input("customers", schema=customer_schema)
result = builder.filter(
    "active_customers",
    source=source,
    where=col("status") == "ACTIVE",
)
plan = builder.output("result", result).build()
~~~

`Pipeline` is not a canonical root export. Temporary pre-1.0 root access emits a
`DeprecationWarning`.

## 2. Execution service

Before:

~~~python
from pytransformkit import RunPipelineService
~~~

V1:

~~~python
from pytransformkit import TransformationRuntime
from pytransformkit.engines import EngineRegistry
from pytransformkit.adapters.pandas import PandasEngineAdapter

engines = EngineRegistry()
engines.register(PandasEngineAdapter())

runtime = TransformationRuntime(engines=engines)
~~~

Execution is explicit:

~~~python
result = runtime.execute(
    plan,
    engine="pandas",
    inputs={
        "customers": InputBinding.from_native(
            "customers",
            customers_df,
            engine="pandas",
        )
    },
)
~~~

There is no implicit selection of whichever engine happens to be installed.

## 3. EngineRegistry

Pre-V1 root access:

~~~python
from pytransformkit import EngineRegistry
~~~

moves to:

~~~python
from pytransformkit.engines import EngineRegistry
~~~

The root compatibility resolver may warn during the migration window.

## 4. ExecutionMode

Use:

~~~python
from pytransformkit.runtime import ExecutionMode
~~~

rather than the legacy root compatibility name.

## 5. Resource/write types

Use qualified runtime or writer namespaces:

~~~python
from pytransformkit.runtime import (
    CredentialReference,
    ResourceReference,
    RetrySafety,
    WriteMode,
    WriteStatus,
)
~~~

or:

~~~python
from pytransformkit.writers import WriteMode, WriteStatus
~~~

They are intentionally not canonical root exports.

## 6. Input and output bindings

Native process-local input:

~~~python
InputBinding.from_native(
    "orders",
    orders_df,
    engine="pandas",
)
~~~

Portable resource input:

~~~python
InputBinding.from_resource(
    "orders",
    ResourceReference(
        scheme="file",
        locator="orders.parquet",
    ),
)
~~~

Output materialization:

~~~python
OutputBinding.to_resource(
    "customer_mart",
    ResourceReference(
        scheme="file",
        locator="customer_mart.parquet",
    ),
    mode=WriteMode.CREATE_NEW,
)
~~~

Resource materialization is not governed dataset publication.

## 7. Expression and transformation namespaces

V1 provides explicit qualified namespaces:

~~~python
from pytransformkit.expressions import Expression
from pytransformkit.transformations import TransformationSpec
from pytransformkit import functions as fn
from pytransformkit import window
~~~

Internal `pytransformkit.domain.*` imports should be migrated when an equivalent
public namespace exists.

## 8. DataType factories

Instead of constructing common primitive types directly, V1 callers may use:

~~~python
DataType.string()
DataType.int64()
DataType.float64()
DataType.decimal(18, 2)
DataType.timestamp(timezone="UTC")
~~~

The concrete logical type classes remain available through qualified data/internal
surfaces where needed by advanced integrations, but portable application code should
prefer DataType factories.

## 9. Field dtype

Both forms are valid in the V1 line:

~~~python
field.data_type
field.dtype
~~~

`dtype` is an alias; it does not introduce native engine dtype semantics.

## 10. Schema names

The qualified V1 implementation uses:

~~~python
schema.names()
~~~

not `schema.names`.

This method form is frozen because it is already exercised across engine contracts.

## 11. LogicalPlan

Compilation:

~~~python
from pytransformkit.planning import TransformationCompiler

logical = TransformationCompiler().compile(plan)
~~~

Optimization remains:

~~~python
from pytransformkit.planning import LogicalOptimizer

optimized = LogicalOptimizer().optimize(logical)
~~~

The optimizer returns another `LogicalPlan`; there is no public
`OptimizedLogicalPlan`.

Logical lineage is inspected through:

~~~python
from pytransformkit import lineage

lineage_result = lineage.analyze(logical)
~~~

## 12. Exceptions

Catch public exceptions through:

~~~python
from pytransformkit.errors import (
    PyTransformKitError,
    ExecutionError,
    UnsupportedEngineCapabilityError,
)
~~~

Do not parse exception strings to determine failure category or retry semantics.

## 13. Serialization

Durable plan/resource/runtime references use explicit codecs:

~~~python
from pytransformkit.serialization import TransformationPlanCodec

payload = TransformationPlanCodec().to_json(plan)
restored = TransformationPlanCodec().from_json(payload)
~~~

Do not migrate durable state through `pickle`, `cloudpickle` or `dill`.

## 14. Plugins

Plugin discovery and activation remain distinct:

~~~python
from pytransformkit.plugins import PluginRegistry

registry = PluginRegistry.discover()
registry.activate("plugin-id")
~~~

Deserialization never activates plugins.

## 15. Migration checklist

A pre-V1 consumer is migrated when:

- no canonical code imports `Pipeline` from the root;
- no canonical code instantiates `RunPipelineService`;
- engine selection is explicit;
- native values enter through `InputBinding.from_native`;
- portable resources use `ResourceReference`;
- root resource/write enums have moved to qualified namespaces;
- durable state uses explicit codecs;
- internal domain imports have been replaced with public namespaces where available;
- tests run without relying on deprecated root compatibility names.

The compatibility aliases are migration aids, not a promise that they will remain
after the 1.0 transition window.


## 16. Release-candidate migration checkpoint

PyTransformKit `1.0.0rc1` freezes the canonical V1 migration target.

Consumers upgrading from the LOT-26 `0.8.0` baseline or the LOT-27 `0.9.0`
qualification line should verify all of the following before adopting V1 stable:

- imports use the canonical root or documented qualified namespaces;
- deprecated root compatibility aliases are not treated as new application API;
- persisted contracts are encoded with the explicit V1 serialization codecs;
- automation consumes public exception types and `PTK-*` error codes rather than
  parsing messages;
- plugins declare compatibility with plugin protocol V1 and a host range that
  includes the intended PyTransformKit 1.x deployment;
- engine-specific behavior relies only on capabilities published in the
  conformance matrix.

The default plugin V1 compatibility range is now `>=0.5.0,<2.0.0`. This was
corrected before RC freeze so a plugin using the default declaration remains
eligible for PyTransformKit `1.0.0`.

After `1.0.0rc1`, only blocker fixes are accepted before the stable release.
