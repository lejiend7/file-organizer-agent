# Architecture

Product behavior is defined in [`PRODUCT_SPEC.md`](PRODUCT_SPEC.md); this document explains how the system is built to deliver it.

## 1. Shared Python core

Everything under `organizer/core/`, `organizer/content/`, `organizer/ai/`, and `organizer/review/` is platform-agnostic and shared verbatim between macOS and Windows. It never imports `organizer/platforms/*` directly — platform behavior is injected in, not reached for.

```
organizer/core/
  watcher.py       filesystem monitoring (watchdog), debounced events
  classifier.py    deterministic extension -> category rules (YAML-driven)
  stability.py     waits until size/mtime stop changing before touching a file
  mover.py         safe move: create dirs, dedupe names, never overwrite/delete
  config.py        loads/saves YAML config + app-data paths (via adapter)
  logger.py        rotating logs; scrubs content/credentials before writing
  fingerprint.py   content hash cache to avoid re-processing unchanged files
organizer/content/  minimal text/metadata extraction for AI (PDF, TXT, MD, DOCX, images)
organizer/ai/       provider interface, mock/cloud providers, output validator
organizer/review/   review queue state + approval/reject/skip transitions
```

The core depends on an injected `PlatformAdapter` instance (see §2) for anything that differs by OS. It never checks `sys.platform` itself.

## 2. Platform adapters

`organizer/platforms/base.py` defines an abstract interface; `organizer/platforms/macos/` and `organizer/platforms/windows/` implement it. The core, UI, and tests only ever depend on the interface.

```python
class PlatformAdapter(Protocol):
    def app_data_dir(self) -> Path: ...
    def select_folder(self, title: str) -> Path | None: ...
    def store_credential(self, key: str, value: str) -> None: ...
    def get_credential(self, key: str) -> str | None: ...
    def delete_credential(self, key: str) -> None: ...
    def set_launch_at_login(self, enabled: bool) -> None: ...
    def notify(self, title: str, message: str) -> None: ...
    def validate_filename(self, name: str) -> bool: ...
```

Notes on specific adapters:
- **Folder selection** is implemented once, in `organizer/platforms/_pywebview_common.py`, using pywebview's own cross-platform file dialog (`window.create_file_dialog`) — since the UI toolkit itself is already cross-platform, there is no OS-specific dialog code to write. The macOS and Windows adapters both delegate to this shared implementation; the adapter *interface* still exists per-platform so the contract stays explicit and swappable (e.g. a future Linux adapter could use a native dialog instead).
- **Credential storage** uses `keyring`, which already targets macOS Keychain and Windows Credential Manager under one API — the adapters are thin wrappers that fix the service name.
- **Launch-at-login**: macOS via a `LaunchAgent` plist in `~/Library/LaunchAgents/`; Windows via a Registry `Run` key or Startup shortcut. Neither requires elevated privileges.
- **Filename validation**: macOS adapter rejects `:` and `/` and NUL; Windows adapter additionally rejects `< > : " / \ | ? *`, trailing dots/spaces, and the reserved device names in `PRODUCT_SPEC.md` §13.

## 3. File organization workflow

```
watcher detects file event
  -> stability.py waits for size/mtime to settle (skips locked/in-progress files)
  -> ignore rules applied (hidden, .DS_Store, sensitive, temp extensions, symlinks, dirs)
  -> fingerprint checked (skip if already processed and unchanged)
  -> classifier.py maps extension -> category (deterministic, YAML-configurable)
     -> recognized: mover.py moves to <destination>/<Category>/, deduping filename
     -> unrecognized or extensionless: mover.py moves to <destination>/need_your_review/
  -> logger.py records the outcome (never file content)
  -> fingerprint recorded
```

Dry-run mode runs the same pipeline but the final `mover.py` call becomes a no-op that only logs the *intended* action.

## 4. Optional AI workflow

AI never runs inline in the watcher loop — it only runs against files already at rest in `need_your_review/`, or files the user explicitly selects, and only when AI is enabled.

```
user enables AI (opt-in) + selects/queues a file
  -> content/ extracts minimal text (skips executables, keys, certs, encrypted/oversized files)
  -> ai/provider.suggest(extracted_content) -> raw JSON
  -> ai/validator.py validates the JSON against PRODUCT_SPEC.md §11
     (extension preserved, no absolute path, no traversal, inside destination,
      no reserved/invalid filename, safe length, no existing-file collision)
  -> invalid or confidence below threshold -> stays in need_your_review, not shown as actionable
  -> valid -> enqueued in review/ queue for human approval
  -> UI shows the popup described in PRODUCT_SPEC.md §14.1; only "Confirm transfer"
     invokes mover.py
```

The `ai/provider.py` interface (`suggest(content) -> RecommendationJSON`) has three implementations: `MockProvider` (tests, AI-disabled demos), and cloud/local providers contributed over time. The core only ever talks to the interface.

## 5. Security boundaries

- **Filesystem**: the app only ever reads inside the selected source and writes inside the selected destination (plus its own app-data config directory). No other path is touched. Path safety is enforced both when computing destinations locally and when validating AI-suggested destinations.
- **Process**: never requests admin/root. All adapters are written to work under a standard user account.
- **Credentials**: stored only via OS keyring, never in the YAML config, never in logs, never in git. `PRIVACY.md` documents this for end users.
- **AI content boundary**: nothing is sent to a cloud provider unless AI is explicitly enabled and the specific file is queued for review; the UI discloses this per-action, not just once at setup.
- **AI output boundary**: `ai/validator.py` is the sole gate between AI output and the filesystem. It is the one piece of code in the repo written defensively against a hostile/malformed provider, since AI output is untrusted input by definition (§11 of the spec).
- **Logging**: `logger.py` scrubs message content — it logs paths, categories, decisions, and errors, never extracted file text or credential values.

## 6. Packaging strategy

- **Runtime**: PyInstaller bundles the shared core, UI (pywebview + bundled HTML/CSS/JS), and platform adapter for the target OS into a single executable/app bundle. macOS and Windows builds are produced independently, each run on its own OS (`packaging/macos/`, `packaging/windows/`) — no cross-compilation.
- **macOS**: `.app` bundle, then packaged into a `.dmg`. Signing and notarization are optional and controlled entirely through environment variables (`APPLE_SIGNING_IDENTITY`, `APPLE_TEAM_ID`, etc.); nothing is hardcoded and no credential is ever committed.
- **Windows**: PyInstaller-built `.exe`, wrapped in an installer via Inno Setup (or an equivalent open-source installer) producing `File Organizer Agent Setup.exe`.
- **Config vs. install location**: packaging never writes user config beside the executable — the app always reads/writes `organizer/core/config.py`'s app-data path, which comes from the platform adapter (§7 of the spec).
