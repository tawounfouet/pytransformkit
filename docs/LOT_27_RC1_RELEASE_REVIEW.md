# LOT-27 — 1.0.0rc1 Release Review

> Release candidate: `1.0.0rc1`  
> Baseline entering LOT-27: `0.8.0`  
> Qualification line: `0.9.0`

This review records the release decision evidence required by the frozen roadmap.
It does not add product capability.

## Review result

No architecture change is required for the release candidate.

The only pre-RC contract amendment discovered during LOT-27 is the documented
PluginCompatibility default host-range correction from `<1.0.0` to `<2.0.0`.
That amendment is compatibility-enabling for the V1 stable line and is protected
by the updated public API and consumer snapshots.

## Exit-criteria evidence

| LOT-27 criterion | Evidence |
| --- | --- |
| Full Python matrix | CI tests on Python 3.11–3.14 |
| Engine contract matrix | Pandas, Polars, PyArrow, DuckDB and cross-engine jobs |
| Serialization compatibility | `serialization-contract` and frozen wire versions |
| Plugin compatibility | `plugin-contract` plus V1 host/protocol snapshot |
| Built artifacts | wheel + sdist built by release qualification |
| Clean environments | isolated wheel and sdist installation |
| Optional isolation | core wheel verified without engine packages |
| Backwards compatibility | `consumer_compatibility_v1.json` |
| Error codes | `error_codes_v1.json` with 53 public exception contracts |
| Security review | `SECURITY_AND_THREAT_MODEL.md` plus security gate |
| Performance review | LOT-25 budgets re-executed in CI |
| Documentation review | Getting Started, engine matrix, API freeze and migration docs |
| Release notes | `RELEASE_NOTES_1_0_0rc1.md` |
| Migration notes | `MIGRATION_TO_V1.md` |

## Mandatory V1 capability status

Pandas and Polars remain the mandatory STABLE execution profiles for V1. PyArrow
and DuckDB remain PROVISIONAL and therefore do not expand the mandatory semantic
denominator.

This is deliberate: RC qualification freezes only semantics already backed by
conformance evidence.

## Compatibility freeze

The RC must preserve:

```text
public API snapshot
+ error-code catalogue
+ wire contract versions
+ plugin protocol V1
+ optional-extra names
+ official engine IDs
+ legacy migration warning behavior
```

A failing compatibility gate is a release blocker.

## Security review

The threat model was re-read against the release-candidate boundaries. The RC
introduces no new trust boundary: it adds release evidence only.

Security-sensitive invariants remain:

- no executable pickle-style portable deserialization;
- no payload-controlled Python imports;
- no plugin auto-activation;
- no raw credential value in portable resource contracts;
- no implicit engine fallback;
- no optional engine import from core import;
- bounded serialized payload parsing;
- explicit local resource root confinement.

## Performance review

LOT-27 does not change transformation execution algorithms. The existing LOT-25
performance budgets remain the regression gate and must pass on the promotion
head.

## Documentation review

The canonical documentation set for the RC is:

```text
README.md
docs/GETTING_STARTED.md
docs/PUBLIC_API_V1_FREEZE.md
docs/BACKWARDS_COMPATIBILITY_V1.md
docs/MIGRATION_TO_V1.md
docs/ENGINE_CONFORMANCE_MATRIX.md
docs/RUNTIME_AND_ENGINE_SAFETY.md
docs/SECURITY_AND_THREAT_MODEL.md
docs/RELEASE_CANDIDATE_QUALIFICATION.md
docs/RELEASE_NOTES_1_0_0rc1.md
```

## Post-RC rule

Once the `1.0.0rc1` promotion head passes the complete matrix, the branch enters
blocker-only mode. Feature work and architecture changes are deferred beyond the
V1 stable release.
