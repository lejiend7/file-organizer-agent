# Privacy

File Organizer Agent is privacy-first by design.

## Local by default

With AI disabled (the default), the app never makes a network request. All file classification and moving happens on your device using deterministic, offline extension rules.

## What AI, if you enable it, can access

- Only files you enable AI for: items in `need_your_review/`, files you manually select, or broadly-categorized documents you've opted into semantic review.
- Only minimal extracted content (e.g. text from a PDF or document) — never the raw file itself, and never executables, scripts with credentials, private keys, certificates, password databases, `.env` files, encrypted/password-protected files, or oversized files.
- Every AI-analyzed file shows you, before any action is taken, whether its content left your device.

## What we never do

- No telemetry by default.
- No account or sign-up required to use the app.
- No credentials stored in plaintext, in the YAML config, or in logs — only in the OS keyring (macOS Keychain / Windows Credential Manager).
- No automatic deletion of files, ever.
- No AI action applied without your explicit, per-file approval.

## Your controls

- Disable AI entirely at any time (Settings).
- Remove stored AI credentials at any time (Settings).
- Change or revoke the selected source/destination folders at any time.
- Enable dry-run mode to preview behavior with nothing actually moved.

## Logs

Activity logs record what happened (file paths, categories, decisions, errors) for your own troubleshooting. Logs never contain extracted file content or credential values.
