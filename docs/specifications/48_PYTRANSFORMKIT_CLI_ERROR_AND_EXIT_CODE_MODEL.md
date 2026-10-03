# PyTransformKit — CLI Error and Exit Code Model

## 1. Principe

Trois dimensions sont distinctes :

```text
Framework error identity
CLI error category
Process exit code
```

Exemple :

```text
PTK-DECL-005
    ↓
invalid_schema
    ↓
exit 10
```

Le passage par la CLI ne doit jamais inventer un remplacement à une erreur `PTK-*` existante.

## 2. Catégories v1

```text
general_error
invalid_usage
invalid_schema
missing_optional_dependency
filesystem_error
unsupported_operation
internal_error
interrupted
broken_pipe
```

## 3. Exit codes v1

| Code | Nom |
|---:|---|
| 0 | SUCCESS |
| 1 | GENERAL_ERROR |
| 2 | INVALID_USAGE |
| 10 | INVALID_SCHEMA |
| 11 | MISSING_OPTIONAL_DEPENDENCY |
| 12 | FILESYSTEM_ERROR |
| 13 | UNSUPPORTED_OPERATION |
| 70 | INTERNAL_ERROR |
| 130 | INTERRUPTED |
| 141 | BROKEN_PIPE |

## 4. Sémantique

### 0 — SUCCESS

Réservé à une commande terminée avec succès.

### 1 — GENERAL_ERROR

Erreur publique connue sans catégorie plus précise. À utiliser avec parcimonie.

### 2 — INVALID_USAGE

Exemples :

```text
unknown command
unknown option
missing required argument
invalid enum
contradictory options
unknown engine ID
unknown contract ID
--force without --output
```

### 10 — INVALID_SCHEMA

Contenu Schema/YAML/SchemaCodec invalide après lecture réussie.

Les erreurs `PTK-DECL-*` appartiennent normalement à cette catégorie, sauf cas explicitement remappé.

### 11 — MISSING_OPTIONAL_DEPENDENCY

Exemples :

```text
Typer/Rich absent pour ptk
PyYAML absent pour une commande YAML
```

Cas spécial :

```text
PTK-DECL-010
→ preserve code
→ missing_optional_dependency
→ exit 11
```

### 12 — FILESYSTEM_ERROR

Exemples :

```text
missing file
directory instead of file
permission denied
missing output parent
destination exists without --force
replace/write failure
mutable symlink rejected
```

### 13 — UNSUPPORTED_OPERATION

Opération reconnue mais non supportée, par exemple source réseau explicitement rejetée ou capability connue indisponible.

Une valeur CLI inconnue telle que `--to xml` reste une erreur d'usage 2.

### 70 — INTERNAL_ERROR

Exception inattendue ou violation d'invariant. Aucun traceback par défaut ; `--debug` peut l'afficher sur stderr.

### 130 — INTERRUPTED

`KeyboardInterrupt` / Ctrl+C.

### 141 — BROKEN_PIPE

Consumer ayant fermé stdout prématurément. Aucun traceback bruyant. Le code 141 suit la convention SIGPIPE-like ; la portabilité de son mécanisme doit être testée.

## 5. CLIErrorReport

Modèle conceptuel :

```text
category
message
exit_code
code?
path?
hint?
details?
```

Le mapper doit préférer les types d'exception, codes PTK et attributs structurés. Le message-string matching est interdit comme mécanisme principal.

## 6. JSON error envelope

```json
{
  "contract_version": 1,
  "ok": false,
  "command": "schema.validate",
  "error": {
    "category": "invalid_schema",
    "code": "PTK-DECL-005",
    "message": "Unsupported type: money128",
    "path": "schema.yml"
  }
}
```

Champs requis : `category`, `message`.

Champs optionnels : `code`, `path`, `hint`, `details`.

## 7. Human errors

En mode humain :

```text
stdout = empty
stderr = controlled error
exit != 0
```

En mode report JSON :

```text
stdout = JSON error
stderr = empty normally
exit != 0
```

`--debug` peut utiliser stderr.

## 8. Payload failures

Les Payload Commands doivent laisser stdout vide en cas d'échec détecté avant émission. Aucun payload partiel ne doit être mélangé à un diagnostic.

## 9. Doctor

Une dépendance optionnelle manquante peut être un check `missing` sans échec process si l'installation reste fonctionnelle. Une violation d'invariant requise peut rendre la commande non-zero.

## 10. Internal architecture

Cible :

```text
cli/exit_codes.py
cli/models/errors.py
cli/exceptions.py
cli/rendering/errors.py
```

Les services ne doivent pas lever `SystemExit`; la conversion en code process appartient à la frontière commande/entrypoint.

## 11. Contract freeze

`contracts/cli_contract_v1.json` doit figer :

```text
exit_codes
error_categories
error envelope
critical mappings
```

Les contrats historiques d'erreurs 1.0/1.1 restent immuables.
