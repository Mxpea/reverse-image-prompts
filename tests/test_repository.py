from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "reverse-image-prompts"
SOURCE = ROOT / "skills" / NAME
INSTALLER = ROOT / "scripts" / "install.py"
VALIDATOR = ROOT / "scripts" / "validate.py"
spec = importlib.util.spec_from_file_location("repo_validator", VALIDATOR)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.temp = Path(self.temporary.name)

    def run_installer(self, *args, env=None):
        return subprocess.run(
            [sys.executable, "-X", "utf8", str(INSTALLER), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )

    def test_repository_passes_structural_validation(self):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(VALIDATOR)],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_explicit_destination_installs_exact_skill_files(self):
        parent = self.temp / "custom skills with spaces"
        result = self.run_installer("--dest", parent)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        target = parent / NAME
        expected = {p.relative_to(SOURCE) for p in SOURCE.rglob("*") if p.is_file()}
        actual = {p.relative_to(target) for p in target.rglob("*") if p.is_file()}
        self.assertEqual(actual, expected)
        for relative in expected:
            self.assertEqual((SOURCE / relative).read_bytes(), (target / relative).read_bytes())
        self.assertFalse((target / "README.md").exists())
        self.assertFalse((target / ".git").exists())

    def test_codex_home_is_respected_without_touching_real_profile(self):
        env = dict(os.environ, CODEX_HOME=str(self.temp / "isolated-codex"))
        result = self.run_installer(env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.temp / "isolated-codex" / "skills" / NAME / "SKILL.md").is_file())

    def test_dry_run_does_not_create_destination(self):
        parent = self.temp / "not-created"
        result = self.run_installer("--dest", parent, "--dry-run")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(parent.exists())

    def test_existing_skill_and_other_skills_are_preserved(self):
        parent = self.temp / "skills"
        existing = parent / NAME
        existing.mkdir(parents=True)
        marker = existing / "keep.txt"
        marker.write_text("existing user content", encoding="utf-8")
        sibling = parent / "unrelated-skill"
        sibling.mkdir()
        (sibling / "keep.txt").write_text("unrelated", encoding="utf-8")
        result = self.run_installer("--dest", parent)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(encoding="utf-8"), "existing user content")
        self.assertEqual(list(existing.iterdir()), [marker])
        self.assertEqual((sibling / "keep.txt").read_text(encoding="utf-8"), "unrelated")

    def test_parent_file_is_rejected_without_modification(self):
        parent = self.temp / "not-a-directory"
        parent.write_text("keep", encoding="utf-8")
        result = self.run_installer("--dest", parent)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(parent.read_text(encoding="utf-8"), "keep")

    def test_missing_relative_reference_is_detected(self):
        fixture = self.temp / NAME
        shutil.copytree(SOURCE, fixture)
        (fixture / "references" / "visual-grammar.md").unlink()
        errors = validator.validate_skill(fixture)
        self.assertTrue(any("visual-grammar.md" in error for error in errors))

    def test_reference_cannot_escape_skill_directory(self):
        fixture = self.temp / NAME
        shutil.copytree(SOURCE, fixture)
        (self.temp / "outside.md").write_text("outside", encoding="utf-8")
        with (fixture / "SKILL.md").open("a", encoding="utf-8") as stream:
            stream.write("\n[external](../outside.md)\n")
        errors = validator.validate_skill(fixture)
        self.assertTrue(any("external local reference" in error for error in errors))


    def test_archive_can_be_extracted_and_installed(self):
        archive = self.temp / "repository.zip"
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(ROOT / "scripts" / "package.py"), "--out", str(archive)],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        extraction = self.temp / "unpacked"
        with ZipFile(archive) as package:
            names = package.namelist()
            self.assertIn(f"{NAME}/skills/{NAME}/SKILL.md", names)
            self.assertIn(f"{NAME}/scripts/install.py", names)
            self.assertFalse(any(".git" in Path(name).parts for name in names))
            self.assertFalse(any("__pycache__" in Path(name).parts for name in names))
            for name in names:
                self.assertTrue((extraction / name).resolve().is_relative_to(extraction.resolve()))
            package.extractall(extraction)
        target = self.temp / "installed-from-archive"
        installer = extraction / NAME / "scripts" / "install.py"
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(installer), "--dest", str(target)],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((target / NAME / "SKILL.md").read_bytes(), (SOURCE / "SKILL.md").read_bytes())

    def test_packager_does_not_overwrite_existing_archive(self):
        archive = self.temp / "existing.zip"
        archive.write_bytes(b"preserve existing artifact")
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(ROOT / "scripts" / "package.py"), "--out", str(archive)],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(archive.read_bytes(), b"preserve existing artifact")


if __name__ == "__main__":
    unittest.main()
