# Windows packaging (Day 2)

Run from Windows, from the repo root:

```bash
./scripts/build_windows_exe.sh        # -> dist/File Organizer Agent/File Organizer Agent.exe
./scripts/build_windows_installer.sh  # -> File Organizer Agent Setup.exe (via Inno Setup)
```

No cross-compilation from macOS/Linux - PyInstaller builds must run on the
target OS. See `installer.iss` for the Inno Setup script.
