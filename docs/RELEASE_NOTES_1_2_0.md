# PyTransformKit 1.2.0 Release Notes

PyTransformKit 1.2 introduces the optional Developer CLI while preserving the
stable 1.0/1.1 Python, wire, error and Declarative Schema contracts.

These notes are prepared during the 1.2 release-candidate closure. The stable
`1.2.0` release is completed only by LOT-59 after the exact stable commit,
artifacts, tag, GitHub Release, PyPI publication and public consumer smoke are
qualified.

## Developer CLI

Install the CLI independently from the zero-runtime-dependency core:

```bash
pip install "pytransformkit[cli]"
pip install "pytransformkit[cli,yaml]"
```

The stable command tree is:

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

## Declarative Schema operations

The CLI exposes the existing 1.1 Declarative Schema authority rather than
creating a second schema model.

Users can:

- validate one explicit local YAML schema;
- inspect its logical fields;
- emit canonical YAML;
- atomically rewrite the explicit source with `--write`;
- convert between declarative YAML and the stable `SchemaCodec` JSON wire
  contract.

PyYAML remains optional.

## Machine-readable contract

Report commands expose CLI contract version 1 with deterministic JSON success
and error envelopes.

The frozen machine-readable contract is:

```text
contracts/cli_contract_v1.json
```

It freezes:

- program and entrypoint;
- command tree and command IDs;
- arguments and options;
- report/payload classification;
- exit codes and error categories;
- JSON envelope;
- stdout/stderr rules;
- reserved future commands;
- filesystem/security guarantees.

`ptk contract inspect cli --json` exposes the packaged snapshot from an
installed wheel without requiring a repository checkout.

## Process semantics

Stable exit codes are:

```text
0    success
1    general error
2    invalid usage
10   invalid schema
11   missing optional dependency
12   filesystem error
13   unsupported operation
70   internal error
130  interrupted
141  broken pipe
```

Framework `PTK-*` identities remain separate from process exit codes.

## Security and filesystem closure

The qualified CLI boundary is local and fail-closed:

- no network loading;
- no environment interpolation;
- no plugin activation;
- no shell execution;
- no silent overwrite;
- safe YAML;
- mutable symlink protection;
- atomic replacement;
- temporary cleanup;
- destination preservation on interruption before commit;
- secret redaction for normal errors and debug tracebacks.

## Artifact and platform qualification

Both wheel and sdist are validated with `twine check`, SHA-256 evidence and
clean-environment installation smokes.

Qualified modes:

```text
core only
[cli]
[cli,yaml]
[cli] without PyYAML
```

The real installed `ptk` console script is exercised on:

```text
Linux   × Python 3.11 / 3.12 / 3.13 / 3.14
macOS   × Python 3.11 / 3.12 / 3.13 / 3.14
Windows × Python 3.11 / 3.12 / 3.13 / 3.14
```

## Shell completion

Shell-completion installer options are intentionally not part of CLI contract
v1. `--install-completion` and `--show-completion` remain absent in 1.2.

## Compatibility

PyTransformKit 1.2 preserves:

- the frozen V1 public Python API;
- the 1.1 successor public API;
- `SchemaCodec.contract = pytransformkit.schema`;
- `SchemaCodec.contract_version = 1`;
- historical V1 and V1.1 error catalogues;
- the 1.1 Declarative Schema public namespace;
- plugin protocol and engine compatibility gates.

## Documentation

The 1.2 CLI documentation consists of:

- `docs/CLI_GETTING_STARTED.md`;
- `docs/CLI_REFERENCE.md`;
- this release-note file;
- the CLI section in `README.md`;
- the 1.2 entry in `CHANGELOG.md`.

Published examples are executed from an installed wheel during CI.

## Intended stable tag

```text
v1.2.0
```

Tagging, GitHub Release creation and PyPI publication belong to LOT-59 only.
