# LOT-43 — PyTransformKit 1.1.0 Stable Release Review

> Stable target: `1.1.0`  
> Release-candidate baseline: `1.1.0rc2`  
> RC main commit: `5c6ae11bab3bc1c2cf37ffd0358b898bc6e32085`

LOT-43 is a promotion and qualification lot. It introduces no new Declarative
Schema feature, grammar rule, logical type, public API symbol, wire version or
error identity.

## Promotion decision

The `1.1.0rc2` line completed the full repository and declarative qualification
matrix on `main`, including installed wheel/sdist scenarios, documentation
execution, compatibility freezes and security boundaries.

The stable promotion is therefore limited to:

- stable version metadata;
- stable release manifest;
- stable release review and notes;
- artifact metadata validation;
- SHA-256 checksum evidence;
- final full-CI qualification.

## Frozen predecessor

PyTransformKit 1.1 is additive to the stable 1.0 contract.

The LOT-43 gate requires `contracts/stable_release_v1.json` to continue passing
unchanged. The 1.1 successor does not replace the 1.0 evidence.

## Frozen 1.1 surface

The stable gate rejects drift in:

```text
V1 public API baseline
V1 root exports
V1 legacy compatibility names
official engine IDs
wire contract IDs and versions

pytransformkit.schema_io exports
8 schema_io signatures
yaml stable runtime extra
PTK-DECL-000 → PTK-DECL-013
declarative exception hierarchy
SchemaCodec wire identity
```

## Artifact qualification

The release contract requires:

```text
wheel                                    PASS
sdist                                    PASS
twine check equivalent                   PASS
core clean install                       PASS
yaml-extra install                       PASS
SHA-256 checksum record                  PASS
Python 3.11                              PASS
Python 3.12                              PASS
Python 3.13                              PASS
Python 3.14                              PASS
```

The checksum record is generated from the built stable artifacts as
`stable-artifact-sha256.txt` and retained as a CI artifact.

## Release boundary

The repository can fully qualify the stable source and package artifacts before
publication. External publication consists of:

1. create tag `v1.1.0` on the qualified stable commit;
2. publish a GitHub Release using `RELEASE_NOTES_1_1_0.md`;
3. allow `.github/workflows/publish-pypi.yml` to build and publish through
   PyPI Trusted Publishing;
4. retain the published distribution hashes.

No publication is claimed by this review until those external release actions
actually complete.
