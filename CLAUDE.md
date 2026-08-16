@AGENTS.md

## Claude-specific notes

- When editing `organizer/core/*`, run `pytest tests/ -k core` afterward and report results before finishing.
- Never place `if platform == "windows"` / macOS-specific branches inside `organizer/core`, `organizer/content`, `organizer/ai`, or `organizer/review`. If a change seems to need that, it belongs in `organizer/platforms/` behind the adapter interface instead.
- When asked to add a feature, check `docs/PRODUCT_SPEC.md` first — if it's not in Version 1 scope, propose adding it to `ROADMAP.md` instead of implementing it.
