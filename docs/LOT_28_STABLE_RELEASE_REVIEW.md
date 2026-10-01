# LOT-28 — PyTransformKit 1.0.0 Stable Release Review

> Stable target: `1.0.0`  
> Release-candidate baseline: `1.0.0rc1`  
> RC main commit: `d8dc2799935d1ea1c0ad9e4f184676b508102d5d`

LOT-28 is a promotion and qualification lot. It does not introduce product
capability.

## Promotion decision

The `1.0.0rc1` baseline completed the full CI matrix on `main` without blocker
defects. No architecture redesign was required after RC qualification.

The stable promotion therefore changes release metadata and final release evidence
only. The frozen V1 API, wire contracts, plugin protocol, error catalogue, engine
partition and compatibility snapshots remain unchanged.

## Acceptance criteria

| 1.0 criterion | Stable evidence |
| --- | --- |
| Domain independent from engine packages | architecture and engine contract tests |
| Optional official adapters | core clean-install isolation |
| Typed serializable transformation vocabulary | serialization + API freeze |
| Relational/aggregate/window contracts | engine and cross-engine suites |
| Quality/Lineage/Observability first-class | existing V1 contract suites |
| Deterministic IR round-trip | serialization contract |
| Optimizer semantics preserved | optimizer contract |
| Plugin contracts versioned | plugin contract V1 |
| Published conformance model | `ENGINE_CONFORMANCE_MATRIX.md` |
| Public error codes stable | `error_codes_v1.json` |
| API/deprecation policy documented | V1 freeze + migration docs |
| Clean supported-Python installs | release qualification |
| Mandatory CI green | full LOT-28 promotion matrix |
| No known blocker | stable-release review |
| No post-RC redesign | RC-to-stable freeze evidence |

## RC-to-stable freeze

The stable gate rejects changes to:

```text
public API category hashes
wire contract IDs/versions
error-code catalogue
plugin protocol V1 contract
official engine IDs
stable/provisional engine partition
supported Python matrix
release evidence set
```

## Artifact policy

Wheel and sdist must both build, install and import in clean environments.

The core wheel must remain usable without Pandas, Polars, PyArrow or DuckDB
installed.

Reproducibility is enforced at the contract and package-content level through
frozen metadata and compatibility snapshots. Cryptographic package signing is
outside the current repository CI capability and is not asserted by LOT-28.

## Final publication boundary

After the stable promotion commit passes on `main`, external publication still
requires:

1. create tag `v1.0.0`;
2. create the GitHub release from the stable release notes;
3. publish the built package to the intended package registry;
4. preserve published artifact hashes/signatures when the publication pipeline
   supports them.

Those actions do not change the already qualified source contract.
