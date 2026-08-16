# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/), versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Project documentation set (`AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION_PLAN.md`, `.github/copilot-instructions.md`) and governance files.
- Shared Python core: extension classifier, safe mover, stability detector, config manager, rotating logger, fingerprint cache, filesystem watcher.
- AI provider interface, mock provider, output validator, review queue.
- macOS platform adapter (paths, folder selection, Keychain credentials, launch-at-login, notifications).
- pywebview-based desktop UI: dashboard, review queue, AI approval popup, settings, extension rules editor, onboarding.
- Pytest suite for core safety behavior.
- Dev/test/build scripts.
- CI workflow running tests on `macos-latest` and `windows-latest`.
- Release workflow: builds the `.app`/`.dmg` on a macOS GitHub Actions runner and publishes to GitHub Releases on tag push, with optional code signing via repository secrets.

### Fixed

- All four `scripts/build_*.sh` packaging scripts `cd`'d to the wrong directory (one level too high), which would have broken every local and CI build.

Nothing has been released yet — this is pre-1.0 development.
