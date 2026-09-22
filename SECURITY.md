# Security Policy

PyTransformKit is pre-1.0 and does not yet publish a formal long-term support window.

## Reporting a vulnerability

Please avoid opening a public issue containing exploit details, credentials, tokens, private data, or other sensitive information.

Use GitHub's private vulnerability reporting mechanism for this repository when available, or contact the repository owner privately.

## Security principles

PyTransformKit must not expose secrets through exception messages, logs, diagnostics, lineage, audit payloads, or serialized connector specifications.

Third-party in-process plugins are trusted Python code and are not sandboxed by PyTransformKit.
