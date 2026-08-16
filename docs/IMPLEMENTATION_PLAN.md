# Implementation plan

Tracks progress against [`PRODUCT_SPEC.md`](PRODUCT_SPEC.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md). Updated as work lands — this file, not chat history or commit messages, is the status source of truth.

_Last updated: 2026-08-16._

## Day 1 — macOS foundation (shared core built here)

| # | Task | Status |
|---|---|---|
| 1 | Shared Python core scaffold | done |
| 2 | Extension classification | done |
| 3 | `need_your_review` handling | done |
| 4 | Safe folder creation | done |
| 5 | Safe movement (no delete/overwrite) | done |
| 6 | Duplicate handling | done |
| 7 | Dry-run mode | done |
| 8 | Logging (rotating, content-scrubbed) | done |
| 9 | macOS platform adapter | done |
| 10 | Folder selection (pywebview dialog) | done |
| 11 | Background monitoring (watcher loop) | done |
| 12 | Launch-at-login (LaunchAgent) | done |
| 13 | macOS Keychain integration (via `keyring`) | done |
| 14 | Initial AI review flow (mock provider + validator + queue) | done |
| 15 | Core tests | done |
| 16 | `.app` build script | scripted, unrun (needs macOS) |
| 17 | DMG build script | scripted, unrun (needs macOS) |

## Day 2 — Windows (begins directly after Day 1, same core)

| # | Task | Status |
|---|---|---|
| 1 | Windows platform adapter | pending |
| 2 | Windows paths | pending |
| 3 | Windows folder selection | pending (reuses shared pywebview dialog) |
| 4 | Windows filename validation | pending |
| 5 | Locked-file handling | pending (stability.py is shared; needs Windows-specific test coverage) |
| 6 | Windows Credential Manager integration | pending (reuses shared `keyring` wrapper) |
| 7 | Launch-at-login | pending |
| 8 | Background monitoring | pending (watcher is shared; needs Windows test run) |
| 9 | Windows application build | pending |
| 10 | Windows installer build | pending |
| 11 | Windows-specific tests | pending |
| 12 | Cross-platform regression tests | pending |

## Completed this session

- Full documentation set (`AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION_PLAN.md`, `.github/copilot-instructions.md`) plus governance files.
- Repo scaffold matching the recommended structure, `pyproject.toml`, `config.example.yaml`.
- Shared core: `classifier.py`, `config.py`, `stability.py`, `mover.py`, `logger.py`, `fingerprint.py`, `watcher.py`.
- AI layer: `ai/provider.py` interface, `ai/mock_provider.py`, `ai/validator.py`, `review/queue.py`.
- macOS platform adapter (`organizer/platforms/macos/`) and shared adapter base/interface.
- pywebview UI shell implementing the designed screens: dashboard, review queue + approval popup, settings, extension rules, onboarding.
- Pytest suite covering classifier, mover safety, stability, AI validator, review queue.
- Dev scripts: setup, run, test, clean.

## Pending / known limitations

- **macOS `.app` and DMG were not built or run** — this session ran in a Linux sandbox; per the spec, macOS builds must run on macOS. `scripts/build_macos_app.sh` and `scripts/build_macos_dmg.sh` are written but unverified. Someone with a Mac needs to run them and report back.
- **Windows work has not started** (Day 2, item-by-item above) — Day 1 must be verified on real macOS hardware first, per the working process in the project instructions.
- **Notarization/signing** wired to environment variables but untested (no Apple credentials available in this environment).
- **Cloud AI provider** is not implemented — only `MockProvider` exists, which is sufficient for offline development and tests but not for real AI recommendations yet. A real provider is a good first external contribution (see `CONTRIBUTING.md`).
- **CI workflows** (`.github/workflows/`) are not yet written — planned next, targeting `macos-latest` and `windows-latest` runners per the spec.
- **Content extractors** (`organizer/content/`) currently handle TXT/MD directly; PDF/DOCX/image extraction are stubbed with clear `NotImplementedError` messages, not silently faked.
- Manual verification still needed: running the actual `.app` and confirming Keychain prompts, launch-at-login behavior, and notifications on real macOS.

## Test status

Ran in this session's Linux sandbox: `pytest tests/ -v`

```
73 passed in 1.18s
```

Coverage by file: `test_classifier.py` (8), `test_mover.py` (16 — safety/ignore rules), `test_stability.py` (5), `test_fingerprint.py` (4), `test_pipeline.py` (9), `test_watcher.py` (2, including an end-to-end drop-a-file-and-watch-it-move test), `test_ai_validator.py` (14 — malformed JSON, path traversal, reserved names, invalid characters, length limits, overwrite prevention, confidence gating), `test_mock_provider.py` (4), `test_review_queue.py` (7 — approve/reject/skip, edited overrides, escape-attempt rejection, persistence), `test_config.py` (4).

Not run in this environment (no display / no macOS): `organizer.ui.*` (pywebview window), `organizer.platforms.macos.adapter` (Keychain/LaunchAgent/osascript calls — these require an actual macOS session to verify). These are the manual-verification items below, not test gaps to close in code.

Also verified manually this session: `organizer.core.*`, `organizer.ai.*`, and `organizer.review.*` import cleanly with zero network calls (confirms offline operation with AI disabled), and `config.example.yaml` parses as valid YAML.
