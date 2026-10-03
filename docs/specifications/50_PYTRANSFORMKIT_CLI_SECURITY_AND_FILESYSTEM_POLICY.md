# PyTransformKit — CLI Security and Filesystem Policy

## 1. Objet

Ce document définit la politique de sécurité et de filesystem de la Developer CLI PyTransformKit 1.2.

Principe :

```text
The CLI must not widen PyTransformKit authority.
```

## 2. Principes

```text
Explicit paths only.
Explicit writes only.
No implicit network.
No arbitrary code execution.
No implicit environment expansion.
No implicit plugin activation.
No recursive discovery in 1.2.
No silent overwrite.
Prefer atomic replacement.
Preserve framework security boundaries.
Fail closed on ambiguity.
```

## 3. Trust boundary

Sont non fiables :

```text
CLI arguments
option values
paths
file contents
YAML / JSON
environment configuration
terminal content
filesystem state
```

Ils doivent rester des données et ne pas devenir implicitement code, shell command, URL loader, plugin import ou template.

## 4. Scope filesystem

Seul le filesystem local est supporté pour les commandes Schema.

Sont hors contrat 1.2 :

```text
HTTP/HTTPS
S3
GCS
Azure Blob
FTP
SSH
remote SMB
custom URI loaders
```

## 5. Explicit local files

Une commande attend un fichier explicitement fourni.

Un directory n'est jamais transformé en scan récursif. Aucun `pytransformkit.yml`, workspace root ou project root n'est découvert.

## 6. Read-only commands

```text
ptk version
ptk doctor
ptk schema validate
ptk schema inspect
ptk engines list
ptk engines inspect
ptk contract inspect
```

ne modifient pas les fichiers métier utilisateur.

## 7. Explicit write commands

```text
ptk schema format PATH --write
ptk schema convert INPUT --output OUTPUT
```

sont les seules mutations métier prévues.

Sans option d'écriture, aucun fichier n'est modifié.

## 8. Overwrite

`schema convert --output` refuse une destination existante par défaut.

`--force` autorise uniquement l'overwrite de la destination explicitement spécifiée.

`--force` sans `--output` est une erreur d'usage.

## 9. Atomic writes

Pour les remplacements :

```text
compute complete payload
→ validate
→ create temporary sibling
→ write fully
→ flush
→ close
→ os.replace / equivalent
```

Le fichier temporaire doit idéalement être dans `destination.parent` afin de rester sur le même filesystem.

Le fichier final ne doit pas être tronqué avant que le payload complet soit prêt.

## 10. Commit point

Le succès du remplacement atomique est le commit point filesystem.

Avant ce point, l'original reste autoritaire. Après succès, aucun rollback implicite non fiable n'est tenté.

## 11. Temporary files

Utiliser des primitives stdlib sûres (`tempfile`). Les noms ne doivent pas être prédictibles. Le cleanup est tenté sur succès, erreur connue et interruption.

## 12. Permissions

Ne pas élargir les permissions. Un nouveau fichier respecte les defaults OS/umask. Un remplacement doit éviter de rendre le fichier plus permissif.

Aucun chmod/chown/élévation de privilège automatique.

## 13. Symlinks

Lecture via symlink : autorisée selon le comportement standard.

Écriture via symlink : rejetée par défaut.

`--force` ne signifie pas « suivre un symlink arbitraire ».

## 14. Path traversal

La CLI n'est pas un sandbox : un utilisateur peut explicitement passer `../file.yml` ou un chemin absolu selon ses permissions.

En revanche, un document lu ne peut pas provoquer une lecture secondaire implicite.

## 15. No includes

Aucun mécanisme `include`, tag YAML de lecture fichier ou référence externe n'est ajouté par la CLI.

## 16. Declarative security inheritance

La CLI doit conserver :

```text
SafeLoader-based parsing
alias amplification protection
no arbitrary constructors
no implicit file reads
no URL fetching
no env expansion
unknown types fail closed
no plugin import during parsing
```

Toutes les commandes YAML passent par `schema_io`.

## 17. No arbitrary deserialization

Interdits pour des données non fiables :

```text
eval
exec
pickle
unsafe YAML constructors
dynamic import from payload content
```

SchemaCodec reste basé sur un registre sémantique fermé.

## 18. Remote resources

Une entrée `https://...`, `s3://...`, etc. doit être rejetée explicitement et ne déclencher aucune requête.

`ptk doctor` est également offline et n'effectue aucun update check.

## 19. Environment

La CLI peut lire des métadonnées locales nécessaires (version Python, package metadata, TTY, NO_COLOR) mais ne doit jamais dumper l'environnement complet.

Aucune expansion `os.path.expandvars` n'est appliquée au contenu YAML ou aux paths CLI par défaut.

## 20. Shell

Les opérations CLI 1.2 ne nécessitent pas de `shell=True` ni de commandes externes `cat`, `cp`, `mv`, `sed`, etc.

## 21. Plugins

Discovery metadata ≠ activation.

`--help`, `doctor`, `engines list` et parsing Schema ne doivent pas activer automatiquement des plugins tiers.

Aucun plugin ne peut injecter des commandes dans `ptk` en 1.2.

## 22. Secrets

Ne pas afficher l'environnement ou les objets complets.

Les diagnostics doivent redacter les champs sensibles tels que :

```text
password
passwd
token
secret
api_key
authorization
credential
private_key
client_secret
```

`--debug` ne désactive pas la redaction.

## 23. Encoding

Les formats texte utilisent UTF-8. Les sorties canoniques sont sans BOM. La CLI ne modifie pas arbitrairement la politique de newline définie par les emitters canoniques.

## 24. Resource protections

La CLI ne contourne pas les protections du parser/codec contre :

```text
oversized payload
deep nesting
alias amplification
invalid semantic tags
```

## 25. Source format ambiguity

`schema convert` infère seulement `.yml`, `.yaml`, `.json`. Une extension inconnue sans `--from` échoue ; aucune stratégie « try YAML then JSON » silencieuse.

## 26. Input/output collision

`schema convert INPUT --output INPUT` est rejeté comme `INVALID_USAGE` / exit 2.

L'in-place réservé est `schema format --write`.

## 27. TOCTOU

Préférer les primitives atomiques/exclusives aux longues séquences `exists() → later open()`. Pour un output nouveau sans `--force`, une création exclusive est préférable.

## 28. Directories

Une destination dont le parent n'existe pas échoue. La CLI ne fait pas de `mkdir -p` implicite.

## 29. File types

Les commandes Schema ciblent des fichiers réguliers. FIFO, sockets, device files et stdin `-` sont hors scope initial.

## 30. Interruptions

Sur `KeyboardInterrupt` avant commit :

```text
cleanup temp attempted
final destination not replaced with partial content
exit 130
```

Broken pipe : pas de traceback bruyante, exit 141 selon le modèle.

## 31. No hidden state

La CLI 1.2 n'a pas besoin de cache global, config persistante ou écriture dans site-packages.

## 32. Threat model

Les tests doivent couvrir :

```text
arbitrary code execution
implicit file disclosure
SSRF / remote loading
environment secret expansion
plugin execution
destructive overwrite
partial write
symlink redirection
parser resource exhaustion
diagnostic secret leak
command injection
TOCTOU
```

## 33. Error mapping

| Situation | Catégorie | Exit |
|---|---|---:|
| missing file | filesystem_error | 12 |
| directory input | filesystem_error | 12 |
| permission denied | filesystem_error | 12 |
| output exists without force | filesystem_error | 12 |
| mutable symlink | filesystem_error | 12 |
| write/replace failure | filesystem_error | 12 |
| recognized remote URI | unsupported_operation | 13 |
| force without output | invalid_usage | 2 |
| convert input == output | invalid_usage | 2 |

## 34. Stable guarantees

Le futur `contracts/cli_contract_v1.json` doit pouvoir figer :

```text
remote_sources = false
recursive_discovery = false
implicit_overwrite = false
format_write_requires_flag = true
convert_output_requires_path = true
convert_overwrite_requires_force = true
mutable_symlinks = false
```

Règle finale :

```text
Read only what the user explicitly names.
Write only what the user explicitly authorizes.
Never execute what should only be data.

Validate first.
Write completely.
Commit atomically.
Fail closed.
```
