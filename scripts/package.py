"""Build a repository ZIP without Git metadata, caches, or environment files."""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from validate import ROOT, SKILL_NAME, validate_repo


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / f"{SKILL_NAME}.zip")
    args = parser.parse_args()
    errors = validate_repo()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    target = args.out.expanduser().resolve()
    if target.exists():
        print("ERROR: Archive already exists; choose a new --out path. Nothing was overwritten.")
        return 1
    top_files = [ROOT / name for name in ("README.md", ".gitignore", ".gitattributes")]
    included = list(top_files)
    for folder in ("skills", "scripts", "tests"):
        for path in (ROOT / folder).rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(ROOT)
            if "__pycache__" in relative.parts or path.suffix in (".pyc", ".pyo"):
                continue
            if path.name.startswith(".env"):
                continue
            included.append(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target, "x", compression=ZIP_DEFLATED) as archive:
        for path in sorted(included):
            archive.write(path, str(Path(SKILL_NAME) / path.relative_to(ROOT)))
    print(f"Archive created: {target}")
    print(f"Repository files: {len(included)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
