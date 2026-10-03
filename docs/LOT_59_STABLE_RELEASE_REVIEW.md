# LOT-59 — PyTransformKit 1.2.0 Stable Release Review

> Stable target: `1.2.0`  
> Qualified release candidate: `1.2.0rc3`  
> Release-candidate main commit: `02028651a242912633b1ad7d17364714be016ce6`

LOT-59 is a promotion-only release closure. No new CLI command, option, schema
semantic, wire contract, error identity, engine capability or project concept is
introduced after the 1.2 RC freeze.

## Stable scope

PyTransformKit 1.2 promotes the optional Developer CLI:

```text
ptk
├── version
├── doctor
├── schema
│   ├── validate
│   ├── inspect
│   ├── format
│   └── convert
├── engines
│   ├── list
│   └── inspect
└── contract
    └── inspect
```

The machine contract remains:

```text
contract         = pytransformkit.cli
contract_version = 1
status           = stable
framework_line   = 1.2.x
```

The stable snapshot is `contracts/cli_contract_v1.json`.

## Preserved baselines

The release keeps the existing stable baselines intact:

- PyTransformKit V1 public API;
- 1.1 Declarative Schema successor API;
- V1 and V1.1 error catalogues;
- `SchemaCodec.contract = pytransformkit.schema`;
- `SchemaCodec.contract_version = 1`;
- plugin protocol V1;
- engine stability partition;
- zero mandatory runtime dependency core.

Typer, Rich and PyYAML remain optional extras.

## Security closure

The stable CLI remains fail-closed:

- no remote schema loading;
- no recursive discovery;
- no environment expansion;
- no implicit include;
- no implicit plugin activation;
- no shell execution;
- no silent overwrite;
- mutable symlink writes rejected;
- authorized replacement writes are atomic;
- temporary siblings are cleaned;
- interruption before commit preserves the destination;
- normal and debug diagnostics redact common credential forms.

## Artifact qualification

The release requires both wheel and source distribution.

Each stable artifact must pass:

- `twine check`;
- SHA-256 recording;
- clean core installation;
- clean `[cli]` installation;
- clean `[cli,yaml]` installation;
- explicit `[cli]` without PyYAML;
- real installed `ptk` invocation.

The CLI is qualified on:

```text
Linux   × Python 3.11 / 3.12 / 3.13 / 3.14
macOS   × Python 3.11 / 3.12 / 3.13 / 3.14
Windows × Python 3.11 / 3.12 / 3.13 / 3.14
```

## Documentation closure

Stable documentation includes:

- `docs/CLI_GETTING_STARTED.md`;
- `docs/CLI_REFERENCE.md`;
- `docs/RELEASE_NOTES_1_2_0.md`;
- `README.md`;
- `CHANGELOG.md`.

Published examples are executed against an installed wheel in CI.

Shell-completion installer options remain intentionally outside CLI contract v1.
Neither `--install-completion` nor `--show-completion` is supported.

## Stable manifest

The machine-readable stable release authority is:

```text
contracts/stable_release_v1_2.json
```

It pins:

- RC3 source commit;
- stable target version;
- predecessor stable manifest;
- required CI jobs and evidence paths;
- CLI contract identity;
- command IDs;
- Python and platform matrix;
- artifact policy;
- publication policy;
- blocker-only release policy.

## Publication sequence

Publication may start only after the exact `1.2.0` commit is fully green on
`main`.

The sequence is:

1. qualify exact `1.2.0` stable commit;
2. verify post-merge `main` CI;
3. create tag `v1.2.0` on that exact commit;
4. build wheel and sdist from the tagged commit;
5. record SHA-256;
6. create the GitHub Release using `docs/RELEASE_NOTES_1_2_0.md`;
7. publish through PyPI Trusted Publishing;
8. install `pytransformkit[cli,yaml]==1.2.0` from public PyPI;
9. run `scripts/public_consumer_smoke.py`.

A tag, GitHub Release or PyPI package pointing at any other commit does not
satisfy LOT-59.

## Stable blocker policy

After promotion begins, the only acceptable changes are release blockers:

- contract drift correction;
- packaging/publication correctness;
- security correction;
- documentation correction required for publication;
- consumer-smoke correction that does not add functionality.

Any new feature belongs to a later release line.
