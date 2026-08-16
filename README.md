# File Organizer Agent

A privacy-first file organizer for macOS and Windows. It watches a folder you choose and sorts files into category folders in a destination you choose — deterministically, offline, and without ever deleting or overwriting anything. AI-assisted renaming and semantic sorting are optional, off by default, and require your approval before anything moves.

Full behavior is documented in [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md) (authoritative) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (how it's built). Current status lives in [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md).

## Status

Version 1 is under active development. macOS (Day 1) foundation is in place; Windows (Day 2) has not started. See the implementation plan for exact status per task.

## Why

Most "smart" file organizers either require a cloud account or quietly upload your files. This one works entirely offline by default: extension-based sorting needs no network access at all. AI is opt-in, per-action transparent about what leaves your device, and never acts without your explicit approval.

## Features

- Watches a source folder, sorts into category folders under a destination folder.
- Deterministic, case-insensitive extension matching, including compound extensions like `.tar.gz`.
- Unrecognized files go to `need_your_review/` — never guessed.
- Never deletes, never overwrites; safe duplicate naming (`report-2.pdf`).
- Dry-run mode to preview without moving anything.
- Optional AI: suggests a clearer filename and a semantic subfolder, with a reason and confidence score, and requires your approval for every action.
- Runs quietly in the menu bar / system tray; launch-at-login supported.

## Download

Pre-built macOS releases (`.app` and `.dmg`) are published under [GitHub Releases](https://github.com/lejiend7/file-organizer-agent/releases) — built automatically by CI on a real macOS runner (see Building, below). Windows builds will appear there once Day 2 work lands.

## Getting started (development)

```bash
git clone https://github.com/lejiend7/file-organizer-agent.git
cd file-organizer-agent
./scripts/dev_setup.sh
./scripts/run.sh
```

Run the test suite:

```bash
./scripts/test.sh
```

Copy `config.example.yaml` to see the default extension category mappings — the running app manages its own copy in the OS application-support directory (see `docs/PRODUCT_SPEC.md` §7), never beside the installed executable.

## Building

macOS builds must run on macOS; Windows builds must run on Windows (no cross-compilation). See `packaging/macos/` and `packaging/windows/`, and `scripts/build_macos_app.sh` / `scripts/build_windows_exe.sh` to build locally.

To cut an official release without needing local build tools, push a version tag (e.g. `git tag v0.1.0 && git push origin v0.1.0`) or run the "Release" workflow manually from the Actions tab. `.github/workflows/release.yml` builds the `.app` and `.dmg` on a macOS GitHub Actions runner, runs the full test suite as a release gate, and publishes both files to GitHub Releases. Code signing is optional — configure the `APPLE_SIGNING_IDENTITY`, `APPLE_CERTIFICATE_P12`, `APPLE_CERTIFICATE_PASSWORD`, and `KEYCHAIN_PASSWORD` repository secrets to sign; without them the build is still fully usable, just with a one-time Gatekeeper "right-click > Open" prompt.

## Contributing

Contributions are welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md), [`GOVERNANCE.md`](GOVERNANCE.md), and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). Lejiend, the founding maintainer, holds final authority over Version 1 scope, architecture, roadmap, PR approval, and releases. Ideas beyond Version 1 belong in [`ROADMAP.md`](ROADMAP.md), not silently added to the codebase.

Security issues: see [`SECURITY.md`](SECURITY.md). Privacy details: see [`PRIVACY.md`](PRIVACY.md).

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).
