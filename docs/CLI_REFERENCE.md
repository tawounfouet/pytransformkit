# PyTransformKit CLI — Reference

This document describes the frozen `pytransformkit.cli` contract version 1
for the PyTransformKit 1.2 release line.

## Installation model

| Installation | CLI routing | YAML schema commands |
| --- | --- | --- |
| `pytransformkit` | entrypoint explains missing `[cli]`; exit 11 | unavailable |
| `pytransformkit[cli]` | available | YAML operations fail with `PTK-DECL-010`; exit 11 |
| `pytransformkit[yaml]` | CLI dependencies absent | authoring API available in Python |
| `pytransformkit[cli,yaml]` | available | fully available |

Console entrypoint:

```text
ptk = pytransformkit.cli.bootstrap:main
```

## Frozen command tree

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

Stable command IDs:

```text
version
doctor
schema.validate
schema.inspect
schema.format
schema.convert
engines.list
engines.inspect
contract.inspect
```

## Root

`ptk` without a command prints help and exits `0`.

| Option | Meaning |
| --- | --- |
| `--version` | print installed PyTransformKit and Python versions |

Shell-completion installer options are not part of CLI contract v1. The root help does not expose `--install-completion` or `--show-completion`.

## Report commands

Report commands can emit human output or the stable JSON envelope.

### `ptk version`

```text
ptk version [--json] [--no-color]
```

Reports the installed PyTransformKit and Python versions.

### `ptk doctor`

```text
ptk doctor [--json] [--quiet] [--verbose] [--debug] [--no-color]
```

Performs local diagnostics for PyTransformKit, Python, CLI dependencies,
PyYAML and optional execution-engine packages. Missing optional engines do not
make the command fatal.

### `ptk schema validate PATH`

```text
ptk schema validate PATH [--json] [--quiet] [--verbose] [--debug] [--no-color]
```

Loads one explicit local declarative schema and validates it through the public
`schema_io` authority.

### `ptk schema inspect PATH`

```text
ptk schema inspect PATH [--json] [--quiet] [--verbose] [--debug] [--no-color]
```

Reports schema name, ordered fields, nullability, descriptions and semantic
details for complex types.

### `ptk engines list`

```text
ptk engines list [--json] [--quiet] [--verbose] [--debug] [--no-color]
```

Lists official engine metadata without importing or activating engine plugins.

### `ptk engines inspect ENGINE_ID`

```text
ptk engines inspect ENGINE_ID [--json] [--quiet] [--verbose] [--debug] [--no-color]
```

Inspects one official engine ID. Unknown IDs are invalid usage and exit `2`.

### `ptk contract inspect [CONTRACT_ID]`

```text
ptk contract inspect [CONTRACT_ID] [--json] [--quiet] [--verbose] [--debug] [--no-color]
```

Without an ID, lists inspectable contracts. Stable IDs are:

```text
public-api
errors
schema-wire
cli
```

The `cli` document is the packaged `pytransformkit.cli` contract version 1.

## Payload commands

Payload commands do not use the report JSON envelope. They emit canonical
content directly or write to an explicit file.

### `ptk schema format PATH`

```text
ptk schema format PATH [--write] [--debug] [--no-color]
```

Without `--write`, emits canonical declarative YAML to stdout. With
`--write`, replaces the explicit regular file atomically.

Mutable symlink targets are rejected.

### `ptk schema convert INPUT_PATH --to FORMAT`

```text
ptk schema convert INPUT_PATH --to FORMAT
    [--from FORMAT]
    [--name NAME]
    [--output PATH]
    [--force]
    [--debug]
    [--no-color]
```

Supported formats:

```text
yaml
json
```

`--from` overrides format inference. `--name` supplies the authoring name
when YAML output needs one. `--output` selects an explicit destination.
Existing destinations require `--force`.

## Output modes

The stable report envelope uses:

```json
{
  "contract_version": 1,
  "ok": true,
  "command": "command.id",
  "data": {}
}
```

Errors use:

```json
{
  "contract_version": 1,
  "ok": false,
  "command": "command.id",
  "error": {
    "category": "invalid_usage",
    "message": "..."
  }
}
```

JSON is deterministic, UTF-8, ANSI-free, terminal-width independent and written
on stdout. Human errors are written to stderr. Debug tracebacks are redacted
before crossing stderr.

## Option compatibility

The following combinations are invalid:

```text
--quiet --verbose
--quiet --debug
--json --verbose
```

`--json --quiet`, `--json --debug` and `--json --no-color` remain valid
where those options exist and do not change the successful machine payload.

## Exit-code contract

| Symbol | Code |
| --- | ---: |
| `SUCCESS` | 0 |
| `GENERAL_ERROR` | 1 |
| `INVALID_USAGE` | 2 |
| `INVALID_SCHEMA` | 10 |
| `MISSING_OPTIONAL_DEPENDENCY` | 11 |
| `FILESYSTEM_ERROR` | 12 |
| `UNSUPPORTED_OPERATION` | 13 |
| `INTERNAL_ERROR` | 70 |
| `INTERRUPTED` | 130 |
| `BROKEN_PIPE` | 141 |

## Filesystem and security guarantees

CLI v1 is fail-closed:

- local explicit paths only;
- no URL retrieval;
- no recursive directory discovery;
- no environment expansion;
- no implicit include/import;
- safe YAML parsing;
- no plugin activation;
- no shell execution;
- no implicit overwrite;
- mutable symlink writes rejected;
- atomic replacement for authorized writes;
- temporary cleanup on failure/interruption;
- interruption before commit preserves the destination;
- diagnostic and debug secret redaction.

## Platform support

The 1.2 artifacts are qualified on:

```text
Python 3.11, 3.12, 3.13, 3.14
Linux, macOS, Windows
```

Wheel and sdist are both qualified in clean environments with:

```text
core only
[cli]
[cli,yaml]
[cli] without PyYAML
```

## Frozen authority

The machine-readable CLI contract is:

```text
contracts/cli_contract_v1.json
```

Installed artifacts package the same document under
`pytransformkit._contract_data`. Runtime drift is checked by
`scripts/cli_contract_snapshot.py`.
