# PyTransformKit 1.0.0rc1 Release Notes

PyTransformKit `1.0.0rc1` is the first release candidate for the V1 public
contract. It closes the implementation phase and starts the blocker-only
validation window before `1.0.0`.

## What is frozen

The release candidate freezes the V1 compatibility surface qualified by LOT-26
and LOT-27:

- canonical `TransformationPlan -> LogicalPlan -> TransformationRuntime` flow;
- public imports, signatures, enums and Protocol members;
- public exception hierarchy and machine-readable error codes;
- optional-extra names and official engine IDs;
- versioned serialization contract identifiers and wire versions;
- plugin protocol V1 and its entry-point group;
- Pandas and Polars as STABLE V1 engines;
- PyArrow and DuckDB as explicitly PROVISIONAL engines.

The machine-readable evidence is stored under:

```text
contracts/public_api_v1.json
contracts/error_codes_v1.json
contracts/consumer_compatibility_v1.json
contracts/release_qualification_v1.json
```

## Qualification

The RC is qualified on Python 3.11, 3.12, 3.13 and 3.14.

Release gates cover:

- static quality and typing;
- Pandas, Polars, PyArrow and DuckDB engine contracts;
- cross-engine semantics and Customer 360 conformance;
- physical I/O;
- canonical serialization and migrations;
- plugin discovery, compatibility and activation boundaries;
- logical optimizer equivalence;
- performance regression budgets;
- security and threat-model contracts;
- public API freeze;
- backwards compatibility and the V1 error-code catalogue;
- wheel and source-distribution build/install in clean environments;
- optional-dependency isolation.

## Controlled pre-RC compatibility amendment

LOT-27 found one release blocker in the LOT-26 plugin default:

```text
PluginCompatibility()
framework range: >=0.5.0,<1.0.0
```

That default would reject PyTransformKit `1.0.0`. Before RC freeze, the V1 host
range was deliberately corrected to:

```text
>=0.5.0,<2.0.0
plugin protocol == 1
```

Only the public-signature category changed. The amendment is recorded in the API
snapshot, consumer compatibility snapshot, changelog and compatibility guide.

## Migration

Pre-V1 consumers should migrate away from root compatibility names such as
`Pipeline`, `RunPipelineService`, `ExecutionContext` and `WriteMode`.
Those names remain migration aids and emit `DeprecationWarning`; they are not
canonical V1 exports.

See `docs/MIGRATION_TO_V1.md` for the complete migration path.

## Security posture

PyTransformKit is an in-process transformation framework, not a sandbox.
Deserialization is fail-closed, plugin activation is explicit, credentials are
not embedded in portable resource contracts, core import does not activate
optional engines, and local resource access is root-confined by the reference
filesystem resolver.

See `docs/SECURITY_AND_THREAT_MODEL.md`.

## Engine stability

| Engine | V1 status |
| --- | --- |
| Pandas | STABLE |
| Polars | STABLE |
| PyArrow | PROVISIONAL |
| DuckDB | PROVISIONAL |

PROVISIONAL engines remain supported only for their published qualified subsets.
Unsupported semantics must fail explicitly; no hidden fallback is permitted.

## RC policy

After `1.0.0rc1`:

- no new feature is accepted into the V1 release line;
- no architecture change is accepted;
- no compatibility baseline is changed except to fix a blocker;
- any blocker fix must rerun the complete release qualification matrix;
- non-blocking improvements are deferred until after `1.0.0`.

The next roadmap step after successful RC validation is LOT-28 —
PyTransformKit `1.0.0` stable.
