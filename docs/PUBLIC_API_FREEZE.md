# PyTransformKit V1 Public API Freeze

> Freeze candidate: 0.8.0  
> Target stable release: 1.0.0  
> Normative source: `docs/specifications/PYTRANSFORMKIT_V1_PUBLIC_API_SPEC.md`

LOT-26 establishes the compatibility baseline that LOT-27 and LOT-28 must preserve
unless a deliberate pre-1.0 correction updates the normative specification, snapshot,
tests and migration guidance together.

## Canonical lifecycle

~~~text
DataType / Field / Schema / Expression
        ↓
TransformationPlan
        ↓
TransformationCompiler
        ↓
LogicalPlan
        ↓
InputBinding + explicit EngineAdapter
        ↓
TransformationRuntime.execute(...)
        ↓
TransformationResult
~~~

The package does not expose a required public `TransformationGraph`,
`OptimizedLogicalPlan` or universal `PhysicalPlan`.

## Frozen root surface

The package root remains curated around the canonical logical/runtime vocabulary:

~~~text
DataType
Dataset
Expression
Field
Schema
TransformationPlan
LogicalPlan
InputBinding
OutputBinding
TransformationRuntime
TransformationResult
TransformationExecutionId
ResourceReference
CredentialReference
RetrySafety
WriteMode
WriteStatus
col
lit
quality
window
lineage
diagnostics
~~~

Legacy `Pipeline`, `RunPipelineService` and `PipelineExecutionResult` remain
pre-V1 compatibility names resolved through deprecation access only. They are not
part of `pytransformkit.__all__`.

## Stable qualified namespaces

The V1 freeze protects these qualified surfaces:

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

The canonical stable adapter symbols are:

~~~python
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
~~~

PyArrow and DuckDB remain PROVISIONAL at this freeze. Their qualified namespaces may
evolve before a later explicit stability promotion.

## Stable extras

Stable installation API:

~~~text
pytransformkit[pandas]
pytransformkit[polars]
~~~

Provisional feature extras:

~~~text
pytransformkit[pyarrow]
pytransformkit[duckdb]
pytransformkit[io]
~~~

Development-only qualification extras:

~~~text
pytransformkit[dev]
pytransformkit[performance]
~~~

Renaming or removing a stable extra is a compatibility event.

## Plugin and wire contracts

Plugin entry-point group:

~~~text
pytransformkit.plugins
~~~

Plugin protocol version:

~~~text
1
~~~

The default plugin compatibility declaration covers PyTransformKit `>=0.5.0,<2.0.0`,
so protocol-v1 plugins can remain valid throughout the framework 1.x line.

All public wire codecs currently use contract version `1`. Contract versions remain
independent from the package version.

## Freeze artifact

The executable compatibility snapshot is:

~~~text
tests/fixtures/public_api/v1.json
~~~

It freezes:

- root exports;
- qualified stable exports;
- public signature shapes and defaults;
- extension Protocol members;
- public exception parentage and error codes;
- stable enum names and values;
- optional-extra names and stability tiers;
- official engine IDs/stability;
- plugin API/group/range;
- wire contract IDs and versions.

The corresponding gate is:

~~~text
tests/contract/api/test_public_api_freeze.py
~~~

A snapshot change is not automatically acceptable because tests can be updated.
Any intentional change must first be classified as additive, breaking, security-driven
or migration-related and then reflected in normative docs and release notes.

## Convenience alignment completed in LOT-26

The freeze also aligns frequently used V1 conveniences with the normative API:

- `DataType.boolean/int8/int16/int32/int64/uint8/uint16/uint32/uint64`;
- `DataType.float32/float64/decimal/string/binary/date/time/timestamp/duration`;
- `DataType.unknown()`;
- `Field.dtype` as the canonical read-only type alias;
- `Schema.fingerprint()`;
- `TransformationPlan.fingerprint()` and `TransformationPlan.explain()`;
- `LogicalPlan.required_capabilities`, `LogicalPlan.lineage` and
  `LogicalPlan.explain()`;
- public `pytransformkit.expressions` and `pytransformkit.transformations`
  namespaces.

A distinct logical NullType is not introduced merely to satisfy API symmetry. NULL is
currently represented through field nullability and expression semantics; adding a new
logical type would require its own cross-engine and wire qualification.

## Compatibility rule after freeze

From LOT-26 through the 1.0 release:

1. existing STABLE names/signatures/enums/contracts do not change accidentally;
2. additive APIs require tests and documentation;
3. PROVISIONAL surfaces may still evolve with explicit release notes;
4. unsafe behavior may be tightened even when compatibility would otherwise prefer
   preservation;
5. wire and plugin protocol versions evolve independently from package versions;
6. the exact built wheel remains the authoritative release artifact.
