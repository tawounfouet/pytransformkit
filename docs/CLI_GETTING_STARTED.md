# PyTransformKit CLI — Getting Started

PyTransformKit 1.2 adds the optional `ptk` developer CLI without changing the
zero-runtime-dependency core package.

## Installation

Install only the capabilities you need:

```bash
pip install pytransformkit
pip install "pytransformkit[cli]"
pip install "pytransformkit[yaml]"
pip install "pytransformkit[cli,yaml]"
```

The CLI dependencies are optional. A core-only installation still installs the
`ptk` console entrypoint, but invoking it exits with code `11` and explains
how to install the `cli` extra.

Declarative YAML commands require the `yaml` extra. With `[cli]` but without
PyYAML, YAML-backed schema operations fail explicitly with `PTK-DECL-010`
and exit code `11`.

## First commands

Check the installed package and Python versions:

```bash
ptk version
ptk version --json
ptk --version
```

Inspect the local environment:

```bash
ptk doctor
ptk doctor --json
```

List the official execution engines and inspect one engine:

```bash
ptk engines list
ptk engines list --json
ptk engines inspect pandas
ptk engines inspect pandas --json
```

These commands are local and read-only. They do not activate plugins, execute
transformations, discover projects, or access the network.

## Validate and inspect a declarative Schema

Create `customers.yml`:

```yaml
version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
    - name: email
      type: string
      nullable: true
```

Validate it:

```bash
ptk schema validate customers.yml
ptk schema validate customers.yml --json
```

Inspect its logical fields:

```bash
ptk schema inspect customers.yml
ptk schema inspect customers.yml --json
```

The CLI reads exactly the file you name. Directories, remote URLs and recursive
discovery are not supported.

## Canonically format YAML

Preview canonical YAML on stdout:

```bash
ptk schema format customers.yml
```

Rewrite the explicit file atomically:

```bash
ptk schema format customers.yml --write
```

The `--write` flag is required for in-place modification. A failed or
interrupted replacement preserves the original destination and cleans temporary
siblings.

## Convert between authoring YAML and wire JSON

Convert YAML to the stable `SchemaCodec` JSON wire representation:

```bash
ptk schema convert customers.yml --to json --output customers.json
```

Convert wire JSON back to declarative YAML:

```bash
ptk schema convert customers.json --to yaml --name customers --output restored.yml
```

Existing output paths are rejected unless `--force` is supplied explicitly:

```bash
ptk schema convert customers.yml --to json --output customers.json --force
```

Payload commands write only the canonical payload to stdout when no output file
is requested.

## Inspect frozen contracts

List inspectable contracts:

```bash
ptk contract inspect
ptk contract inspect --json
```

Inspect the frozen CLI v1 contract:

```bash
ptk contract inspect cli
ptk contract inspect cli --json
```

The installed wheel packages the frozen contract snapshot. Contract inspection
works outside a source checkout.

## Machine-readable output

Report commands support the stable CLI v1 JSON envelope:

```json
{
  "command": "version",
  "contract_version": 1,
  "data": {
    "pytransformkit": "1.2.0",
    "python": "3.x.y"
  },
  "ok": true
}
```

The version values vary with the installed environment; the envelope does not.

For report commands:

- `--json` emits machine-readable output on stdout;
- `--quiet` reduces successful human output where supported;
- `--verbose` enriches human output;
- `--debug` adds internal diagnostics only on stderr when necessary;
- `--no-color` disables ANSI color;
- `NO_COLOR` is honored.

`--json --verbose`, `--quiet --verbose` and `--quiet --debug` are invalid
combinations and exit with code `2`.

## Exit codes

The stable process contract is:

| Code | Meaning |
| ---: | --- |
| 0 | success |
| 1 | general error |
| 2 | invalid usage |
| 10 | invalid schema |
| 11 | missing optional dependency |
| 12 | filesystem error |
| 13 | unsupported operation |
| 70 | internal error |
| 130 | interrupted |
| 141 | broken pipe |

Framework `PTK-*` error identities remain separate from process exit codes.

## Shell completion

PyTransformKit 1.2 intentionally does **not** publish shell-completion installer
options. The frozen CLI v1 contract does not include
`--install-completion` or `--show-completion`, and the Typer application is
configured with completion disabled.

This avoids adding new root options after the LOT-55 contract freeze. Shell
completion may be introduced in a future CLI contract version.

## What the 1.2 CLI does not own

The 1.2 command tree deliberately excludes project/workflow orchestration:

```text
ptk project
ptk run
ptk compile
ptk plan
ptk build
ptk test
```

These names are reserved for future contract versions. The CLI performs no
implicit project discovery.

## Further reference

See `docs/CLI_REFERENCE.md` for the complete command and option reference.
