# Runtime and Engine Safety Contract

> V1 freeze line: `0.8.x`

This document defines the concurrency, ownership and lifecycle expectations for
the stable PyTransformKit runtime and the stable Pandas/Polars adapters.

## Transformation declarations

`Schema`, `Expression`, `TransformationPlan` and `LogicalPlan` are immutable
semantic values after construction. They may be reused across executions.

The mutable `TransformationPlanBuilder` is an authoring helper and should not be
mutated concurrently.

## EngineRegistry

`EngineRegistry` is mutable during application configuration.

Registration, replacement, removal and `freeze()` are not advertised as concurrent
mutation operations. Configure the registry before sharing a runtime between worker
contexts.

After configuration, adapter lookup is read-only. No global registry is mutated by
importing PyTransformKit or an official adapter.

## TransformationRuntime

`TransformationRuntime.execute()` is synchronous. PyTransformKit does not expose a
native async execution API in V1.

Each execution receives a new `TransformationExecutionId` and its own execution
context. Runtime execution does not mutate TransformationPlan or LogicalPlan values.

The V1 contract does not promise that one runtime/adapter instance can be called
concurrently from arbitrary threads. Applications needing parallel execution should
use execution isolation appropriate to the selected engine and provider.

## Native input ownership

`InputBinding.from_native` is process-local.

The caller retains ownership of the supplied native DataFrame/Table/relation. A native
binding is not durable state and must not be transferred through workflow serialization
as though it were a ResourceReference.

## Pandas adapter

Pandas is a stable eager V1 adapter.

- the adapter does not close or dispose caller-owned DataFrames;
- framework transformations return process-local Pandas handles;
- no async execution contract is provided;
- sharing mutable caller DataFrames across threads remains the caller's responsibility;
- the adapter does not register itself globally on import.

## Polars adapter

Polars is a stable eager/lazy V1 adapter.

- caller-owned DataFrame/LazyFrame values remain process-local;
- lazy execution can return a LazyFrame without implicit collection;
- collection/materialization is explicit at the consumer boundary unless a qualified
  transformation such as a quality gate requires physical evaluation;
- no async execution contract is provided;
- the adapter does not register itself globally on import.

## PyArrow adapter

PyArrow remains PROVISIONAL as a transformation engine. Arrow interchange values are
explicit physical boundary values and are not logical Dataset state.

## DuckDB adapter

DuckDB remains PROVISIONAL for V1 semantic stability.

Its connection ownership rule is explicit:

- an internally created connection is owned and closed by the adapter;
- a caller-supplied connection is not closed or committed implicitly;
- lazy relations may retain connection-bound state until materialization/cleanup;
- connection/thread behavior is governed by DuckDB's native contract in addition to
  PyTransformKit's explicit ownership rules.

## Resource I/O

Reader/Writer implementations own only the physical operations they start.

The local reference profile confines paths beneath its configured root. Resource writes
use typed write modes and expose `UNKNOWN_OUTCOME` when commit certainty is lost.

A successful physical write is not a governed dataset publication.

## Telemetry

Telemetry is best-effort and must not control business execution.

A failing telemetry sink:

- does not cause transformation replay;
- does not change a successful engine result into a business failure;
- produces structured diagnostic evidence.

## Process boundaries

`PhysicalHandle`, `CancellationToken`, native DataFrames, LazyFrames, Arrow objects,
DuckDB relations/connections and plugin instances are process-local unless an external
provider explicitly defines a stronger contract.

Portable cross-process state should use:

- TransformationPlan/LogicalPlan codecs;
- ResourceReference;
- TransformationExecutionReference;
- lineage/diagnostic/manifest codecs where appropriate.

## No hidden globals

Normal V1 use does not depend on:

- a globally selected engine;
- an import-time plugin registry;
- an import-time network connection;
- an implicit current execution;
- an implicit global credential provider.

Applications explicitly construct and inject registries, adapters, resource I/O and
telemetry dependencies.
