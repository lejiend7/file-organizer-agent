# Product specification — File Organizer Agent

This document is the **authoritative source of truth** for product behavior and Version 1 scope. If any other document, comment, or code path disagrees with this file, this file wins. Do not copy a conflicting version of this spec into another file — link back here instead.

Founding maintainer and product owner: **Lejiend**. Lejiend retains final authority over Version 1 scope, architecture, roadmap, pull request approval, and official releases. See [`GOVERNANCE.md`](../GOVERNANCE.md).

## 1. Product goal

Monitor a user-selected source folder and automatically organize files into category folders under a user-selected destination — locally, privately, and safely by default.

## 2. Platforms and build order

- **macOS is built first (Day 1)**, on a single shared Python core.
- **Windows begins directly on Day 2**, reusing the same core — no separate implementation.
- Linux is out of scope for Version 1 (see [`ROADMAP.md`](../ROADMAP.md)).

## 3. Core behavior

The organizer must:

- Work completely locally without AI.
- Detect extensions using deterministic, case-insensitive rules, including compound extensions such as `.tar.gz`.
- Create missing category folders (only inside the selected destination).
- Move files safely — never copy-then-delete in a way that risks data loss.
- **Never delete files.**
- **Never overwrite files.**
- Send unrecognized or extensionless files to `need_your_review/`. Never guess a category for an unrecognized extension.
- Optionally use AI to understand file content, propose a clearer filename, and recommend a more meaningful destination.
- Require explicit user approval before any AI-recommended rename or move is applied.

### Example

| | |
|---|---|
| Original | `invoice_scan_001.pdf` |
| Extension-based result | `Documents/invoice_scan_001.pdf` |
| Optional AI recommendation | `Documents/Finance/Invoices/AWS-Invoice-2026-08.pdf` |

Every AI recommendation carries a reason and a confidence score, shown to the user before approval.

## 4. Core technology

- Python 3, type-hinted, modular.
- `watchdog` for filesystem monitoring.
- `pathlib` for paths, `shutil` for safe moves.
- YAML for extension configuration (user-editable, no code changes required).
- Rotating Python logs.
- A secure cross-platform keyring abstraction (macOS Keychain / Windows Credential Manager).
- PyInstaller for packaging.
- Pytest for testing.
- Dependencies kept minimal and well-maintained.

## 5. Shared cross-platform architecture (summary)

Shared: file watcher, extension classifier, file stability detector, safe mover, duplicate filename handler, configuration manager, logger, file fingerprint cache, content extractors, AI provider interface, AI recommendation validator, review queue, tests.

Platform-specific via adapters only: application data paths, folder selection, permissions, secure credential storage, launch-at-login, notifications, background operation, filename validation, packaging.

Full detail in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## 6. Extension categories

Matching is deterministic, case-insensitive, and supports compound extensions.

| Category | Extensions |
|---|---|
| Images | `.jpg` `.jpeg` `.png` `.gif` `.webp` `.svg` `.heic` `.tiff` `.bmp` |
| Documents | `.pdf` `.doc` `.docx` `.txt` `.md` `.rtf` `.pages` `.epub` |
| Spreadsheets | `.csv` `.xls` `.xlsx` `.numbers` `.ods` |
| Presentations | `.ppt` `.pptx` `.key` `.odp` |
| Videos | `.mp4` `.mov` `.avi` `.mkv` `.webm` `.m4v` |
| Audio | `.mp3` `.wav` `.aac` `.m4a` `.flac` `.ogg` |
| Archives | `.zip` `.rar` `.7z` `.tar` `.tar.gz` `.gz` `.bz2` |
| Code | `.js` `.jsx` `.ts` `.tsx` `.py` `.java` `.php` `.html` `.css` `.scss` `.json` `.xml` `.yaml` `.yml` `.sh` `.sql` `.go` `.rs` `.swift` |
| Installers | `.dmg` `.pkg` `.exe` `.msi` |
| Need your review | anything unrecognized, or files without an extension |

> Note: the source instruction listed the Documents extension as `.pdfpdf`; this is treated as a typo for `.pdf` and corrected here to avoid shipping a non-functional rule. `config.example.yaml` uses `.pdf`.

Users can change extension mappings entirely through YAML configuration (see the Extension rules editor in the UI). Never ask AI to detect a normal file extension; never guess the extension category.

## 7. Folder permissions

The user selects a source folder and a destination folder. The app may only create category folders and approved subfolders inside the selected destination.

Requirements:
- Request minimum required access; never scan unrelated folders.
- Never require administrator or root access for normal operation.
- Validate that both paths exist and are writable.
- Prevent recursive organization loops.
- Warn if the destination is inside the source (user may proceed after acknowledging).
- Let users change or revoke selected folders at any time.

Config storage locations (never beside the installed executable):
- macOS: `~/Library/Application Support/File Organizer Agent/`
- Windows: `%APPDATA%\File Organizer Agent\`

## 8. Safe file handling

Safety outranks speed.

- Never delete. Never overwrite.
- Ignore directories and symbolic links.
- Ignore hidden and system files, and `.DS_Store`.
- Ignore sensitive files: `.env`, private keys, certificates, credential files.
- Ignore temporary files: `.crdownload`, `.download`, `.part`, `.tmp`.
- Wait until file size and modification time are stable before acting.
- Handle files locked by another application without crashing or corrupting state.
- Avoid organizing the same file twice (fingerprint cache).
- Prevent recursive movements.
- Duplicate destination names get safe suffixes, e.g. `report-2.pdf`.
- Support dry-run mode (simulate, log, don't move).
- Log movements, skipped files, errors, and approved AI actions.
- **Never log extracted file content, API keys, or credentials.**

## 9. Optional AI content understanding

- Disabled by default. The organizer works fully offline when AI is disabled.
- AI may only: understand file content, suggest a clearer filename, recommend a semantic subfolder, explain the recommendation, return a confidence score.
- AI is not run on every file automatically. Prioritized for: files in `need_your_review`, files the user manually selects, and broadly-categorized documents where semantic organization helps.
- Supported initial content analysis: PDF, TXT, Markdown, DOCX, supported images, scanned documents via a vision-capable provider.
- Never analyze or upload: executables, scripts containing credentials, private keys, certificates, password databases, environment files, encrypted or password-protected files, unsupported archives, or excessively large files.
- Extract only the minimum content required for the recommendation.
- Use a local fingerprint to avoid repeatedly analyzing an unchanged file.

## 10. AI provider architecture

- AI providers are decoupled from the organizer core via an interface, so contributors can add cloud providers, local models, or mock providers for tests. The core is never permanently tied to one provider.
- Cloud AI requires: explicit user opt-in, a clear notice that content may leave the device, secure credential storage, no plaintext API keys, no telemetry by default, an option to disable AI entirely, and an option to remove stored credentials.
- Credential storage: macOS Keychain on macOS, Windows Credential Manager on Windows.
- Credentials are never committed to git.

## 11. AI output contract

AI providers must return structured JSON:

```json
{
  "suggested_filename": "AWS-Invoice-2026-08.pdf",
  "top_level_category": "Documents",
  "suggested_subfolder": "Finance/Invoices",
  "confidence": 0.94,
  "reason": "The document appears to be an AWS invoice issued in August 2026.",
  "requires_review": true
}
```

All AI output is treated as **untrusted input** and validated before use. Recommendations must:
- Preserve the original file extension.
- Contain no absolute path and no `..` traversal.
- Resolve to a location inside the selected destination.
- Contain no executable commands.
- Use platform-safe filenames (including rejecting Windows reserved names — see §13).
- Stay within a safe filename length.
- Never overwrite an existing file.

Low-confidence or invalid recommendations stay in `need_your_review` rather than being surfaced for approval.

## 12. Human approval (Version 1)

Every AI action requires approval. The user can: accept filename and destination, accept only the filename, accept only the destination, edit the filename, edit the destination, keep the original filename, reject the recommendation, or skip the file.

The approval UI shows: original filename, current location, proposed filename, proposed destination, reason, confidence score, and whether content will be sent externally. AI-recommended folders are only created after approval. Fully automatic AI actions are **out of scope** for Version 1.

## 13. Windows-specific handling (Day 2)

Must handle: drive letters, backslash separators, case-insensitive paths, UNC paths, OneDrive folders, locked files, antivirus scan delays, path-length limits, invalid Windows characters, and reserved Windows names.

Reject any AI-generated name matching (case-insensitive, with or without extension): `CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9`.

If file stability can't be confirmed (e.g. on a network or sync folder), leave the file in place and show a warning rather than guessing.

## 14. Interface (see also `docs/DESIGN.md`-equivalent decisions below)

The UI must let users: select source folder, select destination folder, start monitoring, stop monitoring, enable dry-run mode, enable optional AI, open the review queue, view recent activity, open logs, edit extension mappings, configure launch-at-login, remove saved AI credentials, and view version information.

The interface is a separate layer from the core so additional interfaces (e.g. a future CLI) can be added later without touching organizer logic.

### 14.1 Interface architecture decisions (locked)

- **UI toolkit**: pywebview — a local HTML/CSS/JS front end rendered in a native webview, backed by the shared Python core. Chosen so the interface is reused nearly as-is between macOS and Windows rather than written twice.
- **Launch behavior**: tray/menu-bar-first. The app launches quietly into the macOS menu bar / Windows system tray; the full window opens only when the user requests it.
- **Main window layout**: single persistent shell — native OS title bar, fixed 180px left sidebar (Dashboard, Review queue, Activity log, Extension rules, Settings, version footer), flexible content area with a header row (page title + one primary action) and independently scrolling body. Sidebar never collapses. No separate top toolbar or bottom status bar. Default window size ~960×600, resizable down to 720×480, remembers last size/position in app config.
- **Menu bar / tray dropdown**: shows monitoring status, start/stop, review queue count badge, dry-run toggle, and links to open the dashboard, review queue, and logs.
- **AI review flow**: reviewing a file opens a focused popup (not silent auto-apply) showing current location, an editable proposed filename and destination with a live "will appear at" preview path, the AI's reason, confidence score, and a notice if content left the device. Nothing moves until the user clicks "Confirm transfer"; "Skip" leaves the file untouched.
- **Review queue**: a list of all pending files, each showing filename, proposed destination preview, and confidence badge; low-confidence items are visually flagged and marked as staying in `need_your_review` rather than being offered for one-click approval.
- **Onboarding**: first-run wizard for selecting source then destination, showing the destination-inside-source warning inline when applicable, and a plain-language notice of the minimal permissions requested.
- **Settings**: general (launch-at-login, dry-run default), AI and privacy (enable/disable AI, provider + "content may leave this device" disclosure, credential removal, telemetry — off by default), and version info.
- **Extension rules editor**: one card per category with removable extension tags and an add-extension input; a persistent note that unmatched extensions always go to `need_your_review`, never a guess.

## 15. Background operation

Supported on both platforms. Must never run as root, administrator, or a privileged system service during normal operation. Documented operations: start, stop, restart, status, enable/disable launch-at-login, uninstall.

## 16. Packaging

Reproducible scripts for: dev setup, running locally, running tests, building the macOS app, building the DMG, building the Windows executable, building the Windows installer, cleaning build artifacts. macOS builds must run on macOS; Windows builds must run on Windows. No cross-compilation.

Expected artifacts: `File Organizer Agent.app` + `File Organizer Agent.dmg` (macOS), `File Organizer Agent.exe` + `File Organizer Agent Setup.exe` (Windows, via PyInstaller + Inno Setup or equivalent).

## 17. Version 1 scope

**In scope**: shared Python core; macOS app + DMG; Windows app + installer; extension-based organization; configurable categories; `need_your_review`; safe folder creation; safe moves; duplicate handling; dry-run mode; activity logs; background monitoring; optional AI understanding with filename/destination recommendations and mandatory approval; secure platform credential storage; cross-platform tests; open-source contribution setup.

**Out of scope for Version 1** (see [`ROADMAP.md`](../ROADMAP.md)): Linux production support, mobile apps, cloud file storage, user accounts, team sync, remote file management, automatic deletion, telemetry by default, fully automatic AI actions, mandatory subscriptions.
