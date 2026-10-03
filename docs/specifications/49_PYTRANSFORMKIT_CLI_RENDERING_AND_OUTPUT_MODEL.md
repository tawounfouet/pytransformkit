# PyTransformKit — CLI Rendering and Output Model

## 1. Objet

Ce document définit le modèle de rendu et de sortie de la Developer CLI PyTransformKit 1.2.

Principe :

```text
Rendering presents results.
Rendering does not define semantics.
```

## 2. Deux familles de sorties

### Report Output

```text
version
doctor
schema.validate
schema.inspect
engines.list
engines.inspect
contract.inspect
```

Un report peut être rendu pour un humain ou sérialisé en JSON machine.

### Payload Output

```text
schema.format
schema.convert
```

Les payloads sont directement le YAML canonique de `schema_io` ou le JSON wire de `SchemaCodec`.

```text
Report JSON ≠ SchemaCodec JSON
```

## 3. Architecture

```text
CLI Service
    ↓
CLI Report
    ├── HumanRenderer → Rich
    └── JSONRenderer  → stdlib json
```

Pour les payloads :

```text
Schema → schema_io   → canonical YAML
Schema → SchemaCodec → canonical JSON
```

Le JSONRenderer ne doit pas importer Rich.

## 4. Reports neutres de présentation

Les services construisent des objets simples, typés, déterministes et sérialisables. Les renderers ne doivent pas introspecter arbitrairement les objets du Domain.

Exemples conceptuels :

```text
VersionReport
DoctorReport
SchemaValidationReport
SchemaInspectionReport
EngineReport
ContractReport
CLIErrorReport
```

## 5. JSON contract

Succès :

```json
{
  "contract_version": 1,
  "ok": true,
  "command": "doctor",
  "data": {}
}
```

Erreur :

```json
{
  "contract_version": 1,
  "ok": false,
  "command": "doctor",
  "error": {}
}
```

Le JSON doit être UTF-8, sans ANSI, sans Rich markup, sans dépendance à la largeur du terminal, sans timestamp/UUID/hostname par défaut.

Les consumers doivent tolérer des champs additifs inconnus. L'ordre des clés et le whitespace ne sont pas contractuels.

## 6. stdout / stderr

| Situation | stdout | stderr |
|---|---|---|
| report humain succès | report | warnings éventuels |
| report JSON succès | JSON | vide normalement |
| report humain erreur | vide | erreur |
| report JSON erreur | JSON error | vide normalement |
| payload stdout succès | payload | vide normalement |
| payload fichier succès | vide/minimal | vide normalement |
| payload erreur | vide | erreur |
| debug | résultat normal | détails techniques |
| bootstrap sans CLI | vide | guidance stdlib |

## 7. Payload purity

Les payloads ne doivent jamais contenir :

```text
Success!
Generated:
Output:
Rich panels
progress bars
status messages
```

Les redirections doivent produire des fichiers valides :

```bash
ptk schema format schema.yml > canonical.yml
ptk schema convert schema.yml --to json > schema.json
ptk doctor --json > doctor.json
```

## 8. Human rendering

Rich est réservé à la présentation humaine. Le rendu humain est sémantiquement stable mais non byte-stable.

Peuvent évoluer sans breaking change :

```text
couleurs
bordures
spacing
line wrapping
minor wording
```

Doivent rester présents :

```text
outcome
error identity
critical message
path/context pertinent
actionable hint quand nécessaire
```

## 9. Color

La couleur est cosmétique et non sémantique. Les mots tels que `AVAILABLE`, `MISSING`, `ERROR`, `VALID` doivent rester lisibles sans couleur.

`--no-color` élimine les séquences ANSI. Le JSON et les payloads n'en contiennent jamais.

La CLI peut respecter `NO_COLOR`, mais `--no-color` reste l'option publique explicite.

## 10. TTY / non-TTY

Le TTY peut influencer :

```text
colors
borders
wrapping
decorations
```

Il ne peut jamais influencer :

```text
data
validation result
exit code
JSON
payload
```

Aucun prompt, full-screen UI ou comportement interactif n'est requis en 1.2.

## 11. Quiet

`--quiet` réduit les informations non essentielles mais ne masque jamais une erreur fatale.

Pour l'automatisation, `--json` ou l'exit code sont préférés.

`--quiet --verbose` et `--quiet --debug` sont invalides.

## 12. Verbose

`--verbose` enrichit le report humain avec des détails déjà connus. Il ne déclenche aucun réseau, plugin ou exécution métier supplémentaire.

`--json --verbose` est rejeté afin de garder un seul contrat JSON.

## 13. Debug

`--debug` ajoute les diagnostics techniques sur stderr et peut afficher une traceback sur erreur interne.

Il ne change jamais :

```text
semantic outcome
exit category
PTK error identity
payload
security redaction
```

## 14. Rendu par commande

### version

Sortie compacte :

```text
PyTransformKit 1.2.0
Python 3.x
```

### doctor

Table de checks avec statut et version.

### schema validate

Succès compact ; échec avec `PTK-*`, message et path.

### schema inspect

Table fields :

```text
name
type
nullable
description
```

### engines list / inspect

Ordre déterministe, qualification et capabilities issues de la source canonique.

### contract inspect

Identité et version des contrats embarqués.

## 15. User content safety

Les valeurs utilisateur doivent être rendues comme données littérales.

Rich markup ou séquences terminales provenant d'un fichier ne doivent pas devenir des instructions de style/terminal.

Aucun `repr(exception)` ou `repr(report)` brut ne doit devenir une sortie utilisateur publique.

## 16. Unicode

Les sorties supportent UTF-8. Le JSON machine peut utiliser `ensure_ascii=False`. Les informations essentielles ne doivent pas dépendre d'emoji.

## 17. Déterminisme

Les collections machine utilisent un ordre stable. Aucun `set` ne doit être sérialisé sans normalisation.

Les sorties machine n'introduisent pas de données variables non contractuelles.

## 18. Niveaux de stabilité

### A — Human semantic stability

Stable : sens et informations critiques. Flexible : style.

### B — Machine structural stability

Stable : champs requis, types, command IDs, valeurs sémantiques. Flexible : whitespace, key order, champs additifs.

### C — Canonical payload stability

Autorité : `schema_io` et `SchemaCodec`.

## 19. Broken pipe

Un consumer fermant stdout ne doit pas générer une traceback bruyante. Le mapping attendu suit l'exit model : `BROKEN_PIPE = 141`.

## 20. Tests

La matrice doit couvrir :

```text
human success/error
JSON success/error
payload success/error
stdout/stderr
--no-color
quiet
verbose
debug
TTY/non-TTY
Unicode
ANSI absence
Rich markup injection
deterministic ordering
payload golden fixtures
```

## 21. Invariants

1. Rich est réservé au rendu humain.
2. Le JSON ne dépend pas de Rich.
3. Les payloads ne passent pas par un renderer humain.
4. stdout contient les résultats utiles.
5. stderr contient erreurs humaines et debug.
6. Le JSON reste valide même en erreur.
7. Les payloads ne sont jamais pollués.
8. La couleur n'est jamais sémantique.
9. Le TTY ne change pas la sémantique.
10. Le debug ne change pas l'outcome.
11. Les valeurs utilisateur sont échappées.
12. Les collections machine sont déterministes.
13. Les emitters canoniques restent autorités.

Règle finale :

```text
Reports are rendered.
Payloads are emitted.
```
