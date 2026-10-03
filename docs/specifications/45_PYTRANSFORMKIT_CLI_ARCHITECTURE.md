# PyTransformKit — CLI Architecture

## 1. Positionnement

La CLI est un **driving adapter** autour du framework existant.

```text
Shell
  ↓
bootstrap
  ↓
Typer application
  ↓
commands
  ↓
services
  ↓
public PyTransformKit APIs
  ↓
reports / canonical payloads
  ↓
renderers
```

La dépendance inverse est interdite.

## 2. Package cible

```text
src/pytransformkit/cli/
├── __init__.py
├── __main__.py
├── bootstrap.py
├── app.py
├── context.py
├── exit_codes.py
├── exceptions.py
├── filesystem.py
├── security.py
├── commands/
│   ├── version.py
│   ├── doctor.py
│   ├── schema.py
│   ├── engines.py
│   └── contract.py
├── services/
│   ├── version.py
│   ├── doctor.py
│   ├── schema.py
│   ├── engines.py
│   └── contracts.py
├── models/
│   ├── reports.py
│   ├── errors.py
│   └── outputs.py
└── rendering/
    ├── console.py
    ├── human.py
    ├── json.py
    ├── errors.py
    └── tables.py
```

Cette structure est une cible ; l'implémentation peut rester plus petite tant que les responsabilités restent séparées.

## 3. Bootstrap

Le script console doit cibler :

```text
pytransformkit.cli.bootstrap:main
```

et non directement l'objet Typer.

Le bootstrap doit pouvoir :

1. détecter l'absence de Typer/Rich ;
2. produire une instruction d'installation simple ;
3. sortir avec le code dédié à une dépendance optionnelle manquante ;
4. importer l'application seulement après cette vérification.

## 4. CLIContext

Le contexte CLI contient uniquement des préoccupations d'interface :

```text
output mode
quiet
verbose
debug
color
```

Il ne contient pas de :

```text
project
profile
target
manifest
workflow state
```

## 5. Commands

Les handlers Typer restent minces :

```text
parse
validate CLI-level options
call service
render
return process outcome
```

Ils ne portent pas de sémantique Schema/engine.

## 6. Services

Les services coordonnent les APIs publiques et transforment leurs résultats en reports neutres de présentation.

Exemples :

```text
SchemaCLIService
DoctorService
EngineInspectionService
ContractInspectionService
```

Ils ne doivent pas appeler Rich.

## 7. Reports

Les reports sont simples, typés, déterministes et sérialisables. Un même report peut alimenter le HumanRenderer et le JSONRenderer.

## 8. Rendering

```text
HumanRenderer → Rich
JSONRenderer  → stdlib json
```

Le JSONRenderer ne doit pas importer Rich.

Les payloads canoniques ne passent pas par ces renderers :

```text
schema_io      → YAML payload
SchemaCodec    → JSON payload
```

## 9. Filesystem

Les services n'effectuent que des accès explicitement demandés. Les écritures complètes utilisent autant que possible :

```text
generate full payload
→ temp sibling
→ flush/close
→ atomic replace
```

## 10. Engines

La détection de disponibilité doit préférer metadata/find_spec/registry plutôt qu'initialiser tous les moteurs. Les capabilities viennent des contrats de conformance, pas de la réflexion sur les méthodes.

## 11. Doctor

Les checks sont indépendants et isolés. Un check optionnel manquant n'empêche pas les autres checks. Aucun réseau ni auto-update.

## 12. Contracts

Les métadonnées nécessaires à `contract inspect` doivent être disponibles dans l'artefact installé. La commande ne doit pas dépendre du dossier Git `contracts/` de la checkout.

## 13. Plugin boundary

La CLI ne fournit pas de mécanisme de commande dynamique via plugins en 1.2. La simple inspection ne doit pas activer du code tiers.

## 14. Import boundaries

Le core ne doit jamais importer `pytransformkit.cli`. Les modules CLI peuvent dépendre du core via ses surfaces publiques.

## 15. Invariants

1. CLI = adapter.
2. Typer = routing.
3. Rich = presentation.
4. Services = coordination.
5. Domain = semantic authority.
6. Report JSON indépendant de Rich.
7. Payloads canoniques inchangés.
8. Aucun project runtime en 1.2.
9. Aucun hidden engine fallback.
10. Aucun plugin command injection.
