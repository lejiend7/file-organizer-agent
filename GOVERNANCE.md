# Governance

File Organizer Agent uses a **maintainer-led governance model**.

## Lejiend (founding maintainer)

Lejiend created this project and retains final authority over:

- Product scope
- Architecture
- Roadmap
- Maintainer appointments
- Pull request approval
- Official releases

## Contributors can

- Report bugs
- Suggest features
- Improve documentation
- Submit pull requests
- Add extension mappings
- Add AI provider adapters
- Improve macOS or Windows support
- Propose future Linux support (see `ROADMAP.md`)

## Decision process

Major changes (new architecture, new Version 1 scope, new dependencies, new AI providers shipped by default) require discussion in an issue before implementation, and maintainer approval before merge. Small, clearly-scoped fixes can go straight to a pull request.

## Branch protection

`main` is protected from direct community pushes. All changes land via pull request, with automated tests passing, and maintainer review.
