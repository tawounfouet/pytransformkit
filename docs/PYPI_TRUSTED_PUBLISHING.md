# PyPI Trusted Publishing

PyTransformKit uses PyPI Trusted Publishing for future releases.

Trusted Publishing replaces static PyPI API tokens with short-lived OpenID Connect
(OIDC) credentials issued to the GitHub Actions release workflow.

## GitHub workflow identity

Configure the PyPI project publisher with exactly:

```text
Owner: tawounfouet
Repository: pytransformkit
Workflow name: publish-pypi.yml
Environment name: pypi
```

PyPI project publishing settings:

```text
https://pypi.org/manage/project/pytransformkit/settings/publishing/
```

## Workflow

The publisher workflow is:

```text
.github/workflows/publish-pypi.yml
```

It runs only when a GitHub Release is published.

The workflow deliberately separates:

```text
Build job
  ↓
wheel + sdist validation
  ↓
GitHub Actions artifact
  ↓
Publish job (environment: pypi)
  ↓
OIDC / PyPI Trusted Publishing
```

The build job has no OIDC permission.

Only the publish job receives:

```yaml
permissions:
  id-token: write
  contents: read
```

No PyPI username, password, or API token is stored in the repository.

## Release identity gate

Before building, the workflow verifies that the GitHub Release tag exactly matches
the package version in `pyproject.toml`.

For example:

```text
pyproject.toml version = 1.1.0
GitHub Release tag     = v1.1.0
```

Any mismatch fails before publication.

## Distribution validation

Before publication the workflow:

1. checks out the released tag;
2. builds wheel and sdist with `python -m build`;
3. runs `python -m twine check dist/*`;
4. verifies that both wheel and source distribution exist;
5. transfers only the built `dist/` files to the privileged publish job.

## Digital attestations

The official `pypa/gh-action-pypi-publish` Trusted Publishing flow generates and
uploads digital attestations by default.

These attestations use the GitHub OIDC identity and Sigstore, tying published
distribution files to the release workflow identity.

## PyPI setup

In PyPI, add a GitHub publisher under the `pytransformkit` project and use the
exact workflow identity above.

The workflow file can exist before the publisher is registered. Publication will
only succeed after PyPI trusts that identity.

## Recommended GitHub environment

Create the `pypi` environment under:

```text
Repository Settings
→ Environments
→ New environment
→ pypi
```

Optionally add deployment protection rules or required reviewers for an additional
human approval gate before PyPI publication.

## Release sequence

For future stable releases:

```text
qualify release commit
    ↓
tag release commit
    ↓
publish GitHub Release
    ↓
publish-pypi.yml
    ↓
build + validate
    ↓
OIDC authentication
    ↓
PyPI publication + attestations
```

PyTransformKit `1.0.0` was published manually before this Trusted Publishing
workflow was introduced. Future releases should use the OIDC workflow.
