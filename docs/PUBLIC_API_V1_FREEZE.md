# PyTransformKit V1 Public API Freeze

> Baseline line: `0.8.x`  
> Freeze lot: LOT-26  
> Target stable release: `1.0.0`

LOT-26 turns the intended V1 API into an executable compatibility contract.

The machine-readable baseline is:

~~~text
contracts/public_api_v1.json
~~~

The verifier is:

~~~text
scripts/public_api_snapshot.py
~~~

Release CI compares the built package against that baseline.

## Canonical root

The stable root is intentionally small:

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

The root may also expose stable convenience namespaces such as `quality`,
`lineage`, `diagnostics` and `window`, but engine-specific and compatibility
symbols are not canonical root vocabulary.

## Qualified stable namespaces

The freeze covers:

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
pytransformkit.quality
pytransformkit.window
pytransformkit.conformance
pytransformkit.readers
pytransformkit.writers
pytransformkit.errors
pytransformkit.adapters.pandas
pytransformkit.adapters.polars
~~~

PyArrow and DuckDB remain provisional execution adapters at the semantic
conformance level even though their extras, engine IDs and wire/interchange
boundaries are compatibility-tracked.

## Freeze dimensions

The snapshot protects:

- every `__all__` export in the frozen namespaces;
- signatures of canonical V1 constructors/services/functions;
- extension Protocol members;
- public exception inheritance;
- selected public enum names and values;
- stable runtime extra names;
- tooling extra names;
- official engine IDs;
- codec contract identifiers and wire versions;
- absence of forbidden public duplicate-plan types.

## Root exclusions

The root does not promote:

~~~text
Pipeline
RunPipelineService
ExecutionContext
EngineRegistry
CredentialReference
RetrySafety
WriteMode
WriteStatus
TransformationGraph
OptimizedLogicalPlan
PhysicalPlan
~~~

The first group is available only through qualified namespaces or temporary
pre-1.0 compatibility resolution. The last three do not exist as stable public
types.

## Pre-1.0 compatibility

Legacy root access such as:

~~~python
import pytransformkit

pytransformkit.Pipeline
pytransformkit.RunPipelineService
pytransformkit.WriteMode
~~~

emits `DeprecationWarning` and does not place those names in `pytransformkit.__all__`.

This compatibility path exists to make migration observable before 1.0. It is
not part of the canonical V1 facade.

## Data model reconciliation

The frozen implementation uses:

~~~python
Field("amount", DataType.decimal(18, 2))
field.data_type
field.dtype
schema.names()
~~~

`Field.dtype` is a stable convenience alias for `data_type`.

`Schema.names()` remains a method because that form has already been qualified
through the implementation and adapter contract suites. LOT-26 does not turn it
into a property merely to match an earlier aspirational example.

Logical `Dataset` identity remains explicit and UUID-backed. Normal plan
authoring should obtain Dataset values from `TransformationPlan.builder().input()`
and subsequent builder transformations rather than constructing physical-looking
Dataset values manually.

## DataType factories

The V1 convenience factory surface includes:

~~~text
boolean
int8 / int16 / int32 / int64
uint8 / uint16 / uint32 / uint64
float32 / float64
decimal
string
binary
date
time
timestamp
duration
list_of
struct
map_of
unknown
~~~

A dedicated `NullType` is not frozen in V1. Nullability belongs to Field/Schema
semantics and null literals use ordinary expression values.

## LogicalPlan inspection

The frozen LogicalPlan surface includes its immutable node/output structure,
canonical plan identity aliases, input/output names, output schema lookup and
semantic fingerprinting.

Lineage is obtained through:

~~~python
from pytransformkit import lineage

result = lineage.analyze(logical_plan)
~~~

Capability analysis remains part of runtime/engine compatibility validation and
is not duplicated as mutable state on LogicalPlan.

## Compatibility rule

After the 1.0 freeze, changes to the stable snapshot require one of:

1. an additive compatible change accepted by the release policy;
2. a documented deprecation path;
3. a new major version for incompatible changes;
4. an explicitly documented urgent security exception.

The API snapshot is evidence, not a replacement for semantic tests. Engine,
serialization, security, optimizer and cross-engine conformance suites remain
mandatory alongside it.


## LOT-27 pre-RC amendment

LOT-27 identified one release blocker in the frozen signature surface:
`PluginCompatibility()` defaulted to a host range ending at `<1.0.0`, which
would reject PyTransformKit `1.0.0` itself.

Before the RC freeze, that default was deliberately corrected to
`>=0.5.0,<2.0.0` for plugin protocol V1. The change affected only the
`signatures` category of the public API snapshot. All exports, Protocol members,
exception hierarchy, enum values, extras, engine IDs and wire contracts remained
unchanged.

The amended signature hash is the V1 RC baseline and is protected by both the
built-wheel API gate and the consumer compatibility gate.
