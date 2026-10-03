# CLAUDE.md

# PyTransformKit — Claude Code Instructions

This file contains Claude Code-specific instructions for PyTransformKit.

It is intentionally a thin overlay.

The canonical repository-wide instructions are defined in:

```text
AGENTS.md
```

Claude Code MUST read and follow `AGENTS.md` before making changes.

Authority order:

```text
specifications / contracts / tests
        ↓
AGENTS.md
        ↓
CLAUDE.md
```

## 1. Repository context

```text
Project: PyTransformKit
Package: pytransformkit
Repository: tawounfouet/pytransformkit
Current stable baseline: 1.1.0
Next planned line: 1.2 Developer CLI
Python: 3.11 / 3.12 / 3.13 / 3.14
```

## 2. First action in every coding session

Before editing:

```text
1. Read AGENTS.md.
2. Inspect the current branch and version.
3. Read the relevant specification.
4. Inspect existing implementation.
5. Inspect adjacent tests.
6. Inspect affected contract snapshots.
7. Only then plan and edit.
```

Do not assume current repository state from prior conversations, stale notes, or an older branch.

The live repository is the source of truth.

## 3. Preserve architecture

Keep the dependency direction defined in `AGENTS.md`.

Never introduce a dependency from Domain/core toward:

```text
engines
CLI
Typer
Rich
physical I/O
```

Use public APIs before internals.

If the public surface is insufficient, identify the architectural gap explicitly rather than bypassing it silently.

## 4. Do not rewrite historical contracts

Files under `contracts/` are evidence.

Do not change historical snapshots merely because an implementation breaks them.

A compatibility failure should first trigger an implementation review.

Intentional public evolution uses successor contracts according to the relevant specification.

## 5. Tests are part of implementation

Preferred cycle:

```text
inspect
→ implement a small coherent change
→ add/update tests
→ run targeted tests
→ fix
→ run broader regression
```

Do not postpone all verification to the end.

## 6. Quality commands

Normal Python changes:

```bash
ruff check .
ruff format --check .
mypy src/pytransformkit
pytest
```

If formatting is required:

```bash
ruff format .
```

Packaging/release-sensitive changes:

```bash
python -m build
python -m twine check dist/*
```

Do not report a command as green unless it was actually executed successfully.

## 7. LOT workflow

PyTransformKit uses focused implementation LOTs.

```text
read spec
→ limit scope
→ implement
→ test
→ qualify
→ apply planned version checkpoint
→ requalify
→ PR
→ required CI
→ merge
→ verify main when required
```

Avoid unrelated refactors.

## 8. Current CLI roadmap

```text
LOT-44  CLI bootstrap                  → 1.2.0a1
LOT-45  CLI foundations                → 1.2.0a2
LOT-46  ptk version                    → 1.2.0a3
LOT-47  ptk doctor                     → 1.2.0a4
LOT-48  schema validate                → 1.2.0a5
LOT-49  schema inspect                 → 1.2.0a6
LOT-50  schema format                  → 1.2.0a7
LOT-51  schema convert                 → 1.2.0a8
LOT-52  engines                        → 1.2.0b1
LOT-53  contract inspect               → 1.2.0b2
LOT-54  machine output hardening       → 1.2.0b3
LOT-55  CLI contract freeze            → 1.2.0b4
LOT-56  security/filesystem closure    → 1.2.0rc1
LOT-57  artifact qualification         → 1.2.0rc2
LOT-58  docs/RC closure                → 1.2.0rc3
LOT-59  stable release                 → 1.2.0
```

Do not skip foundations.

## 9. CLI rule

For 1.2:

```text
Typer = routing
Rich = human rendering
CLI services = coordination
public PyTransformKit APIs = semantic authority
```

Typer handlers should parse input, build context, call a service, render, and map the process outcome.

They must not implement Schema, engine, or wire semantics.

## 10. CLI scope

Canonical target:

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

Do NOT add during 1.2:

```text
ptk project
ptk run
ptk build
ptk compile
ptk plan
pytransformkit.yml
ProjectDefinition
Profile
Target
```

unless the roadmap is explicitly changed.

## 11. Reports vs payloads

Reports:

```text
version
doctor
schema.validate
schema.inspect
engines.list
engines.inspect
contract.inspect
```

Payloads:

```text
schema.format
schema.convert
```

Rule:

```text
Reports are rendered.
Payloads are emitted.
```

Do not wrap SchemaCodec JSON in a CLI report envelope.

Do not decorate canonical YAML with Rich.

## 12. Schema authority

```text
Declarative YAML
      ↓
schema_io
      ↓
Schema
      ↓
SchemaCodec JSON
```

Do not create a CLI-specific schema model.

## 13. Optional dependencies

Core must remain usable without:

```text
PyYAML
Typer
Rich
Pandas
Polars
PyArrow
DuckDB
```

Avoid convenience imports that accidentally make optional dependencies mandatory.

## 14. Security

Fail closed.

Do not introduce:

```text
unsafe YAML
eval/exec
untrusted pickle
implicit URL retrieval
implicit includes
environment expansion in schema data
automatic plugin activation
shell=True
automatic dependency installation
silent overwrite
```

## 15. Filesystem

CLI rule:

```text
read explicit paths
write explicit paths
```

For replacement writes prefer:

```text
validate
→ complete payload
→ temporary sibling
→ flush / close
→ atomic replace
```

Do not silently follow mutable output symlinks or create parent directories unless the spec explicitly allows it.

## 16. Error identity

Framework error codes and process exit codes are separate contracts.

```text
PTK-DECL-005
    ≠
exit 10
```

Preserve the PTK code while mapping the process outcome.

## 17. Determinism

Avoid public behavior based on unordered sets, random IDs, timestamps, hostnames, memory addresses, or filesystem discovery order unless specified.

## 18. No speculative support

Do not mark an engine capability supported merely because an underlying library appears able to do it.

Conformance evidence is required.

No hidden engine fallback.

## 19. Editing discipline

Before replacing an existing file:

```text
read it
understand adjacent patterns
preserve unrelated content
```

Prefer focused patches over broad rewrites.

For large changes, work incrementally and inspect diffs frequently.

## 20. Git/PR discipline

Use focused commit messages such as:

```text
feat(cli): bootstrap ptk entrypoint
feat(cli): add doctor command
test(cli): qualify machine output contract
fix(cli): preserve PTK error identity
docs(cli): add implementation roadmap
```

PR descriptions should identify:

```text
LOT
version checkpoint
scope
contract impact
tests run
known limitations
```

Do not declare full qualification while required CI is pending, failed, cancelled, or unexpectedly skipped.

## 21. Stable release

Stable closure is promotion-only.

Focus on:

```text
version
contracts
qualification
artifacts
tag
release
publication
consumer smoke
```

Do not add new features in the stable closure LOT.

## 22. Communication

For substantial repository work, give concise checkpoints describing:

```text
what was inspected
what was found
what changed
what remains unverified
```

Do not present assumptions as completed work.

## 23. Unexpected repository state

If the live repository contradicts the expected roadmap:

```text
stop
inspect
reconcile
```

Examples:

```text
version already advanced
LOT already merged
contract already exists
architecture changed
tests reveal different behavior
```

The live repository wins.

## 24. Never invent evidence

If a branch, PR, CI result, artifact, tag, hash, or release status cannot be verified, state that it is unverified.

Never fabricate it.

## 25. Claude Code working pattern

For a significant change:

```text
search first
read second
edit third
test fourth
```

Do not generate a parallel architecture when the repository already defines one.

## 26. Final Claude rule

```text
Read AGENTS.md.
Read the relevant specification.
Inspect live state.
Preserve contracts.
Keep adapters thin.
Keep dependencies optional.
Fail closed.
Add executable proof.
Do not claim what you did not verify.
```

Shortest summary:

```text
Repository truth over memory.
Public contracts over convenience.
Evidence over assertion.
```
