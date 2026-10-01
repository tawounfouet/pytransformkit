# 28 — PyTransformKit Declarative Schema — Expression du besoin

> **Document status:** DRAFT  
> **Scope:** PyTransformKit post-1.0 authoring experience  
> **Subject:** Declarative schema definitions  
> **Primary candidate format:** YAML  
> **Canonical runtime/domain model:** Schema / Field / DataType  
> **Target release line:** à déterminer par la roadmap d'implémentation

---

## 1. Contexte

PyTransformKit 1.0.0 fournit un modèle de schéma typé, immutable et indépendant des moteurs physiques.

Le modèle canonique repose notamment sur :

~~~text
Schema
└── Field
    ├── name
    ├── DataType
    ├── nullable
    └── metadata
~~~

Un schéma est aujourd'hui défini directement en Python.

Exemple :

~~~python
schema = Schema(
    fields=(
        Field(
            "customer_id",
            IntegerType(),
            nullable=False,
        ),
        Field(
            "email",
            StringType(),
            nullable=True,
        ),
        Field(
            "status",
            StringType(),
            nullable=False,
        ),
    )
)
~~~

Cette API Python est explicite, typée et adaptée à la construction dynamique.

Elle devient néanmoins relativement verbeuse lorsque :

- de nombreux schémas doivent être maintenus ;
- les schémas sont principalement déclaratifs et peu dynamiques ;
- les définitions sont relues par des profils Data Engineering, Analytics Engineering, Data Quality ou Data Governance ;
- plusieurs datasets partagent un même dépôt de contrats ;
- les équipes souhaitent versionner les contrats de données séparément du code d'exécution ;
- les schémas servent autant à la documentation et à la gouvernance qu'au runtime.

L'expérience des outils Data modernes, notamment dbt, montre qu'un format déclaratif lisible par l'humain peut compléter efficacement une API programmable.

Le besoin n'est toutefois pas de remplacer le modèle Python de PyTransformKit ni de faire de YAML une représentation interne du framework.

Le besoin est de fournir **une nouvelle surface d'authoring déclarative** permettant de produire exactement les mêmes objets de domaine Schema.

---

## 2. Problème

La représentation Python actuelle est adaptée à la logique applicative mais présente plusieurs limites pour les schémas essentiellement statiques.

### 2.1 Verbosité

Une définition simple exige plusieurs constructions imbriquées :

~~~python
Schema(
    fields=(
        Field("customer_id", IntegerType(), nullable=False),
        Field("email", StringType(), nullable=True),
        Field("status", StringType(), nullable=False),
    )
)
~~~

Lorsque des dizaines ou centaines de champs sont concernés, la structure métier du schéma devient moins immédiatement lisible.

### 2.2 Couplage de l'authoring au code Python

Un schéma purement déclaratif doit actuellement être exprimé sous forme de code.

Cela impose :

- un fichier Python ;
- des imports ;
- une connaissance minimale de l'API PyTransformKit ;
- une exécution Python pour charger la définition.

Pour certaines équipes, un schéma doit pouvoir être relu et modifié sans manipuler le code applicatif.

### 2.3 Lisibilité des contrats de données

Les informations suivantes sont naturellement déclaratives :

- nom du champ ;
- type logique ;
- nullabilité ;
- description ;
- classification ;
- metadata ;
- contraintes structurelles.

Elles sont souvent plus lisibles lorsqu'elles apparaissent sous forme de document structuré plutôt que comme appels de constructeurs Python.

### 2.4 Industrialisation

Une organisation peut souhaiter conserver :

~~~text
schemas/
├── customers.yml
├── orders.yml
├── products.yml
└── payments.yml
~~~

et utiliser ces fichiers comme contrats versionnés entre plusieurs pipelines, applications ou équipes.

PyTransformKit ne propose pas actuellement de surface standard pour ce besoin.

---

## 3. Expression du besoin

PyTransformKit doit pouvoir accepter une définition déclarative de schéma, initialement en YAML, et la convertir de manière stricte et déterministe en son modèle de domaine canonique.

Le besoin cible la chaîne conceptuelle suivante :

~~~text
YAML
  │
  ▼
Declarative Schema Document
  │
  ▼
Parsing + validation
  │
  ▼
SchemaDefinition
  │
  ▼
SchemaDefinitionCompiler
  │
  ▼
Schema
  ├── Field
  └── DataType
~~~

Le résultat doit être sémantiquement équivalent à la construction directe en Python.

Ainsi :

~~~yaml
version: 1

schema:
  name: customers
  fields:
    - name: customer_id
      type: integer
      nullable: false

    - name: email
      type: string
      nullable: true

    - name: status
      type: string
      nullable: false
~~~

doit pouvoir produire le même modèle logique que :

~~~python
Schema(
    fields=(
        Field("customer_id", IntegerType(), nullable=False),
        Field("email", StringType(), nullable=True),
        Field("status", StringType(), nullable=False),
    )
)
~~~

---

## 4. Principe architectural fondamental

Le format déclaratif ne devient pas le modèle de domaine.

La règle structurante est :

~~~text
YAML != Schema
YAML != canonical IR
YAML != runtime contract

YAML = authoring format
Schema = canonical domain model
~~~

Par conséquent :

- Schema reste indépendant de YAML ;
- Field reste indépendant de YAML ;
- DataType reste indépendant de YAML ;
- le Domain ne dépend pas de PyYAML ou d'un parser externe ;
- les transformations continuent de recevoir des Schema ;
- le runtime continue de manipuler le modèle canonique ;
- la serialization canonique de PyTransformKit reste distincte du YAML d'authoring.

Cette séparation doit être considérée comme non négociable.

---

## 5. Objectifs

### 5.1 Réduire la friction d'authoring

Permettre de décrire des schémas statiques avec une syntaxe concise et lisible.

### 5.2 Préserver le Domain existant

Aucune nouvelle représentation déclarative ne doit devenir un second modèle concurrent de Schema.

### 5.3 Améliorer la lisibilité des contrats

Un fichier de schéma doit pouvoir servir de support de revue technique et fonctionnelle.

### 5.4 Permettre le versionnement indépendant

Les équipes doivent pouvoir versionner leurs schémas comme artefacts déclaratifs dans Git sans les enfouir dans le code applicatif.

### 5.5 Supporter les types PyTransformKit

Le format déclaratif doit pouvoir exprimer les types logiques existants, y compris les types paramétrés et imbriqués.

### 5.6 Conserver une validation stricte

Toute ambiguïté ou donnée invalide doit échouer explicitement.

Aucune coercition silencieuse ne doit modifier la sémantique déclarée.

### 5.7 Permettre une évolution versionnée du format

Le document déclaratif doit posséder sa propre version :

~~~yaml
version: 1
~~~

Cette version doit rester indépendante de la version du package PyTransformKit.

---

## 6. Non-objectifs

Cette évolution ne vise pas à :

- remplacer l'API Python Schema ;
- remplacer la serialization canonique V1 ;
- définir un langage complet de transformations en YAML ;
- introduire un moteur de workflow déclaratif ;
- permettre l'exécution de code Python arbitraire depuis YAML ;
- importer dynamiquement des classes à partir de chaînes fournies dans le fichier ;
- faire de YAML une dépendance du Domain ;
- reproduire dbt dans PyTransformKit ;
- convertir PyTransformKit en framework configuration-first.

Le besoin porte exclusivement sur **l'authoring déclaratif des schémas**.

---

## 7. Pourquoi conserver l'API Python

Les deux modes d'authoring répondent à des besoins différents.

### Python

Approprié pour :

- schémas générés dynamiquement ;
- tests unitaires ;
- notebooks ;
- bibliothèques ;
- composition programmative ;
- génération conditionnelle ;
- intégration directe dans du code métier.

### YAML

Approprié pour :

- schémas statiques ;
- contrats de données ;
- repositories Data ;
- documentation versionnée ;
- revue par des profils non développeurs Python ;
- grands catalogues de datasets ;
- gouvernance.

La cible est donc :

~~~text
            Authoring
               │
       ┌───────┴───────┐
       │               │
    Python            YAML
       │               │
       │         loader/compiler
       │               │
       └───────┬───────┘
               ▼
             Schema
               │
               ▼
         PyTransformKit
~~~

---

## 8. Utilisateurs cibles

### 8.1 Data Engineer

Le Data Engineer souhaite définir les contrats d'entrée et de sortie d'un pipeline sans répéter de longues constructions Python.

### 8.2 Analytics Engineer

L'Analytics Engineer est habitué à une logique déclarative proche de dbt et souhaite relire rapidement types, nullabilité et descriptions.

### 8.3 Data Quality Engineer

Le Data Quality Engineer doit pouvoir associer ultérieurement les champs à des contraintes et règles de validation sans réécrire le modèle métier.

### 8.4 Data Governance / Data Steward

Le Data Steward doit pouvoir inspecter un contrat sans comprendre la totalité de l'API Python.

### 8.5 Développeur Python

Le développeur doit pouvoir continuer à utiliser l'API Python existante sans changement ni dépendance supplémentaire obligatoire.

---

## 9. Cas d'usage prioritaires

### UC-01 — Charger un schéma unique

~~~text
customers.yml
      ↓
loader
      ↓
Schema
~~~

### UC-02 — Définir plusieurs schémas dans un document

~~~yaml
version: 1

schemas:
  customers:
    ...

  orders:
    ...
~~~

### UC-03 — Décrire les types paramétrés

~~~yaml
type:
  decimal:
    precision: 18
    scale: 2
~~~

### UC-04 — Décrire les types imbriqués

~~~yaml
type:
  struct:
    fields:
      - name: city
        type: string

      - name: country
        type: string
~~~

### UC-05 — Ajouter de la documentation

~~~yaml
- name: email
  type: string
  nullable: true
  description: Customer contact email
~~~

### UC-06 — Ajouter de la metadata

Le format doit pouvoir transporter une metadata portable sans introduire de logique d'exécution.

### UC-07 — Exporter un Schema

Un Schema créé en Python doit pouvoir être exporté vers une représentation YAML déclarative.

Le round-trip recherché est **sémantique**, pas textuel.

---

## 10. Forme déclarative illustrative

La syntaxe définitive sera figée dans la spécification dédiée.

Une forme candidate est :

~~~yaml
version: 1

schemas:
  customers:
    description: Customer master dataset

    fields:
      - name: customer_id
        type: integer
        nullable: false
        description: Stable customer identifier

      - name: email
        type: string
        nullable: true
        metadata:
          classification: pii

      - name: account_balance
        type:
          decimal:
            precision: 18
            scale: 2
        nullable: true

      - name: address
        type:
          struct:
            fields:
              - name: city
                type: string
                nullable: true

              - name: country
                type: string
                nullable: true
        nullable: true
~~~

Cette syntaxe n'est pas encore normative.

Elle illustre seulement le niveau d'expressivité recherché.

---

## 11. Types à prendre en compte

Le langage déclaratif doit pouvoir couvrir le système de types logique de PyTransformKit.

Le périmètre attendu comprend notamment :

~~~text
String
Boolean
Integer
Float
Decimal
Date
Time
Timestamp
Duration
Binary
List
Struct
Map
Unknown
~~~

Les paramètres propres à certains types doivent être explicitement représentés.

Exemples :

~~~yaml
type:
  decimal:
    precision: 18
    scale: 2
~~~

~~~yaml
type:
  list:
    element:
      type: string
~~~

~~~yaml
type:
  map:
    key:
      type: string
    value:
      type: integer
~~~

La correspondance normative YAML ↔ DataType fera l'objet d'un document dédié.

---

## 12. Validation attendue

Le parser doit fonctionner selon une politique fail-closed.

### Exemple : type inconnu

~~~yaml
type: intger
~~~

doit produire une erreur explicite.

Il ne doit pas devenir silencieusement UnknownType.

### Exemple : propriété inconnue

~~~yaml
name: id
type: integer
nulable: false
~~~

Le typo nulable ne doit pas être ignoré.

### Exemple : mauvais type de valeur

~~~yaml
nullable: "false"
~~~

Une chaîne ne doit pas nécessairement être acceptée comme équivalent d'un booléen.

Le niveau exact de coercition autorisé devra être défini explicitement.

---

## 13. Sécurité

Le format déclaratif est une entrée potentiellement non fiable.

Le système doit notamment interdire :

- les constructeurs YAML Python arbitraires ;
- les tags permettant l'instanciation de classes ;
- les imports dynamiques pilotés par le document ;
- eval ;
- exec ;
- les payloads susceptibles de contourner le registre fermé des types ;
- les profondeurs ou tailles non bornées lorsque cela expose à un risque de DoS.

Le chargement YAML doit produire uniquement des valeurs structurées sûres avant compilation vers le Domain.

---

## 14. Dépendances

Le support YAML ne doit pas imposer une nouvelle dépendance obligatoire au cœur de PyTransformKit si elle peut être évitée.

Deux modèles restent à étudier.

### Option A — dépendance YAML standard

~~~text
pip install pytransformkit
~~~

inclut le parser YAML.

### Option B — extra optionnel

~~~text
pip install "pytransformkit[yaml]"
~~~

Le second modèle est cohérent avec la politique existante d'isolation des capacités optionnelles.

La décision sera prise dans l'analyse des exigences et l'architecture détaillée.

---

## 15. Relation avec la serialization canonique

PyTransformKit dispose déjà de contrats de serialization versionnés.

Le YAML d'authoring ne doit pas remplacer ces contrats.

Les deux surfaces ont des finalités différentes :

| Surface | Objectif |
| --- | --- |
| YAML declarative schema | authoring humain |
| Python Domain Schema | modèle canonique en mémoire |
| Serialization contract | échange déterministe/versionné |
| Engine schema | représentation physique spécifique |

La chaîne doit donc rester :

~~~text
Human YAML
    ↓
SchemaDefinition
    ↓
Schema
    ↓
Canonical serialization / runtime / engines
~~~

et non :

~~~text
YAML
    ↓
physical engine
~~~

---

## 16. Relation avec dbt

dbt constitue une source d'inspiration importante pour l'expérience déclarative, mais PyTransformKit ne doit pas copier son modèle sans tenir compte de ses propres frontières.

Les éléments intéressants sont notamment :

- fichiers YAML lisibles ;
- descriptions proches du schéma ;
- centralisation des contrats ;
- revue Git simple ;
- séparation entre déclaration et exécution.

Les différences restent fondamentales :

- PyTransformKit est engine-agnostic ;
- son Schema est un objet de Domain ;
- son système de types ne dépend pas d'un entrepôt SQL ;
- sa serialization est déjà versionnée indépendamment ;
- ses transformations peuvent s'exécuter sur plusieurs moteurs ;
- YAML doit rester une façade d'authoring, pas devenir le runtime model.

---

## 17. Besoins fonctionnels de haut niveau

Le futur mécanisme doit permettre au minimum :

1. de charger un document YAML ;
2. de vérifier sa version ;
3. de valider sa structure ;
4. de résoudre ses types ;
5. de construire un ou plusieurs Schema ;
6. de détecter les noms de champs dupliqués ;
7. de préserver l'ordre des champs ;
8. de représenter la nullabilité ;
9. de représenter les types paramétrés ;
10. de représenter les types imbriqués ;
11. de transporter descriptions et metadata lorsque compatibles avec le Domain ;
12. de produire des erreurs structurées ;
13. d'exporter un Schema vers YAML ;
14. de garantir un round-trip sémantique ;
15. de fonctionner sans importer les moteurs physiques.

---

## 18. Besoins non fonctionnels

### Déterminisme

Une même déclaration doit produire le même Schema.

### Isolation du Domain

Aucun import YAML ne doit apparaître dans le package Domain.

### Sécurité

Le parser doit être safe-by-default et fail-closed.

### Testabilité

Chaque type et chaque erreur doivent pouvoir être testés sans moteur physique.

### Compatibilité

L'ajout de la couche déclarative ne doit pas casser les utilisateurs Python existants.

### Optionalité

L'absence éventuelle de la dépendance YAML ne doit pas casser l'import du core.

### Observabilité des erreurs

Les erreurs doivent indiquer le document, le schéma, le champ et le chemin fautif lorsque ces informations sont disponibles.

---

## 19. Critères de succès

La fonctionnalité sera considérée comme réussie lorsque :

- un utilisateur peut définir un schéma réaliste en YAML sans écrire les constructeurs Python correspondants ;
- le résultat est un Schema canonique existant ;
- aucune nouvelle représentation de runtime concurrente n'est introduite ;
- les types simples, paramétrés et imbriqués sont supportés conformément au Domain ;
- les erreurs sont strictes, localisées et déterministes ;
- Python et YAML produisent des objets sémantiquement équivalents ;
- les schémas peuvent être exportés et rechargés sans perte sémantique ;
- le Domain reste indépendant du parser YAML ;
- l'import du core reste possible sans moteurs physiques ;
- la sécurité de parsing est couverte par des tests négatifs.

---

## 20. Risques identifiés

### 20.1 Création d'un second modèle de Schema

Le risque principal serait de laisser SchemaDefinition devenir un objet métier concurrent de Schema.

Le compilateur doit donc constituer une frontière claire.

### 20.2 Dérive vers un DSL général

Après les schémas, il peut être tentant d'exprimer transformations, pipelines, workflows et logique conditionnelle en YAML.

Cette évolution n'est pas implicite.

Chaque éventuel DSL devra faire l'objet d'une décision séparée.

### 20.3 Ambiguïtés YAML

Le parsing YAML peut introduire des conversions implicites surprenantes.

Une politique de parsing stricte sera nécessaire.

### 20.4 Divergence avec le système de types

La syntaxe déclarative doit être dérivée du système de types PyTransformKit, et non créer son propre vocabulaire parallèle.

### 20.5 Surcharge de dépendances

Le support YAML ne doit pas remettre en cause l'isolation légère du package core.

---

## 21. Décisions proposées à ce stade

### DEC-01

Schema reste le modèle canonique.

### DEC-02

YAML est une surface d'authoring, pas une représentation runtime.

### DEC-03

La définition déclarative est versionnée indépendamment du package.

### DEC-04

Le parsing est strict et fail-closed.

### DEC-05

Le Domain ne dépend pas du parser YAML.

### DEC-06

L'API Python actuelle reste pleinement supportée.

### DEC-07

Les types déclaratifs doivent être mappés vers les DataType existants.

### DEC-08

Le round-trip recherché est sémantique, pas textuel.

### DEC-09

Les transformations et workflows YAML ne font pas partie de ce besoin.

---

## 22. Questions à résoudre dans les documents suivants

Les points suivants restent volontairement ouverts :

- le nom exact du format et du namespace public ;
- la forme normative d'un document mono-schema ;
- la forme normative d'un document multi-schema ;
- la syntaxe exacte des types imbriqués ;
- le comportement de UnknownType ;
- la représentation des metadata ;
- la représentation éventuelle de contraintes de qualité ;
- la politique de propriétés inconnues ;
- le support ou non des YAML anchors/aliases ;
- les limites de taille et de profondeur ;
- le choix du parser YAML ;
- l'extra optionnel éventuel yaml ;
- l'emplacement architectural de SchemaDefinition ;
- l'API load_schema / load_schemas / exporter ;
- les codes d'erreur associés ;
- la stratégie de versioning du document ;
- la compatibilité future entre versions de documents.

---

## 23. Documents de conception suivants

La conception doit se poursuivre avec :

~~~text
29_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_REQUIREMENTS_ANALYSIS.md
30_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ARCHITECTURE.md
31_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SPECIFICATION.md
32_PYTRANSFORMKIT_DECLARATIVE_TYPE_SYSTEM_MAPPING.md
33_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_DOMAIN_MODEL.md
34_PYTRANSFORMKIT_SCHEMA_LOADER_COMPILER_AND_EXPORTER_SPEC.md
35_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_VALIDATION_AND_ERROR_MODEL.md
36_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_SECURITY_AND_PARSING_POLICY.md
37_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_ROUNDTRIP_AND_SERIALIZATION_MODEL.md
38_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_PUBLIC_API_SPEC.md
39_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_TEST_MATRIX_AND_ACCEPTANCE_CRITERIA.md
40_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_IMPLEMENTATION_ROADMAP.md
41_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_GETTING_STARTED.md
42_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_REFERENCE_EXAMPLES.md
~~~

---

## 24. Résumé

PyTransformKit possède désormais un modèle de schéma mature et qualifié.

La prochaine amélioration recherchée n'est pas de modifier ce modèle, mais d'améliorer la manière dont les utilisateurs peuvent l'exprimer.

La cible est donc :

~~~text
Python authoring ─────┐
                      │
YAML authoring ───────┼────> Schema ────> PyTransformKit
                      │
future authoring ─────┘
~~~

Le Domain reste unique.

Le YAML devient une façade déclarative lisible, versionnable et strictement contrôlée.

Cette distinction constitue le principe directeur de toute l'évolution.
