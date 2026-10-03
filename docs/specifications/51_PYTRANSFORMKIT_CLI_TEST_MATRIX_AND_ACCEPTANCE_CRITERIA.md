# PyTransformKit — CLI Test Matrix and Acceptance Criteria

## 1. Objet

Ce document transforme les spécifications CLI en preuves exécutables.

```text
No CLI capability is considered supported
until its contract is covered by tests.
```

## 2. Niveaux

```text
UNIT
CONTRACT
INTEGRATION
SECURITY
ARTIFACT
COMPATIBILITY
PLATFORM
RELEASE
POST-PUBLISH
```

## 3. Matrice Python

Obligatoire :

```text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

## 4. Matrice plateformes

Cibles :

```text
Linux
macOS
Windows
```

Les assertions doivent porter sur les contrats publics et non sur les messages OSError natifs exacts.

## 5. Matrice d'installation

| Installation | Attendu |
|---|---|
| `pytransformkit` | core fonctionne |
| `pytransformkit[cli]` | CLI fonctionne |
| `pytransformkit[yaml]` | Declarative Schema fonctionne |
| `pytransformkit[cli,yaml]` | CLI Schema complète |
| core sans Typer/Rich | import core vert |
| CLI sans PyYAML | non-YAML vert, YAML exit 11 |
| CLI sans engines | doctor/engines robustes |

## 6. Root/help

Doivent être testés :

```text
ptk
ptk --help
ptk version --help
ptk doctor --help
ptk schema --help
ptk schema validate --help
ptk schema inspect --help
ptk schema format --help
ptk schema convert --help
ptk engines --help
ptk engines list --help
ptk engines inspect --help
ptk contract --help
ptk contract inspect --help
```

Le help ne nécessite ni PyYAML, ni moteur lourd, ni réseau, ni activation plugin.

## 7. version

Tests :

- human output ;
- JSON output ;
- package version consistency ;
- Python version ;
- no heavy engine import ;
- no network ;
- exit 0.

## 8. doctor

Tests :

- toutes dépendances présentes ;
- dépendances optionnelles absentes ;
- check individuel en erreur ;
- JSON ;
- quiet/verbose/debug ;
- no env dump ;
- no network ;
- no plugin activation ;
- ordre déterministe.

Une dépendance optionnelle absente ne rend pas automatiquement la commande fatale.

## 9. schema validate

Tests :

- valid schema ;
- invalid type ;
- invalid YAML ;
- missing PyYAML ;
- missing file ;
- directory ;
- remote URI ;
- unsafe constructor ;
- alias amplification ;
- env literal ;
- JSON success/error.

Mappings critiques :

```text
PTK-DECL-010 → missing_optional_dependency → 11
other PTK-DECL-* → invalid_schema → 10
```

## 10. schema inspect

Tests :

- basic ;
- nested types ;
- field ordering ;
- null descriptions ;
- human table ;
- JSON report ;
- distinction claire avec SchemaCodec.

## 11. schema format

Tests :

```text
canonical stdout
input unchanged by default
idempotence
semantic round-trip
--write success
atomic failure
no partial file
symlink rejection
Ctrl+C before commit
temp cleanup
already canonical no-op acceptable
```

Invariants :

```text
format(format(x)) == format(x)
load(original) == load(formatted)
```

## 12. schema convert

Tests :

```text
YAML → JSON
JSON → YAML
round-trip semantic equality
extension inference
--from override
unknown extension
missing name
stdout payload
--output
destination exists without force
force overwrite
force without output
input == output
missing parent
symlink output
```

SchemaCodec doit garder :

```text
contract = pytransformkit.schema
contract_version = 1
```

## 13. engines

`engines list/inspect` doit tester :

```text
known installed
known absent
unknown
deterministic order
JSON
no blanket imports
no plugin activation
capabilities from conformance authority
```

## 14. contract inspect

Doit fonctionner depuis un wheel installé sans checkout Git.

Tests :

```text
list contracts
known contract
unknown contract
JSON
read-only
offline
```

## 15. Exit code matrix

| Situation | Exit |
|---|---:|
| success | 0 |
| general error | 1 |
| invalid usage | 2 |
| invalid schema | 10 |
| missing optional dependency | 11 |
| filesystem error | 12 |
| unsupported operation | 13 |
| internal error | 70 |
| interrupted | 130 |
| broken pipe | 141 |

Le runtime enum devra correspondre exactement au snapshot contractuel.

## 16. Error preservation

Tout `PTK-*` existant conserve son code.

Human error :

```text
stdout empty
stderr error
no traceback by default
```

JSON error :

```text
valid JSON on stdout
ok=false
correct command/category/code
stderr normally empty
```

`--debug` peut ajouter une traceback sur stderr sans modifier category/code/exit.

## 17. Rendering tests

Couvrir :

```text
human
JSON
payload
--no-color
quiet
verbose
debug
TTY
non-TTY
Unicode
ANSI absence
markup injection
stream separation
deterministic ordering
```

## 18. Security matrix

Obligatoire :

```text
unsafe YAML rejected
implicit include rejected
env expansion absent
URL retrieval absent
plugin activation absent
arbitrary import absent
silent overwrite absent
mutable symlink write absent
network dependency absent
secret redaction
no shell execution
```

## 19. Filesystem matrix

Obligatoire :

```text
regular file read
directory rejected
missing file
permission denied
output exists
force overwrite
write symlink rejected
missing parent
input == output
atomic replace failure
temporary cleanup
KeyboardInterrupt before commit
```

Fault injection doit vérifier les étapes avant/durant le replace.

## 20. Artifact qualification

Construire :

```bash
python -m build
python -m twine check dist/*
```

Puis qualifier wheel et sdist dans des environnements propres :

1. core only ;
2. `[cli]` ;
3. `[cli,yaml]` ;
4. `[cli]` sans yaml.

Le vrai console script `ptk` doit être exécuté en subprocess.

## 21. Architecture tests

Protéger :

```text
domain !→ cli
schema_io !→ cli
serialization !→ cli
engines !→ cli
domain !→ typer/rich
JSON renderer !→ rich
CLI services use public APIs
```

## 22. Quality gates

Selon la configuration du repo :

```bash
ruff check .
ruff format --check .
mypy src/pytransformkit
pytest
```

Aucune exception de qualité spécifique à la CLI.

## 23. Contract freeze

Le futur `contracts/cli_contract_v1.json` doit couvrir :

```text
program name
commands/subcommands
command IDs
arguments/options
report/payload classification
exit codes
error categories
JSON envelope
reserved commands
filesystem/security guarantees
```

Un verifier CI compare la surface runtime au snapshot.

## 24. Compatibility

Les contrats historiques restent gates de release :

```text
public_api_v1.json
public_api_v1_1.json
error_codes_v1.json
error_codes_v1_1.json
SchemaCodec v1
Declarative Schema 1.1
stable release manifests
```

## 25. CI jobs cibles

```text
quality
python-matrix
cli-contract
cli-command-matrix
cli-security
cli-core-without-extra
cli-with-cli-extra
cli-with-yaml
cli-artifact-wheel
cli-artifact-sdist
cli-platform-smoke
backward-compatibility
```

## 26. Release phase gates

### Alpha

LOT courant + regression + quality green.

### Beta

Toutes commandes target présentes, JSON/exit/security convergés, artifact smoke en place.

### Contract freeze

Command tree, options, JSON envelope, exit codes, error categories et filesystem policy figés.

### RC

Full Python matrix, contract, security, wheel/sdist, compatibility et docs green.

### Stable

Commit exact qualifié, tag exact, artefacts, publication PyPI et consumer smoke public.

## 27. Stable blockers

Bloquants :

```text
contract drift
wrong exit code
invalid JSON
payload pollution
silent overwrite
security regression
core requiring Typer/Rich
Python matrix failure
wheel/sdist broken
1.0/1.1 regression
```

## 28. Evidence policy

Ne sont pas des preuves suffisantes :

```text
assumption
manual-only observation
agent claim
local-only success
skipped mandatory gate
partial CI
```

Une capacité supportée exige un test automatisé, CI ou artifact/consumer smoke selon le niveau.

## 29. Stable checklist

```text
[ ] version 1.2.0
[ ] cli contract v1
[ ] command tree frozen
[ ] JSON contract frozen
[ ] exit codes frozen
[ ] security/filesystem green
[ ] Python 3.11–3.14 green
[ ] Linux/macOS/Windows smoke
[ ] wheel/sdist green
[ ] historical compatibility green
[ ] docs complete
[ ] exact tag/release
[ ] PyPI publish
[ ] public consumer smoke
```

Principe final :

```text
Test what users call.
Test what machines parse.
Test what attackers may abuse.
Test what packages actually ship.
```
