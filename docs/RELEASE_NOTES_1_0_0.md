# PyTransformKit 1.0.0 Release Notes

PyTransformKit `1.0.0` is the first stable release of the V1 architecture.

It promotes the qualified `1.0.0rc1` contract without adding new features,
changing architecture, or widening the mandatory semantic surface.

## Stable V1 contract

The stable release preserves the RC freeze for:

- canonical `TransformationPlan -> LogicalPlan -> TransformationRuntime` execution;
- public imports, signatures, enums and Protocol members;
- public exception hierarchy and machine-readable `PTK-*` error codes;
- optional-extra names and official engine IDs;
- versioned serialization contract identifiers and wire versions;
- plugin protocol V1 and entry-point group;
- legacy pre-V1 compatibility aliases and their warning behavior.

## Engine status

| Engine | V1 status |
| --- | --- |
| Pandas | STABLE |
| Polars | STABLE |
| PyArrow | PROVISIONAL |
| DuckDB | PROVISIONAL |

The stable release does not promote provisional engine semantics beyond their
published capability matrix.

## Qualification

The full release matrix is rerun for `1.0.0` across Python 3.11–3.14 and covers:

- quality, formatting and static typing;
- engine and cross-engine contracts;
- Customer 360 conformance;
- I/O;
- serialization and migrations;
- plugins;
- optimizer equivalence;
- performance regression budgets;
- security;
- public API freeze;
- backwards compatibility;
- error-code freeze;
- clean wheel and sdist installation;
- optional-dependency isolation;
- stable-release freeze validation.

## Compatibility

The stable compatibility evidence is:

```text
contracts/public_api_v1.json
contracts/error_codes_v1.json
contracts/consumer_compatibility_v1.json
contracts/release_qualification_v1.json
contracts/stable_release_v1.json
```

No public API category hash changes between `1.0.0rc1` and `1.0.0`.

## Migration

Consumers migrating from the pre-V1 API should follow
`docs/MIGRATION_TO_V1.md`.

Legacy root names remain compatibility aids and are intentionally absent from the
canonical root export set.

## Security

The V1 threat model remains unchanged from the RC. PyTransformKit is an in-process
transformation framework, not a sandbox for arbitrary Python or plugin code.

See `docs/SECURITY_AND_THREAT_MODEL.md`.

## Release publication

The repository release commit and package artifacts are qualified before tag/package
publication. The intended stable tag is:

```text
v1.0.0
```

Package signing is not claimed unless the external publication pipeline produces
and verifies signed artifacts.
