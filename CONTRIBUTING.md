# Contributing to File Organizer Agent

Thanks for considering a contribution. Please read [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) first — they're the source of truth for what this project does and how it's built. See [`GOVERNANCE.md`](GOVERNANCE.md) for who decides what.

## Ground rules

- One shared Python core. Never fork organizer logic per platform — use `organizer/platforms/` adapters.
- Never delete or overwrite user files. Never add a fully-automatic AI action. Never add telemetry that's on by default.
- If your idea isn't in Version 1 scope (`docs/PRODUCT_SPEC.md` §17), propose it in `ROADMAP.md` first rather than implementing it directly.

## Developer Certificate of Origin

We use a lightweight DCO instead of a CLA. By submitting a pull request, you certify that you wrote the contribution or otherwise have the right to submit it under this project's license (Apache 2.0). Sign off your commits:

```
git commit -s -m "your message"
```

This adds a `Signed-off-by: Your Name <email>` line to your commit.

## Workflow

1. Fork the repo, create a feature branch off `main` (e.g. `feature/windows-platform-adapter`, `fix/duplicate-file-handling`).
2. Use [Conventional Commits](https://www.conventionalcommits.org/) where practical (`feat:`, `fix:`, `docs:`, `test:`).
3. Add or update tests with any behavior change (`pytest tests/`).
4. Open a pull request against `main` using the PR template. Automated tests must pass.
5. A maintainer reviews and approves before merge — only maintainers merge to `main` or cut releases.

## Setting up locally

```bash
./scripts/dev_setup.sh
./scripts/test.sh
```

## Adding an AI provider

Implement the `AIProvider` interface in `organizer/ai/provider.py` — see `organizer/ai/mock_provider.py` for the minimal shape. Your provider's output still passes through `organizer/ai/validator.py`; you don't get to skip validation.

## Reporting bugs / suggesting features

Use the issue templates under `.github/ISSUE_TEMPLATE/`.
