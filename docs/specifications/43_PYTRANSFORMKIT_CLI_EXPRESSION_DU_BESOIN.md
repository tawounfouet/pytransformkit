# PyTransformKit — CLI Expression du besoin

## 1. Contexte

PyTransformKit 1.1.0 fournit une bibliothèque Python stable, un modèle `Schema` canonique, `pytransformkit.schema_io` pour l'authoring YAML et `SchemaCodec` comme contrat wire JSON. La ligne 1.2 introduit une **Developer CLI** sans transformer PyTransformKit en runtime de projet.

Le programme public est :

```text
ptk
```

## 2. Besoin

Les développeurs doivent pouvoir accéder depuis un terminal aux capacités d'inspection et de validation déjà portées par les APIs publiques :

```text
version
diagnostic local
validation de schéma
inspection de schéma
formatage déclaratif
conversion YAML ↔ SchemaCodec JSON
inspection des moteurs
inspection des contrats
```

La CLI est un adaptateur primaire :

```text
Shell
  ↓
ptk
  ↓
CLI commands
  ↓
CLI services
  ↓
Public PyTransformKit APIs
```

Elle ne redéfinit aucune sémantique métier.

## 3. Surface cible 1.2

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

## 4. Expérience attendue

La CLI doit être :

- explicite ;
- scriptable ;
- déterministe ;
- utilisable en CI ;
- lisible pour un humain ;
- stable pour une machine ;
- sûre par défaut ;
- compatible avec Python 3.11 à 3.14.

Typer est utilisé pour le routage. Rich est utilisé uniquement pour le rendu humain.

## 5. Modèle d'installation

Le core reste minimal :

```bash
pip install pytransformkit
```

La CLI devient un extra :

```bash
pip install "pytransformkit[cli]"
```

Le support YAML reste indépendant :

```bash
pip install "pytransformkit[yaml]"
pip install "pytransformkit[cli,yaml]"
```

Typer et Rich ne doivent pas devenir des dépendances du core.

## 6. Sorties

Deux familles sont distinguées :

### Reports

```text
version
doctor
schema.validate
schema.inspect
engines.list
engines.inspect
contract.inspect
```

Ils peuvent produire un rendu humain ou un report JSON versionné.

### Payloads

```text
schema.format
schema.convert
```

Ils émettent directement le YAML canonique ou le JSON SchemaCodec. Aucun wrapper CLI ne doit contaminer ces payloads.

## 7. Sécurité

La CLI ne doit pas introduire de capacité implicite supplémentaire :

- aucun téléchargement distant ;
- aucun include YAML ;
- aucune expansion de variables d'environnement ;
- aucune activation implicite de plugin ;
- aucune exécution arbitraire ;
- aucune écriture implicite ;
- aucun overwrite silencieux.

## 8. Hors périmètre 1.2

Sont explicitement exclus :

```text
pytransformkit.yml
ProjectDefinition
profiles
targets
project discovery
ptk project
ptk run
ptk compile
ptk plan
ptk build
ptk test
workflow orchestration
scheduling
run history
```

Ces sujets appartiennent aux lignes futures :

```text
1.3 — Project Contract
1.4 — Project Execution
```

## 9. Invariants

1. La CLI reste un adaptateur.
2. Le Domain n'importe jamais la CLI.
3. `Schema` reste l'autorité sémantique.
4. `schema_io` reste l'autorité YAML.
5. `SchemaCodec` reste l'autorité JSON wire.
6. Les dépendances CLI restent optionnelles.
7. Les erreurs `PTK-*` conservent leur identité.
8. Les comportements non supportés échouent explicitement.
9. Aucun projet n'est découvert implicitement.
10. Les contrats 1.0 et 1.1 restent compatibles.

## 10. Critère de réussite

La ligne 1.2 est réussie lorsque `ptk` est installable, sûr, scriptable, qualifié depuis wheel/sdist et consommable sans modifier le modèle métier du framework.
