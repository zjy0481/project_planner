from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "project-planner" / "scripts" / "skill_config.py"
SCRIPT_DIR = SCRIPT.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("skill_config", SCRIPT)
skill_config = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(skill_config)


class SkillConfigTests(unittest.TestCase):
    def test_grandfathered_language_preferences_normalize_without_rewriting_on_read(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "config.json"
            for supplied, expected in (("i-klingon", "tlh"), ("en-GB-oed", "en-GB-oxendict"),
                                       ("art-lojban", "jbo"), ("i-default", "i-default")):
                with self.subTest(language=supplied):
                    config_path.write_text(json.dumps({"language": supplied, "custom": True}), encoding="utf-8")
                    before = config_path.read_bytes()
                    self.assertEqual(skill_config.read_config(config_path)["language"], expected)
                    self.assertEqual(config_path.read_bytes(), before)
                    saved = subprocess.run(
                        [sys.executable, "-X", "utf8", str(SCRIPT), "--config", str(config_path),
                         "set", "--language", supplied, "--confirmed"],
                        cwd=ROOT, text=True, capture_output=True,
                    )
                    self.assertEqual(saved.returncode, 0, saved.stderr)
                    result = json.loads(config_path.read_text(encoding="utf-8"))
                    self.assertEqual(result["language"], expected)
                    self.assertTrue(result["custom"])

    def test_missing_file_returns_defaults_without_creating_it(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "missing" / "config.json"

            self.assertEqual(skill_config.read_config(config_path), skill_config.DEFAULTS)
            self.assertFalse(config_path.exists())

    def test_shipped_config_has_initial_defaults(self):
        config_path = ROOT / "project-planner" / "config.json"
        self.assertEqual(
            skill_config.read_config(config_path),
            {
                "language": None,
                "max_parallel": None,
                "max_review_revisions": 2,
            },
        )

    def test_invalid_json_and_invalid_fields_fail_clearly(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text("{broken", encoding="utf-8")
            with self.assertRaisesRegex(skill_config.ConfigError, "无法读取配置文件"):
                skill_config.read_config(config_path)

            invalid_configs = [
                {"language": "../outside", "max_parallel": None, "max_review_revisions": 2},
                {"language": "", "max_parallel": None, "max_review_revisions": 2},
                {"language": "en_US", "max_parallel": None, "max_review_revisions": 2},
                {"language": r"C:\outside", "max_parallel": None, "max_review_revisions": 2},
                {"language": 7, "max_parallel": None, "max_review_revisions": 2},
                {"language": None, "max_parallel": True, "max_review_revisions": 2},
                {"language": None, "max_parallel": 0, "max_review_revisions": 2},
                {"language": None, "max_parallel": None, "max_review_revisions": True},
                {"language": None, "max_parallel": None, "max_review_revisions": -1},
            ]
            for invalid in invalid_configs:
                with self.subTest(config=invalid):
                    config_path.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.assertRaisesRegex(skill_config.ConfigError, "字段无效"):
                        skill_config.read_config(config_path)

    def test_read_normalizes_language_without_rewriting_the_file(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "language": "ZH-cn",
                        "max_parallel": 3,
                        "max_review_revisions": 2,
                        "future_option": "preserved",
                    }
                ),
                encoding="utf-8",
            )
            original_bytes = config_path.read_bytes()

            config = skill_config.read_config(config_path)

            self.assertEqual(config["language"], "zh-CN")
            self.assertEqual(config["future_option"], "preserved")
            self.assertEqual(config_path.read_bytes(), original_bytes)

    def test_partial_update_preserves_other_values_and_unknown_fields(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "config.json"
            original = {
                "language": "en",
                "max_parallel": 3,
                "max_review_revisions": 0,
                "future_option": {"enabled": True},
            }
            config_path.write_text(json.dumps(original), encoding="utf-8")

            updated = skill_config.update_config(
                {"language": "zh-CN"}, path=config_path, confirmed=True
            )

            self.assertEqual(updated["language"], "zh-CN")
            self.assertEqual(updated["max_parallel"], 3)
            self.assertEqual(updated["max_review_revisions"], 0)
            self.assertEqual(updated["future_option"], {"enabled": True})
            self.assertEqual(json.loads(config_path.read_text(encoding="utf-8")), updated)

    def test_unconfirmed_update_does_not_write(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "config.json"
            original_bytes = b'{"language":null,"max_parallel":null,"max_review_revisions":2}\n'
            config_path.write_bytes(original_bytes)

            with self.assertRaisesRegex(skill_config.ConfigError, "需要明确确认"):
                skill_config.update_config(
                    {"language": "ja"}, path=config_path, confirmed=False
                )

            self.assertEqual(config_path.read_bytes(), original_bytes)

    def test_failed_atomic_replace_keeps_original_file(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "config.json"
            original_bytes = b'{"language":"en","max_parallel":4,"max_review_revisions":2}\n'
            config_path.write_bytes(original_bytes)

            with patch.object(skill_config.os, "replace", side_effect=OSError("simulated failure")):
                with self.assertRaisesRegex(skill_config.ConfigSaveError, "无法原子保存"):
                    skill_config.update_config(
                        {"language": "zh-CN"}, path=config_path, confirmed=True
                    )

            self.assertEqual(config_path.read_bytes(), original_bytes)
            self.assertEqual(list(Path(directory).glob(".config.json.*.tmp")), [])

    def test_cli_reports_failed_save_without_success_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "config.json"
            original_bytes = b'{"language":"en","max_parallel":2,"max_review_revisions":2}\n'
            config_path.write_bytes(original_bytes)
            stdout = io.StringIO()
            stderr = io.StringIO()

            with patch.object(skill_config.os, "replace", side_effect=OSError("simulated failure")):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as exit_info:
                        skill_config.main(
                            [
                                "--config",
                                str(config_path),
                                "set",
                                "--language",
                                "ja",
                                "--confirmed",
                            ]
                        )

            self.assertEqual(exit_info.exception.code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("无法原子保存配置文件", stderr.getvalue())
            self.assertEqual(config_path.read_bytes(), original_bytes)

    def test_cli_requires_confirmation_and_accepts_null_values(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "config.json"
            original = {
                "language": "en",
                "max_parallel": 2,
                "max_review_revisions": 2,
                "future_option": {"enabled": True},
            }
            config_path.write_text(json.dumps(original), encoding="utf-8")

            unconfirmed = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(SCRIPT),
                    "--config",
                    str(config_path),
                    "set",
                    "--language",
                    "ja",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(unconfirmed.returncode, 2)
            self.assertEqual(json.loads(config_path.read_text(encoding="utf-8")), original)

            confirmed_ja = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(SCRIPT),
                    "--config",
                    str(config_path),
                    "set",
                    "--language",
                    "ja",
                    "--confirmed",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(confirmed_ja.returncode, 0, confirmed_ja.stderr)
            self.assertEqual(json.loads(config_path.read_text(encoding="utf-8"))["language"], "ja")
            self.assertEqual(
                json.loads(config_path.read_text(encoding="utf-8"))["future_option"],
                {"enabled": True},
            )

            confirmed = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(SCRIPT),
                    "--config",
                    str(config_path),
                    "set",
                    "--language=null",
                    "--max-parallel=null",
                    "--max-review-revisions",
                    "0",
                    "--confirmed",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(confirmed.returncode, 0, confirmed.stderr)
            self.assertEqual(
                json.loads(config_path.read_text(encoding="utf-8")),
                {
                    "language": None,
                    "max_parallel": None,
                    "max_review_revisions": 0,
                    "future_option": {"enabled": True},
                },
            )
            self.assertEqual(list(Path(directory).iterdir()), [config_path])

    def test_cli_normalizes_general_language_tags(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "language": "en",
                        "max_parallel": None,
                        "max_review_revisions": 2,
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(SCRIPT),
                    "--config",
                    str(config_path),
                    "set",
                    "--language",
                    "FR-ca",
                    "--confirmed",
                ],
                cwd=directory,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["language"], "fr-CA")
            self.assertEqual(
                json.loads(config_path.read_text(encoding="utf-8"))["language"], "fr-CA"
            )

    def test_cli_rejects_invalid_language_without_writing(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "language": "en",
                        "max_parallel": 2,
                        "max_review_revisions": 2,
                    }
                ),
                encoding="utf-8",
            )
            original_bytes = config_path.read_bytes()

            for invalid_language in ("", "../outside", r"C:\outside", "en_US"):
                with self.subTest(language=invalid_language):
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-X",
                            "utf8",
                            str(SCRIPT),
                            "--config",
                            str(config_path),
                            "set",
                            "--language",
                            invalid_language,
                            "--confirmed",
                        ],
                        cwd=directory,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                    )

                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(config_path.read_bytes(), original_bytes)

    def test_cli_read_uses_isolated_config_from_another_working_directory(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "config.json"
            expected = {
                "language": "ja",
                "max_parallel": 2,
                "max_review_revisions": 0,
                "future_option": {"enabled": True},
            }
            config_path.write_text(json.dumps(expected), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(SCRIPT),
                    "--config",
                    str(config_path),
                    "read",
                ],
                cwd=directory,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), expected)

    def test_cli_read_missing_config_returns_defaults_without_creating_it(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            config_path = Path(directory) / "missing" / "config.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(SCRIPT),
                    "--config",
                    str(config_path),
                    "read",
                ],
                cwd=directory,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), skill_config.DEFAULTS)
            self.assertFalse(config_path.exists())


if __name__ == "__main__":
    unittest.main()
