# Implementation plan

Tracks progress against [`PRODUCT_SPEC.md`](PRODUCT_SPEC.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md). Updated as work lands — this file, not chat history or commit messages, is the status source of truth.

_Last updated: 2026-08-17._

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
| 16 | `.app` build script | fixed (had a path bug — see below), builds locally unverified on real macOS |
| 17 | DMG build script | fixed (same path bug), builds locally unverified on real macOS |
| 18 | CI workflow (`macos-latest` + `windows-latest`) | done — `.github/workflows/ci.yml` |
| 19 | Release workflow (build + publish to GitHub Releases) | done — `.github/workflows/release.yml`, unverified until first tag push |

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

## Completed in a follow-up session (CI/release)

- Fixed a real bug in all four `scripts/build_*.sh` scripts: each `cd`'d up two directories instead of one, which would have made every packaging build fail immediately (they ran fine as standalone scripts because `set -euo pipefail` masked the failure as "directory doesn't exist" rather than a loud error — caught by tracing the path manually before wiring these into CI).
- `.github/workflows/ci.yml` — runs `pytest tests/` on both `macos-latest` and `windows-latest` on every push/PR to `main`, per the spec's CI requirement.
- `.github/workflows/release.yml` — the actual way to get a real `.app`/`.dmg` without local macOS build tools: triggered by pushing a `vX.Y.Z` tag (or manual dispatch), it runs on a real `macos-latest` GitHub Actions runner, runs the full test suite as a release gate, builds the app and DMG via the existing scripts, optionally code-signs if `APPLE_SIGNING_IDENTITY` + certificate secrets are configured, and publishes both the `.dmg` and a zipped `.app` to GitHub Releases.
- README updated with a Download section pointing at GitHub Releases and instructions for cutting a release via tag push.

## Completed in a second follow-up (release workflow fix)

- The first real tag push (`v1.0.0`) confirmed the prediction below: `.github/workflows/release.yml` failed both times it ran, with "Invalid workflow file... Unrecognized named-value: 'secrets'" — GitHub Actions does not allow the `secrets` context directly inside a step's `if:` condition. Fixed by surfacing it through a job-level `env: HAS_SIGNING_CERT` first and checking that instead (the documented workaround). Confirmed via `python -c "import yaml; yaml.safe_load(...)"` that the file is at least syntactically valid now; full end-to-end verification still needs a real run.
- Because the release still failed validation, no GitHub Release was ever created for `v1.0.0` — GitHub's UI fell back to showing the tag with its default auto-generated `Source code (zip)`/`Source code (tar.gz)` archives, which is not the same thing as a published Release with our `.dmg` attached. Once this fix lands and the tag is recreated, `softprops/action-gh-release` will create the actual Release with `File Organizer Agent.dmg` (the real drag-to-Applications installer) and a zipped `.app` attached.

## Pending / known limitations

- **The release workflow's build steps (PyInstaller onward) are still unverified** — the two real runs so far both failed at workflow-validation time, before any build step executed. The next tag push is the first real test of the actual build. If PyInstaller needs an extra `--hidden-import` or `--collect-all` for pywebview/pystray on a real Mac runner, that'll surface there and need a follow-up fix.
- **Windows work has not started** (Day 2, item-by-item above) — Day 1 must be verified on real macOS hardware first, per the working process in the project instructions. The release workflow does not yet have a Windows job.
- **Notarization/signing** wired to environment variables and repository secrets but untested (no Apple credentials available in any environment used so far).
- **Cloud AI provider** is not implemented — only `MockProvider` exists, which is sufficient for offline development and tests but not for real AI recommendations yet. A real provider is a good first external contribution (see `CONTRIBUTING.md`).
- **Content extractors** (`organizer/content/`) currently handle TXT/MD directly; PDF/DOCX/image extraction are stubbed with clear `NotImplementedError` messages, not silently faked.
- Manual verification still needed: running the actual `.app` and confirming Keychain prompts, launch-at-login behavior, and notifications on real macOS.
- I (the coding agent) have no GitHub push or Actions access from either the original Linux sandbox or this follow-up session — everything above was committed locally only. A human needs to push the branch/tag to actually trigger CI and the release build.

## Test status

Ran in this session's Linux sandbox: `pytest tests/ -v`

```
73 passed in 1.18s
```

Coverage by file: `test_classifier.py` (8), `test_mover.py` (16 — safety/ignore rules), `test_stability.py` (5), `test_fingerprint.py` (4), `test_pipeline.py` (9), `test_watcher.py` (2, including an end-to-end drop-a-file-and-watch-it-move test), `test_ai_validator.py` (14 — malformed JSON, path traversal, reserved names, invalid characters, length limits, overwrite prevention, confidence gating), `test_mock_provider.py` (4), `test_review_queue.py` (7 — approve/reject/skip, edited overrides, escape-attempt rejection, persistence), `test_config.py` (4).

Not run in this environment (no display / no macOS): `organizer.ui.*` (pywebview window), `organizer.platforms.macos.adapter` (Keychain/LaunchAgent/osascript calls — these require an actual macOS session to verify). These are the manual-verification items below, not test gaps to close in code.

Also verified manually this session: `organizer.core.*`, `organizer.ai.*`, and `organizer.review.*` import cleanly with zero network calls (confirms offline operation with AI disabled), and `config.example.yaml` parses as valid YAML.
