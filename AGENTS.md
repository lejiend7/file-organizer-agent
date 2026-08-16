# AGENTS.md

Instructions for coding agents (Claude, Copilot, or otherwise) working in this repository.

## Read before changing code

Before making any change, read these three files in full:

1. [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md) — authoritative source of truth for product behavior and Version 1 scope. If a change conflicts with this file, the change is wrong, not the file.
2. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — shared core, platform adapters, AI workflow, security boundaries, packaging.
3. [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) — current progress, what's done, what's pending, test status, known limitations.

## Non-negotiable rules

- One shared Python core (`organizer/core`, `organizer/content`, `organizer/ai`, `organizer/review`). Never fork it per platform.
- Platform-specific code only inside `organizer/platforms/{macos,windows}/`, behind the `organizer/platforms/base.py` adapter interface.
- Never delete files. Never overwrite files. Unknown or unsafe files go to `need_your_review/`.
- AI output is untrusted input — always validate before acting on it (see `organizer/ai/validator.py`).
- No AI action applies without explicit human approval in Version 1.
- No telemetry by default. No plaintext credentials. No hardcoded user paths.
- Add or update tests with any behavior change. Run `pytest` before calling work done.

## Project owner

Lejiend is the founding maintainer and holds final authority over scope, architecture, roadmap, PR approval, and releases. Community contributions follow [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`GOVERNANCE.md`](GOVERNANCE.md).
