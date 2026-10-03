# PyTransformKit — CLI Command Model

## 1. Arbre canonique

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

Command IDs :

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

## 2. Report Commands

```text
version
doctor
schema.validate
schema.inspect
engines.list
engines.inspect
contract.inspect
```

Ils peuvent proposer un rendu humain ou `--json`.

## 3. Payload Commands

```text
schema.format
schema.convert
```

Ils émettent directement un payload canonique et n'acceptent pas `--json` comme mode report.

## 4. Root

`ptk` et les groupes sans leaf command peuvent afficher le help et sortir avec 0. Aucune discovery de projet n'est effectuée.

`ptk --version` peut être un alias pratique de `ptk version`.

## 5. version

```bash
ptk version
ptk version --json
```

Données minimales : version PyTransformKit et version Python. Startup léger.

## 6. doctor

```bash
ptk doctor
ptk doctor --json
```

Checks minimum :

```text
PyTransformKit
Python
CLI dependencies
PyYAML
Pandas
Polars
PyArrow
DuckDB
```

États :

```text
available
missing
incompatible
error
not_applicable (optionnel)
```

Une dépendance optionnelle absente n'implique pas nécessairement un exit non-zero.

## 7. schema validate

```bash
ptk schema validate PATH
```

Un seul fichier local explicite. Pas d'URL, directory scan ou récursion. Le chargement passe par `schema_io`.

## 8. schema inspect

```bash
ptk schema inspect PATH
```

Report des fields avec au minimum :

```text
name
type
nullable
description
```

Le JSON d'inspection n'est pas un SchemaCodec payload.

## 9. schema format

```bash
ptk schema format PATH
ptk schema format PATH --write
```

Sans `--write` : YAML canonique stdout, fichier inchangé.

Avec `--write` : remplacement explicite, atomique autant que possible. L'opération doit être idempotente.

## 10. schema convert

```bash
ptk schema convert INPUT --to yaml|json
```

Options :

```text
--from yaml|json
--to yaml|json
--name NAME
--output PATH
--force
--debug
```

Inférence uniquement via `.yml`, `.yaml`, `.json`. `--from` explicite domine.

YAML → JSON :

```text
schema_io → Schema → SchemaCodec
```

JSON → YAML :

```text
SchemaCodec → Schema → schema_io
```

Le nom doit être fourni lorsque nécessaire à l'authoring YAML ; il ne doit pas être inventé depuis un filename.

## 11. engines list

Affiche les moteurs connus avec disponibilité et qualification, sans initialiser tous les adapters.

## 12. engines inspect ENGINE

`ENGINE` est un identifiant connu et normalisé. Un moteur connu absent peut être inspecté statiquement. Un identifiant inconnu est une erreur d'usage.

## 13. contract inspect

```bash
ptk contract inspect
ptk contract inspect CONTRACT
```

Identifiants candidats :

```text
public-api
errors
schema-wire
cli
```

Le vocabulaire final sera figé par le CLI contract snapshot.

## 14. Options de rendu

Options applicables selon commande :

```text
--json
--quiet
--verbose
--debug
--no-color
```

`quiet + verbose` et `quiet + debug` sont invalides. `json + verbose` doit être rejeté pour ne pas créer plusieurs formes machine.

## 15. Help

Chaque leaf command doit fonctionner avec `--help` sans PyYAML ni moteurs lourds.

## 16. Noms réservés

```text
project
run
compile
plan
build
test
```

Ils ne peuvent pas être introduits en 1.2.
