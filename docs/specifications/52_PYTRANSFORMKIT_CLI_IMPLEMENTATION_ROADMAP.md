# PyTransformKit — CLI Implementation Roadmap

## 1. Objectif

Roadmap officielle de la Developer CLI PyTransformKit 1.2, basée sur les spécifications 43–51.

Baseline :

```text
PyTransformKit 1.1.0 stable
```

Cible :

```text
PyTransformKit 1.2.0
Developer CLI
ptk
```

## 2. Principes

Chaque LOT :

1. porte une responsabilité principale ;
2. ajoute ses tests ;
3. ne déclare aucun support sans preuve ;
4. préserve les contrats historiques ;
5. utilise les APIs publiques ;
6. garde le core indépendant de Typer/Rich ;
7. qualifie le checkpoint avant merge.

## 3. Phases

```text
PHASE A — Foundations & Core Commands
1.2.0a*

PHASE B — Feature Completion & Contract Convergence
1.2.0b*

PHASE C — Release Candidate Qualification
1.2.0rc*

PHASE D — Stable Release
1.2.0
```

## 4. Version map

| LOT | Capability | Version |
|---|---|---|
| 44 | CLI Package Bootstrap | 1.2.0a1 |
| 45 | Context / Errors / Rendering | 1.2.0a2 |
| 46 | `ptk version` | 1.2.0a3 |
| 47 | `ptk doctor` | 1.2.0a4 |
| 48 | `schema validate` | 1.2.0a5 |
| 49 | `schema inspect` | 1.2.0a6 |
| 50 | `schema format` | 1.2.0a7 |
| 51 | `schema convert` | 1.2.0a8 |
| 52 | `engines list/inspect` | 1.2.0b1 |
| 53 | `contract inspect` | 1.2.0b2 |
| 54 | Machine Output Hardening | 1.2.0b3 |
| 55 | CLI Contract Freeze | 1.2.0b4 |
| 56 | Security & Filesystem Closure | 1.2.0rc1 |
| 57 | Artifact & Platform Qualification | 1.2.0rc2 |
| 58 | Documentation / RC Closure | 1.2.0rc3 |
| 59 | Stable Release | 1.2.0 |

## 5. LOT-44 — CLI Package Bootstrap → 1.2.0a1

Objectif : faire exister `ptk` sans rendre Typer/Rich obligatoires pour le core.

Livrables :

```text
src/pytransformkit/cli/
├── __init__.py
├── __main__.py
├── bootstrap.py
├── app.py
└── commands/__init__.py
```

`pyproject.toml` :

```text
[cli] → Typer + Rich
[project.scripts]
ptk = pytransformkit.cli.bootstrap:main
```

Tests :

```text
core import without CLI deps
controlled ptk bootstrap without [cli]
ptk --help with [cli]
python -m pytransformkit.cli
console script registration
```

Exit : package CLI présent, core minimal préservé, help vert.

## 6. LOT-45 — Foundations → 1.2.0a2

Introduire :

```text
context
exit codes
CLIErrorReport
exception mapper
human renderer
JSON renderer
stdout/stderr policy
```

Le JSON renderer reste indépendant de Rich.

## 7. LOT-46 — version → 1.2.0a3

```text
ptk version
ptk version --json
ptk --version
```

Doit rester léger et cohérent avec la version package.

## 8. LOT-47 — doctor → 1.2.0a4

Checks locaux des composants/dependencies. Offline, side-effect free, plugin-safe, secret-safe.

## 9. LOT-48 — schema validate → 1.2.0a5

Utilise uniquement `schema_io`. Préserve `PTK-DECL-*`, notamment `PTK-DECL-010 → exit 11`.

## 10. LOT-49 — schema inspect → 1.2.0a6

Vue humaine et JSON du `Schema`, explicitement distincte du SchemaCodec wire.

## 11. LOT-50 — schema format → 1.2.0a7

YAML canonique stdout, puis `--write` sûr/atomique. Prouver idempotence et round-trip.

## 12. LOT-51 — schema convert → 1.2.0a8

```text
YAML ↔ Schema ↔ SchemaCodec JSON
```

Avec `--from`, `--to`, `--name`, `--output`, `--force` et garanties filesystem.

Fin Phase A : version + doctor + tooling Schema complet.

## 13. LOT-52 — Engines → 1.2.0b1

```text
ptk engines list
ptk engines inspect ENGINE
```

Source de vérité : registry/conformance metadata, sans blanket initialization.

## 14. LOT-53 — Contract inspect → 1.2.0b2

```text
ptk contract inspect
ptk contract inspect <id>
```

Doit fonctionner depuis wheel installé.

## 15. LOT-54 — Machine Output Hardening → 1.2.0b3

Converger :

```text
--json
--quiet
--verbose
--no-color
--debug
stdout/stderr
TTY/non-TTY
Unicode
deterministic ordering
payload purity
```

## 16. LOT-55 — CLI Public Contract Freeze → 1.2.0b4

Créer :

```text
contracts/cli_contract_v1.json
```

Figer :

```text
program/commands
arguments/options
command IDs
report/payload classification
JSON envelope
exit codes
error categories
reserved future commands
security/filesystem guarantees
```

Créer un verifier runtime vs snapshot.

## 17. LOT-56 — Security & Filesystem Closure → 1.2.0rc1

Fermer la matrice du document 50 :

```text
safe YAML
no network
no env expansion
no plugin activation
no shell
no silent overwrite
atomic write
symlink protection
secret redaction
interrupt/cleanup
```

Job CI obligatoire : `cli-security`.

## 18. LOT-57 — Artifact & Platform Qualification → 1.2.0rc2

```bash
python -m build
python -m twine check dist/*
```

Qualifier wheel/sdist en clean env :

```text
core only
[cli]
[cli,yaml]
[cli] without yaml
```

Python 3.11–3.14 et smoke Linux/macOS/Windows. Produire SHA256.

## 19. LOT-58 — Documentation & RC Closure → 1.2.0rc3

Créer/mettre à jour :

```text
docs/CLI_GETTING_STARTED.md
docs/CLI_REFERENCE.md
README.md
CHANGELOG.md
release notes 1.2
```

Tester les exemples et shell completion supportée.

## 20. LOT-59 — Stable Release Closure → 1.2.0

Promotion-only :

```text
version 1.2.0
stable release manifest
full CI
wheel/sdist
hashes
main post-merge CI
tag v1.2.0
GitHub Release
PyPI
consumer smoke public
```

Aucune nouvelle fonctionnalité.

## 21. Stable command surface

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

## 22. Dépendances

```bash
pip install pytransformkit
pip install "pytransformkit[yaml]"
pip install "pytransformkit[cli]"
pip install "pytransformkit[cli,yaml]"
```

## 23. No Project leakage

LOT-44 à LOT-59 ne doivent pas introduire :

```text
ProjectDefinition
ProjectLoader
Profile
Target
ProjectManifest
pytransformkit.yml
ptk project
ptk run
ptk build
ptk compile
ptk plan
workflow scheduling/orchestration
```

## 24. Flow de LOT

```text
inspect baseline
→ branch focused LOT
→ implement
→ add tests
→ targeted qualification
→ full relevant regression
→ version checkpoint
→ requalify
→ PR
→ required CI green
→ merge
→ main verification
```

Aucun green artificiel : skipped mandatory gate, partial CI ou simple déclaration d'agent ne suffisent pas.

## 25. Roadmap visuelle

```text
1.1.0
  ↓
LOT-44  1.2.0a1  Bootstrap
  ↓
LOT-45  1.2.0a2  Foundations
  ↓
LOT-46  1.2.0a3  Version
  ↓
LOT-47  1.2.0a4  Doctor
  ↓
LOT-48  1.2.0a5  Validate
  ↓
LOT-49  1.2.0a6  Inspect
  ↓
LOT-50  1.2.0a7  Format
  ↓
LOT-51  1.2.0a8  Convert
  ↓
LOT-52  1.2.0b1  Engines
  ↓
LOT-53  1.2.0b2  Contracts
  ↓
LOT-54  1.2.0b3  Output hardening
  ↓
LOT-55  1.2.0b4  Contract freeze
  ↓
LOT-56  1.2.0rc1 Security
  ↓
LOT-57  1.2.0rc2 Artifacts
  ↓
LOT-58  1.2.0rc3 Docs/RC closure
  ↓
LOT-59  1.2.0    Stable
```

Principe final :

```text
Build incrementally.
Freeze deliberately.
Qualify from artifacts.
Publish only proven behavior.
```
