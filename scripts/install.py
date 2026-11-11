"""Install the bundled skill locally without overwriting existing data."""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from validate import SKILL_NAME, SKILL_ROOT, validate_skill


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, help="Parent skills directory (the skill name is appended)")
    parser.add_argument("--dry-run", action="store_true", help="Show paths without creating files")
    args = parser.parse_args()
    errors = validate_skill()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser()
    parent = (args.dest if args.dest is not None else codex_home / "skills").expanduser().resolve()
    target = parent / SKILL_NAME
    print(f"Source: {SKILL_ROOT}")
    print(f"Destination: {target}")
    if target.exists() or target.is_symlink():
        print("ERROR: Destination exists. Nothing was overwritten; back it up and move it yourself first.")
        return 1
    if parent.exists() and not parent.is_dir():
        print("ERROR: The skills parent path is not a directory.")
        return 1
    if args.dry_run:
        print("Dry run: no files or directories were created.")
        return 0
    try:
        parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SKILL_ROOT, target)
    except OSError as exc:
        print(f"ERROR: Installation failed: {exc}")
        print("If copying began, the new destination may be incomplete; inspect it before retrying.")
        return 1
    print(f"Installed {SKILL_NAME}. No other skills were changed.")
    print("Use the skill on your next conversation turn; reopen the session if discovery has not refreshed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
