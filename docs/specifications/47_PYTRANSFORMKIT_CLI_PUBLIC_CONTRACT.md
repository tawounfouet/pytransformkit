# PyTransformKit — CLI Public Contract

## 1. Portée

Ce document définit le contrat public candidat de la CLI `ptk` pour PyTransformKit 1.2.

Distribution :

```text
pytransformkit
```

Programme :

```text
ptk
```

Version logique du contrat CLI :

```text
cli_contract_version = 1
```

La version produit suit le package PyTransformKit.

## 2. Surface stable candidate

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

## 3. JSON report contract

Succès :

```json
{
  "contract_version": 1,
  "ok": true,
  "command": "version",
  "data": {}
}
```

Erreur :

```json
{
  "contract_version": 1,
  "ok": false,
  "command": "version",
  "error": {}
}
```

Champs requis communs :

```text
contract_version
ok
command
```

Il existe exactement `data` en succès et `error` en échec.

Les consumers doivent tolérer des champs additifs inconnus. L'ordre des clés et le whitespace ne sont pas contractuels.

## 4. version

Le JSON expose au minimum :

```text
data.pytransformkit
data.python
```

## 5. doctor

Le JSON expose au minimum :

```text
data.status
data.checks
```

Chaque check possède :

```text
name
status
version? 
detail?
```

## 6. schema.validate

Succès :

```text
data.path
data.valid
```

Une invalidité syntaxique/sémantique utilise l'enveloppe d'erreur.

## 7. schema.inspect

Le report contient un schema et ses fields. Les fields exposent au minimum :

```text
name
type
nullable
description
```

Pour des types complexes, `type_details` peut être ajouté.

## 8. schema.format

Payload YAML uniquement. Le comportement canonique appartient à `schema_io`.

Garanties :

```text
load(original) == load(formatted)
format(format(x)) == format(x)
```

## 9. schema.convert

Payload YAML ou SchemaCodec JSON uniquement.

SchemaCodec conserve :

```text
contract = pytransformkit.schema
contract_version = 1
```

## 10. engines

Les reports distinguent au minimum :

```text
id
installed
qualification
```

`engines inspect` peut ajouter les capabilities.

Le vocabulaire de qualification doit rester aligné au contrat de conformance existant.

## 11. contract.inspect

Les identifiants candidats sont :

```text
public-api
errors
schema-wire
cli
```

Ils seront gelés dans le snapshot v1.

## 12. stdout/stderr

- human success → stdout ;
- human error → stderr ;
- JSON success → stdout ;
- JSON error → stdout ;
- debug diagnostics → stderr ;
- payload → stdout ou fichier explicite.

## 13. Human output

Le rendu humain est sémantiquement stable mais pas byte-stable. Couleurs, bordures, spacing et wording mineur peuvent évoluer.

## 14. Machine output

Le JSON est contractuel sur les noms/types/sens des champs requis. Aucune donnée non déterministe par défaut.

## 15. Security guarantees

Le contrat public inclut les garanties négatives :

- pas de réseau implicite ;
- pas de plugin command injection ;
- pas d'include implicite ;
- pas d'expansion ENV ;
- pas d'overwrite silencieux ;
- pas de project discovery.

## 16. Packaging guarantees

Le core doit fonctionner sans `[cli]`. Le bootstrap `ptk` sans dépendances CLI doit fournir une instruction d'installation contrôlée.

PyYAML manquant doit préserver `PTK-DECL-010`.

## 17. Freeze

Le snapshot cible est :

```text
contracts/cli_contract_v1.json
```

Il devra enregistrer :

```text
program
command tree
command IDs
arguments/options
report/payload classification
JSON contract
exit codes
error categories
reserved future commands
security/filesystem guarantees
```

## 18. Compatibility

Patch releases : aucune suppression/renommage de commande ou option stable, ni changement de type/sens des champs JSON requis.

Les évolutions additives sont permises si compatibles.

Les futures lignes 1.3+ pourront ajouter des commandes sans casser le CLI contract v1.
