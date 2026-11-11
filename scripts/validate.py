"""Dependency-free structural checks for this skill repository."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "reverse-image-prompts"
SKILL_ROOT = ROOT / "skills" / SKILL_NAME
REQUIRED = (
    "SKILL.md", "agents/openai.yaml",
    "references/visual-grammar.md", "references/validation.md",
)
SECRET_PATTERN = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")


def validate_skill(skill_root: Path = SKILL_ROOT) -> list[str]:
    errors: list[str] = []
    skill_root = skill_root.resolve()
    for relative in REQUIRED:
        if not (skill_root / relative).is_file():
            errors.append(f"Missing skill file: {relative}")
    if errors:
        return errors
    texts: dict[Path, str] = {}
    for path in skill_root.rglob("*"):
        if path.is_symlink():
            errors.append(f"Skill must be self-contained; symlink: {path.name}")
            continue
        if path.is_file():
            try:
                texts[path] = path.read_text(encoding="utf-8")
            except (UnicodeError, OSError) as exc:
                errors.append(f"Cannot read UTF-8 file {path.name}: {exc}")
    skill_text = texts.get(skill_root / "SKILL.md", "")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", skill_text, re.S)
    if not match:
        errors.append("SKILL.md must begin with YAML frontmatter")
    else:
        header = match.group(1)
        name = re.search(r"^name:\s*([^\r\n]+)$", header, re.M)
        description = re.search(r"^description:\s*([^\r\n]+)$", header, re.M)
        if not name or name.group(1).strip().strip("\"'") != SKILL_NAME:
            errors.append("Skill name must match its install directory")
        if not description or not description.group(1).strip():
            errors.append("Skill description must be nonempty")
    ui = texts.get(skill_root / "agents" / "openai.yaml", "")
    for field in ("display_name", "short_description", "default_prompt"):
        if not re.search(rf"^  {field}:\s*\S", ui, re.M):
            errors.append(f"Missing UI metadata field: {field}")
    if f"${SKILL_NAME}" not in ui:
        errors.append("UI default prompt must mention the skill")
    for path, text in texts.items():
        if SECRET_PATTERN.search(text):
            errors.append(f"Possible API credential in {path.name}")
        if re.search(r"\bTODO\b", text):
            errors.append(f"Unfinished scaffold in {path.name}")
        if path.suffix == ".md":
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in link or link.startswith("#"):
                    continue
                resolved = (path.parent / link.split("#", 1)[0]).resolve()
                if not resolved.is_relative_to(skill_root) or not resolved.is_file():
                    errors.append(f"Missing or external local reference in {path.name}: {link}")
    return errors


def validate_repo(root: Path = ROOT) -> list[str]:
    errors = validate_skill(root / "skills" / SKILL_NAME)
    for name in ("README.md", "scripts/install.py", "scripts/package.py", "tests/test_repository.py"):
        if not (root / name).is_file():
            errors.append(f"Missing repository file: {name}")
    for base in (root / "scripts", root / "tests"):
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if SECRET_PATTERN.search(text):
                errors.append(f"Possible API credential in {path.relative_to(root)}")
    readme = root / "README.md"
    if readme.is_file() and SECRET_PATTERN.search(readme.read_text(encoding="utf-8")):
        errors.append("Possible API credential in README.md")
    return errors


def main() -> int:
    errors = validate_repo()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Repository and skill checks passed (structure, UTF-8, metadata, links, credential patterns).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
