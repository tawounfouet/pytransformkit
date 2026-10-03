# PyTransformKit — CLI Requirements Analysis

## 1. Objectif

Ce document formalise les exigences de la Developer CLI 1.2.

## 2. Exigences fonctionnelles

### FR-001 — Programme public

La commande publique MUST être `ptk`.

### FR-002 — Commandes

La CLI MUST exposer :

```text
version
doctor
schema validate
schema inspect
schema format
schema convert
engines list
engines inspect
contract inspect
```

### FR-003 — Validation

`schema validate PATH` MUST charger un fichier local explicite via `schema_io` et préserver les erreurs publiques `PTK-DECL-*`.

### FR-004 — Inspection

`schema inspect PATH` MUST produire une vue humaine ou machine du `Schema`, distincte du wire `SchemaCodec`.

### FR-005 — Formatage

`schema format PATH` MUST émettre le YAML canonique sur stdout. `--write` MUST être nécessaire pour modifier le fichier.

### FR-006 — Conversion

`schema convert INPUT --to yaml|json` MUST utiliser `schema_io` et `SchemaCodec`. Sans `--output`, le payload va sur stdout.

### FR-007 — Moteurs

`engines list/inspect` MUST distinguer moteur connu, installé et qualification, sans activer arbitrairement les adapters.

### FR-008 — Contrats

`contract inspect` MUST fonctionner depuis un package installé, sans checkout Git requis.

## 3. Exigences non fonctionnelles

### NFR-001 — Python

Support obligatoire : 3.11, 3.12, 3.13, 3.14.

### NFR-002 — Déterminisme

Les sorties machine ne doivent pas inclure par défaut UUID, timestamp, hostname ou ordre non déterministe.

### NFR-003 — Core minimal

`import pytransformkit` MUST fonctionner sans Typer/Rich/PyYAML/engines optionnels.

### NFR-004 — Portabilité

Linux, macOS et Windows sont des cibles supportées.

### NFR-005 — Startup léger

`ptk --help` et `ptk version` ne doivent pas importer les moteurs lourds.

## 4. Exigences d'architecture

### AR-001

Typer MUST rester limité au routage/argument parsing.

### AR-002

Rich MUST rester limité au rendu humain.

### AR-003

La CLI MUST appeler les APIs publiques lorsqu'elles existent.

### AR-004

Les services CLI MUST être indépendants de Typer et Rich autant que possible.

### AR-005

Le JSON machine MUST être sérialisé sans Rich.

## 5. Exigences de sortie

Les Report Commands MUST supporter un mode machine JSON.

Enveloppe succès :

```json
{
  "contract_version": 1,
  "ok": true,
  "command": "schema.validate",
  "data": {}
}
```

Enveloppe erreur :

```json
{
  "contract_version": 1,
  "ok": false,
  "command": "schema.validate",
  "error": {}
}
```

Les Payload Commands ne doivent pas utiliser cette enveloppe.

## 6. Streams

- succès humain : stdout ;
- erreur humaine : stderr ;
- succès JSON : stdout ;
- erreur JSON : stdout ;
- debug : stderr ;
- payload : stdout ou fichier explicite.

Le JSON et les payloads ne doivent contenir aucun ANSI.

## 7. Options communes

Les Report Commands pourront utiliser selon leur besoin :

```text
--json
--quiet
--verbose
--debug
--no-color
```

Les combinaisons contradictoires doivent échouer explicitement. `quiet + verbose` et `quiet + debug` sont invalides. La combinaison `json + verbose` doit être rejetée pour éviter plusieurs contrats machine.

## 8. Sécurité

La CLI MUST :

- utiliser le parser YAML sécurisé existant ;
- refuser les sources réseau ;
- ne pas étendre les variables d'environnement des documents ;
- ne pas activer les plugins implicitement ;
- ne pas exécuter de shell ;
- ne pas installer automatiquement des dépendances ;
- redacter les secrets dans les diagnostics ;
- protéger les écritures par une stratégie atomique lorsque possible.

## 9. Packaging

Un extra `cli` doit contenir Typer et Rich. Le script console `ptk` doit passer par un bootstrap contrôlé capable d'expliquer l'absence de l'extra CLI sans traceback brut.

## 10. Compatibilité

Les contrats historiques 1.0/1.1 sont immuables. La CLI est additive. Toute nouvelle surface contractuelle doit être figée dans un nouveau snapshot dédié.

## 11. Tests

Les critères d'acceptation incluent :

- unit ;
- integration ;
- contract ;
- security ;
- wheel/sdist ;
- Python matrix ;
- platform smoke ;
- core-without-cli ;
- cli-without-yaml ;
- cli-with-yaml.
