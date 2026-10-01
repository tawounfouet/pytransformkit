# PyTransformKit V1 Release Candidate Qualification

> Lot: LOT-27  
> Qualification line: `0.9.0`  
> Release-candidate target: `1.0.0rc1`

LOT-27 is a qualification phase, not a feature phase. Its purpose is to prove that
the V1 contract frozen in LOT-26 can be built, installed, exercised and released
without architecture changes.

## Machine-readable qualification manifest

The normative release qualification manifest is:

```text
contracts/release_qualification_v1.json
```

It is validated by:

```text
python scripts/release_qualification.py \
  --check contracts/release_qualification_v1.json
```

The manifest pins:

- the qualification package version and the `1.0.0rc1` target;
- Python 3.11 through 3.14;
- the complete optional-extra name set;
- official engine IDs and their STABLE / PROVISIONAL partition;
- mandatory CI jobs;
- required release-evidence documents and benchmark contracts;
- the LOT-26 public API category hashes;
- wheel and sdist requirements;
- clean-install and optional-dependency-isolation requirements;
- the blocker-only policy that applies after `1.0.0rc1`.

## Release qualification gate

The dedicated `release-qualification-contract` job must:

1. validate the machine-readable manifest;
2. build both wheel and source distribution;
3. install the wheel into an isolated environment;
4. prove the core wheel does not require Pandas, Polars, PyArrow or DuckDB;
5. run `pip check` and import/version smoke checks;
6. install the source distribution into a second isolated environment;
7. run the same package version smoke check.

This gate complements, rather than replaces, the existing engine, serialization,
plugin, security, API-freeze, conformance and performance jobs.

## RC policy

The qualification sequence is:

```text
0.8.0
  ↓
0.9.0 qualification line
  ↓
full release evidence green
  ↓
1.0.0rc1
  ↓
blocker fixes only
  ↓
LOT-28 / 1.0.0
```

After `1.0.0rc1`, new features and architecture changes are forbidden. Any change
that would alter the frozen V1 API, wire contracts, plugin contracts or public
semantics must be deferred beyond 1.0 unless it is required to resolve a release
blocker and the compatibility impact is explicitly qualified.

## Exit criteria for LOT-27

LOT-27 is complete only when the full Python matrix, engine contracts, portable
serialization, plugin compatibility, artifact installation, optional dependency
isolation, API snapshot, error catalogue, security review, performance budgets and
documentation checks are green from release artifacts, and the resulting
`1.0.0rc1` is published for blocker-only validation.
