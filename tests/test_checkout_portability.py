import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SKILL = ROOT / "project-planner"
PLAN_FIXTURE = ROOT / "tests" / "fixtures" / "plan.en.json"
SOURCE_FILES = {
    "en": Path("scripts/locales/en.json"),
    "zh-CN": Path("scripts/locales/zh-CN.json"),
    "context": Path("references/localization.md"),
}
BUILTIN_LANGUAGES = {
    "en": "Project plan",
    "zh-CN": "项目计划",
}
OUTPUT_FILES = ("plan.md", "schedule.json", "gantt.svg", "gantt.html")


class CheckoutPortabilityTests(unittest.TestCase):
    def _run(self, args, *, cwd):
        return subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def _source_hashes(skill_dir):
        return {
            name: hashlib.sha256((skill_dir / path).read_bytes()).hexdigest()
            for name, path in SOURCE_FILES.items()
        }

    def _make_snapshot_and_plan(self, skill_dir, temp_root, language):
        snapshot_path = temp_root / f"{language}-locale-snapshot.json"
        localization_script = skill_dir / "scripts" / "localization.py"
        snapshot = self._run(
            [
                sys.executable,
                "-B",
                "-X",
                "utf8",
                str(localization_script),
                "snapshot",
                "--language",
                language,
                "--output",
                str(snapshot_path),
                "--skill-dir",
                str(skill_dir),
            ],
            cwd=ROOT,
        )
        self.assertEqual(snapshot.returncode, 0, snapshot.stderr)
        bundle = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self.assertEqual(bundle["language"], language)

        plan_input = json.loads(PLAN_FIXTURE.read_text(encoding="utf-8"))
        plan_input["language"] = language
        plan_input.pop("unit", None)
        plan_input["localization"] = {
            "snapshot": snapshot_path.name,
            "messages_sha256": bundle["messages_sha256"],
        }
        input_path = temp_root / f"{language}-plan-input.json"
        input_path.write_text(
            json.dumps(plan_input, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        output_dir = temp_root / f"{language}-plan"
        generator = skill_dir / "scripts" / "build_plan.py"
        generated = self._run(
            [
                sys.executable,
                "-B",
                "-X",
                "utf8",
                str(generator),
                str(input_path),
                "--output",
                str(output_dir),
            ],
            cwd=ROOT,
        )
        self.assertEqual(generated.returncode, 0, generated.stderr)
        for name in OUTPUT_FILES:
            self.assertTrue((output_dir / name).is_file(), name)

        schedule = json.loads((output_dir / "schedule.json").read_text(encoding="utf-8"))
        self.assertEqual(schedule["language"], language)
        plan_text = (output_dir / "plan.md").read_text(encoding="utf-8")
        self.assertIn(BUILTIN_LANGUAGES[language], plan_text)
        return bundle

    def test_full_skill_copy_keeps_hashed_sources_lf_and_generates_both_languages(self):
        git = shutil.which("git")
        if git is None:
            self.skipTest("Git is required to verify checkout attributes")

        original_bytes = {
            name: (SOURCE_SKILL / path).read_bytes()
            for name, path in SOURCE_FILES.items()
        }
        original_hashes = {
            name: hashlib.sha256(raw).hexdigest()
            for name, raw in original_bytes.items()
        }
        self.assertTrue((SOURCE_SKILL / ".gitattributes").is_file())

        for autocrlf in ("true", "false"):
            with self.subTest(core_autocrlf=autocrlf), tempfile.TemporaryDirectory(
                prefix=f"checkout-portability-{autocrlf}-", dir=ROOT / "tests"
            ) as temp:
                temp_root = Path(temp)
                skill_dir = temp_root / "installed-skill-copy"
                shutil.copytree(SOURCE_SKILL, skill_dir)

                initialized = self._run([git, "init", "--quiet"], cwd=skill_dir)
                self.assertEqual(initialized.returncode, 0, initialized.stderr)

                attr_args = [git, "check-attr", "text", "eol", "--"] + [
                    path.as_posix() for path in SOURCE_FILES.values()
                ]
                attributes = self._run(attr_args, cwd=skill_dir)
                self.assertEqual(attributes.returncode, 0, attributes.stderr)
                reported = set(attributes.stdout.splitlines())
                for path in SOURCE_FILES.values():
                    relative = path.as_posix()
                    self.assertIn(f"{relative}: text: set", reported)
                    self.assertIn(f"{relative}: eol: lf", reported)

                staged = self._run(
                    [git, "-c", f"core.autocrlf={autocrlf}", "add", "--all"],
                    cwd=skill_dir,
                )
                self.assertEqual(staged.returncode, 0, staged.stderr)
                for path in SOURCE_FILES.values():
                    (skill_dir / path).unlink()
                    checked_out = self._run(
                        [
                            git,
                            "-c",
                            f"core.autocrlf={autocrlf}",
                            "checkout-index",
                            "--force",
                            "--",
                            path.as_posix(),
                        ],
                        cwd=skill_dir,
                    )
                    self.assertEqual(checked_out.returncode, 0, checked_out.stderr)

                for name, path in SOURCE_FILES.items():
                    self.assertEqual((skill_dir / path).read_bytes(), original_bytes[name])
                self.assertEqual(self._source_hashes(skill_dir), original_hashes)

                for language in BUILTIN_LANGUAGES:
                    bundle = self._make_snapshot_and_plan(skill_dir, temp_root, language)
                    self.assertEqual(bundle["source_hashes"], original_hashes)


if __name__ == "__main__":
    unittest.main()
