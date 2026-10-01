# Migrating to the PyTransformKit V1 API

> Migration baseline: LOT-26 / 0.8.0  
> Target: 1.0.0

The V1 API replaces the original linear `Pipeline` / `RunPipelineService` vocabulary
with an engine-neutral declaration/compile/runtime model.

## Migration map

~~~text
Pipeline
    → TransformationPlan

PipelinePlanner
    → TransformationCompiler

RunPipelineService
    → TransformationRuntime

PipelineExecutionResult
    → TransformationResult

DatasetHandle
    → PhysicalHandle

root EngineRegistry compatibility access
    → pytransformkit.engines.EngineRegistry

root ExecutionMode compatibility access
    → pytransformkit.runtime.ExecutionMode
~~~

The old names remain available only as pre-V1 compatibility paths and are deliberately
absent from the canonical root `__all__`.

## Authoring migration

Legacy:

~~~python
from pytransformkit import Pipeline

pipeline = (
    Pipeline.create(
        "active_customers",
        schema,
    )
    .filter(
        col("status") == "ACTIVE"
    )
    .select(
        "customer_id",
        "email",
    )
)
~~~

V1:

~~~python
from pytransformkit import (
    TransformationPlan,
    col,
)

builder = TransformationPlan.builder(
    "active_customers"
)

customers = builder.input(
    "customers",
    schema=schema,
)

active = builder.filter(
    "active_only",
    source=customers,
    where=(
        col("status")
        == "ACTIVE"
    ),
)

selected = builder.select(
    "customer_projection",
    source=active,
    columns=(
        "customer_id",
        "email",
    ),
)

plan = (
    builder
    .output(
        "result",
        selected,
    )
    .build()
)
~~~

The V1 model supports named multi-input/multi-output plans and therefore does not preserve
the legacy linear chaining shape as the canonical abstraction.

## Execution migration

Legacy:

~~~python
service = RunPipelineService(
    registry
)

result = service.run(
    pipeline,
    input_handle,
    engine_id="pandas",
)
~~~

V1:

~~~python
from pytransformkit import (
    InputBinding,
    TransformationRuntime,
)

runtime = TransformationRuntime(
    engines=registry
)

result = runtime.execute(
    plan,
    engine="pandas",
    inputs={
        "customers": (
            InputBinding.from_native(
                "customers",
                customers_df,
                engine="pandas",
            )
        )
    },
)
~~~

The V1 runtime accepts either `TransformationPlan` or precompiled `LogicalPlan`.
Engine choice is explicit and there is no installed-engine fallback.

## Resource migration

Physical resource input should use:

~~~python
InputBinding.from_resource(
    "orders",
    ResourceReference(
        scheme="file",
        locator="data/orders.parquet",
    ),
)
~~~

Credential values do not belong in the locator. Use `CredentialReference` through the
binding when the provider requires credentials.

## Result migration

Use `TransformationResult` for:

- named outputs;
- output Schema;
- execution identity/status;
- diagnostics;
- failure/retry evidence;
- logical lineage;
- execution manifest;
- physical write results.

A result is not a governed DatasetVersion. Publication remains outside PyTransformKit.

## Import migration

Prefer:

~~~python
from pytransformkit.engines import EngineRegistry
from pytransformkit.runtime import ExecutionMode
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
~~~

Do not build new code around compatibility-only root attributes.

## Deprecation posture

Compatibility aliases exist to ease the pre-1.0 transition, but they are not frozen as
canonical V1 API. New code should migrate before 1.0 rather than relying on their
continued root-level availability.
