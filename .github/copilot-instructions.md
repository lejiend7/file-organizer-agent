# GitHub Copilot instructions

Follow [`AGENTS.md`](../AGENTS.md) at the repository root.

Treat [`docs/PRODUCT_SPEC.md`](../docs/PRODUCT_SPEC.md) as the authoritative source of truth for product behavior and Version 1 scope. Do not suggest features, files, or behavior that contradicts it.

Before suggesting changes to organizer logic, read [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) (shared core vs. platform adapters) and [`docs/IMPLEMENTATION_PLAN.md`](../docs/IMPLEMENTATION_PLAN.md) (current status).

Key constraints Copilot suggestions must respect:
- Never suggest code that deletes or overwrites files.
- Never suggest platform-specific logic inside `organizer/core`, `organizer/content`, `organizer/ai`, or `organizer/review`.
- Never suggest hardcoded credentials, telemetry calls, or fully-automatic AI file actions.
