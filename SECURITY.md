# Security policy

## Supported versions

Version 1.x receives security fixes once released. Pre-1.0 development builds are fixed on a best-effort basis.

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities. Instead, use GitHub's private vulnerability reporting (Security tab -> Report a vulnerability) on this repository, or contact the maintainer directly.

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce
- Affected version/commit

We aim to acknowledge reports within 5 business days.

## Scope

Particularly interested in reports involving:

- Path traversal or escape from the selected source/destination folders
- AI-recommended output bypassing `organizer/ai/validator.py`
- Credential storage or leakage (logs, config files, crash reports)
- Privilege escalation (this app should never need admin/root for normal operation)

## Out of scope

Denial of service via extremely large local file trees, and issues that require an already-compromised machine.
