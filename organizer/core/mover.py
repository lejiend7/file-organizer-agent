"""Safe file movement: never delete, never overwrite, always inside destination.

Safety outranks speed (docs/PRODUCT_SPEC.md section 8). Every public function
here is written defensively: it double-checks paths stay inside the intended
root even though callers should already guarantee that, because this module
is the last line of defense before touching a user's filesystem.
"""
from __future__ import annotations

import fnmatch
import shutil
from pathlib import Path


class PathSafetyError(Exception):
    """Raised when an operation would touch a path outside the allowed root."""


def is_within(base: Path, target: Path) -> bool:
    """True if `target` resolves to a location inside `base`."""
    try:
        base_r = base.resolve()
        target_r = target.resolve()
    except OSError:
        return False
    return target_r == base_r or base_r in target_r.parents


def ensure_within(base: Path, target: Path) -> None:
    if not is_within(base, target):
        raise PathSafetyError(f"{target} is not inside allowed root {base}")


def is_hidden(path: Path) -> bool:
    return path.name.startswith(".")


def is_symlink(path: Path) -> bool:
    return path.is_symlink()


def is_sensitive(path: Path, patterns: list[str]) -> bool:
    name = path.name
    return any(fnmatch.fnmatch(name, pattern) or name == pattern for pattern in patterns)


def is_temp_file(path: Path, temp_extensions: list[str]) -> bool:
    lower = path.name.lower()
    return any(lower.endswith(ext.lower()) for ext in temp_extensions)


def should_ignore(path: Path, sensitive_patterns: list[str], temp_extensions: list[str]) -> str | None:
    """Return a human-readable skip reason, or None if the file should be processed."""
    if path.is_dir():
        return "directory"
    if is_symlink(path):
        return "symlink"
    if path.name == ".DS_Store":
        return "ds_store"
    if is_hidden(path):
        return "hidden"
    if is_sensitive(path, sensitive_patterns):
        return "sensitive"
    if is_temp_file(path, temp_extensions):
        return "temp_file"
    return None


def dedupe_destination(dest_dir: Path, filename: str) -> Path:
    """Find a safe, non-colliding destination path, e.g. report-2.pdf, report-3.pdf..."""
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = "".join(Path(filename).suffixes)
    # Path.stem/.suffixes mishandle multi-dot compound extensions like
    # ".tar.gz" inconsistently across stdlib versions, so recompute simply:
    if filename.count(".") > 0 and "".join(Path(filename).suffixes) != Path(filename).suffix:
        # keep it simple and robust: split on the first dot for stem/suffix
        first_dot = filename.find(".")
        stem = filename[:first_dot]
        suffix = filename[first_dot:]

    counter = 2
    while True:
        candidate = dest_dir / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def safe_move(src: Path, dest_root: Path, category: str, dry_run: bool = False) -> Path:
    """Move `src` into dest_root/category/, creating the folder if needed.

    Never overwrites an existing file (dedupes instead) and never deletes -
    shutil.move relocates the file, it does not remove data. Raises
    PathSafetyError if the computed destination would land outside dest_root.

    In dry-run mode, no filesystem changes happen; the intended destination
    path is still returned so callers can log what *would* happen.
    """
    dest_dir = dest_root / category
    ensure_within(dest_root, dest_dir)

    destination = dedupe_destination(dest_dir, src.name) if dest_dir.exists() else dest_dir / src.name
    ensure_within(dest_root, destination)

    if dry_run:
        return destination

    dest_dir.mkdir(parents=True, exist_ok=True)
    # Recompute dedupe now that the directory definitely exists, in case of
    # a race between the check above and directory creation.
    destination = dedupe_destination(dest_dir, src.name)
    ensure_within(dest_root, destination)

    shutil.move(str(src), str(destination))
    return destination


def safe_move_to(src: Path, dest_root: Path, relative_dir: str, filename: str, dry_run: bool = False) -> Path:
    """Move `src` to dest_root/relative_dir/filename, used for AI-approved moves
    where the destination is an arbitrary approved subfolder rather than a
    fixed top-level category. Same never-overwrite/never-escape guarantees
    as safe_move.
    """
    dest_dir = (dest_root / relative_dir).resolve() if relative_dir else dest_root.resolve()
    ensure_within(dest_root, dest_dir)

    destination = dedupe_destination(dest_dir, filename) if dest_dir.exists() else dest_dir / filename
    ensure_within(dest_root, destination)

    if dry_run:
        return destination

    dest_dir.mkdir(parents=True, exist_ok=True)
    destination = dedupe_destination(dest_dir, filename)
    ensure_within(dest_root, destination)

    shutil.move(str(src), str(destination))
    return destination
