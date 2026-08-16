# macOS packaging

Run from a Mac, from the repo root:

```bash
./scripts/build_macos_app.sh   # -> dist/File Organizer Agent.app
./scripts/build_macos_dmg.sh   # -> dist/File Organizer Agent.dmg
```

Signing/notarization are optional and controlled via environment variables
(`APPLE_SIGNING_IDENTITY`, `APPLE_TEAM_ID`, `APPLE_NOTARIZE`). Never commit
signing credentials - see `SECURITY.md`.
