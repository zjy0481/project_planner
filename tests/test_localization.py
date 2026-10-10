from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "project-planner" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import localization


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="localization-test-", dir=ROOT / "tests")
        self.addCleanup(self.temp.cleanup)
        self.temp_root = Path(self.temp.name)
        self.skill_dir = self.temp_root / "skill"
        self._make_skill(self.skill_dir)

    @staticmethod
    def _write_json(path: Path, value) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def _review(cls, source_hashes, expected_messages_hash):
        per_key = {
            key: {
                "status": "PASS",
                "evidence": "temporary fixture evidence for structure validation",
            }
            for key in sorted(localization.MESSAGE_KEYS)
        }
        phases = {}
        for phase in localization.REVIEW_PHASES:
            phases[phase] = {
                "source_hashes": dict(source_hashes),
                "messages_sha256": copy.deepcopy(expected_messages_hash),
            }
        return {
            "status": "PASS",
            "per_key": per_key,
            "reviewer": {
                "identity": "temporary-test-reviewer",
                "fork_turns": "none",
            },
            "hashes": phases,
        }

    @classmethod
    def _make_skill(cls, skill_dir: Path, *, add_baseline: bool = True) -> None:
        source_skill = ROOT / "project-planner"
        locales = skill_dir / "scripts" / "locales"
        references = skill_dir / "references"
        locales.mkdir(parents=True, exist_ok=True)
        references.mkdir(parents=True, exist_ok=True)
        for language in localization.BUILTIN_LANGUAGES:
            shutil.copyfile(
                source_skill / "scripts" / "locales" / f"{language}.json",
                locales / f"{language}.json",
            )
        (references / "localization.md").write_text(
            "Temporary localization context for isolated tests.\n",
            encoding="utf-8",
        )
        if not add_baseline:
            return

        catalogs = localization.read_sources(skill_dir)
        source_hashes = localization.current_source_hashes(skill_dir)
        hashes = {
            language: localization.messages_hash(catalogs[language])
            for language in localization.BUILTIN_LANGUAGES
        }
        baseline = {
            "generator": localization.GENERATOR,
            "version": localization.VERSION,
            "source_hashes": source_hashes,
            "messages_sha256": hashes,
            "semantic_review": cls._review(source_hashes, hashes),
        }
        cls._write_json(locales / "baseline-review.json", baseline)

    def _candidate(self, skill_dir: Path | None = None):
        directory = skill_dir or self.skill_dir
        catalogs = localization.read_sources(directory)
        source_hashes = localization.current_source_hashes(directory)
        messages = dict(catalogs["en"])
        review = self._review(source_hashes, localization.messages_hash(messages))
        return messages, review

    def test_normalize_language_canonicalizes_valid_tags_and_rejects_injection(self):
        examples = {
            "en": "en",
            "ZH-cn": "zh-CN",
            "sr-latn-rs": "sr-Latn-RS",
            "de-CH-1901": "de-CH-1901",
            "en-us-u-ca-gregory": "en-US-u-ca-gregory",
            "en-US-x-Client-Tag": "en-US-x-client-tag",
            "x-private-1": "x-private-1",
            "ja": "ja",
        }
        for supplied, expected in examples.items():
            with self.subTest(supplied=supplied):
                self.assertEqual(localization.normalize_language(supplied), expected)

        invalid = [
            None,
            "null",
            "",
            " ",
            " en",
            "en ",
            "../en",
            "en/US",
            "en\\US",
            "en_US",
            "en--US",
            "en-u",
            "en-u-ca-x",
            "en-a-aa-a-bb",
            "sl-rozaj-ROZAJ",
            "i-not-registered",
            "i-klingon-x-private",
            "en\" onload=\"alert(1)",
        ]
        for supplied in invalid:
            with self.subTest(supplied=supplied):
                with self.assertRaises(localization.LocalizationError):
                    localization.normalize_language(supplied)

    def test_messages_hash_uses_canonical_unicode_json(self):
        first = {"z": "相对工作量", "a": "项目计划"}
        reordered = {"a": "项目计划", "z": "相对工作量"}
        expected = hashlib.sha256(
            '{"a":"项目计划","z":"相对工作量"}'.encode("utf-8")
        ).hexdigest()
        self.assertEqual(localization.messages_hash(first), expected)
        self.assertEqual(localization.messages_hash(first), localization.messages_hash(reordered))

    def test_all_grandfathered_tags_use_verified_preferred_values(self):
        expected = {
            "art-lojban": "jbo", "cel-gaulish": "cel-gaulish",
            "en-GB-oed": "en-GB-oxendict", "i-ami": "ami", "i-bnn": "bnn",
            "i-default": "i-default", "i-enochian": "i-enochian", "i-hak": "hak",
            "i-klingon": "tlh", "i-lux": "lb", "i-mingo": "i-mingo", "i-navajo": "nv",
            "i-pwn": "pwn", "i-tao": "tao", "i-tay": "tay", "i-tsu": "tsu",
            "no-bok": "nb", "no-nyn": "nn", "sgn-BE-FR": "sfb", "sgn-BE-NL": "vgt",
            "sgn-CH-DE": "sgg", "zh-guoyu": "cmn", "zh-hakka": "hak", "zh-min": "zh-min",
            "zh-min-nan": "nan", "zh-xiang": "hsn",
        }
        for supplied, preferred in expected.items():
            with self.subTest(tag=supplied):
                self.assertEqual(localization.normalize_language(supplied), preferred)
                self.assertEqual(localization.normalize_language(supplied.upper()), preferred)
                self.assertEqual(localization.normalize_language(preferred), preferred)
        # Preferred-Value processing is deliberately limited to whole
        # grandfathered tags; private-use strings and ordinary subtags retain identity.
        self.assertEqual(localization.normalize_language("x-i-klingon"), "x-i-klingon")
        self.assertEqual(localization.normalize_language("iw-IL"), "iw-IL")

    def test_grandfathered_alias_uses_modern_bundle_and_preserves_old_snapshot(self):
        messages, review = self._candidate()
        published = localization.publish(messages, review, "art-lojban", skill_dir=self.skill_dir)
        self.assertEqual(published.name, "jbo.json")
        self.assertEqual(localization.get_bundle("ART-LOJBAN", skill_dir=self.skill_dir)["language"], "jbo")
        historic = localization.make_bundle(messages, review, "jbo", skill_dir=self.skill_dir)
        historic["language"] = "art-lojban"
        self.assertEqual(localization.validate_bundle(historic, language="jbo")["messages"], messages)
        self.assertEqual(historic["language"], "art-lojban")
        output = self.temp_root / "old-alias-snapshot.json"
        self._write_json(output, historic)
        localization.snapshot("jbo", output, messages=messages, review=review, skill_dir=self.skill_dir)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["language"], "jbo")
        self._write_json(output, historic)
        localization.snapshot("en", output, skill_dir=self.skill_dir, replace_language=True)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["language"], "en")

    def test_validate_messages_requires_complete_keys_and_matching_safe_placeholders(self):
        sources = localization.read_sources(self.skill_dir)
        self.assertEqual(
            localization.validate_messages(sources["zh-CN"], sources["en"]),
            sources["zh-CN"],
        )

        missing = dict(sources["zh-CN"])
        missing.pop("close")
        with self.assertRaisesRegex(localization.LocalizationError, "missing keys"):
            localization.validate_messages(missing, sources["en"])

        extra = dict(sources["zh-CN"], unexpected="extra")
        with self.assertRaisesRegex(localization.LocalizationError, "unexpected keys"):
            localization.validate_messages(extra, sources["en"])

        empty = dict(sources["zh-CN"], close="  ")
        with self.assertRaisesRegex(localization.LocalizationError, "non-empty"):
            localization.validate_messages(empty, sources["en"])

        wrong_name = dict(sources["zh-CN"], blocked_count="{number} 个任务阻塞")
        with self.assertRaisesRegex(localization.LocalizationError, "frozen placeholder contract"):
            localization.validate_messages(wrong_name, sources["en"])

        wrong_format = dict(sources["zh-CN"], completion="相对终点 {finish:.2f}")
        with self.assertRaisesRegex(localization.LocalizationError, "frozen placeholder contract"):
            localization.validate_messages(wrong_format, sources["en"])

        attribute_access = dict(sources["zh-CN"], chart_title="{title.__class__}")
        with self.assertRaisesRegex(localization.LocalizationError, "unsupported placeholder access"):
            localization.validate_messages(attribute_access, sources["en"])

        conversion = dict(sources["zh-CN"], chart_title="{title!r}")
        with self.assertRaisesRegex(localization.LocalizationError, "must not convert"):
            localization.validate_messages(conversion, sources["en"])

        malformed = dict(sources["zh-CN"], chart_title="{title")
        with self.assertRaisesRegex(localization.LocalizationError, "invalid format braces"):
            localization.validate_messages(malformed, sources["en"])

    def test_read_sources_and_raw_source_fingerprints(self):
        catalogs = localization.read_sources(self.skill_dir)
        hashes = localization.current_source_hashes(self.skill_dir)
        for language in localization.BUILTIN_LANGUAGES:
            source_path = self.skill_dir / "scripts" / "locales" / f"{language}.json"
            self.assertEqual(hashlib.sha256(source_path.read_bytes()).hexdigest(), hashes[language])
            self.assertEqual(set(catalogs[language]), localization.MESSAGE_KEYS)
        context_path = self.skill_dir / "references" / "localization.md"
        self.assertEqual(
            hashlib.sha256(context_path.read_bytes()).hexdigest(),
            hashes["context"],
        )
        self.assertEqual(set(hashes), {"en", "zh-CN", "context"})

    def test_missing_source_files_fail_clearly(self):
        (self.skill_dir / "references" / "localization.md").unlink()
        with self.assertRaisesRegex(localization.LocalizationError, "missing or unreadable"):
            localization.current_source_hashes(self.skill_dir)

        with self.assertRaises(localization.LocalizationError):
            localization.read_sources(self.temp_root / "absent-skill")

    def test_builtin_bundle_requires_current_complete_baseline_review(self):
        with self.assertRaisesRegex(localization.LocalizationError, "baseline-review.json"):
            localization.get_bundle(
                "en",
                skill_dir=self._skill_without_baseline(),
            )

        for language in localization.BUILTIN_LANGUAGES:
            bundle = localization.get_bundle(language, skill_dir=self.skill_dir)
            self.assertEqual(bundle["language"], language)
            self.assertEqual(bundle["messages_sha256"], localization.messages_hash(bundle["messages"]))
            self.assertEqual(
                set(bundle["semantic_review"]["per_key"]),
                localization.MESSAGE_KEYS,
            )

    def _skill_without_baseline(self):
        path = self.temp_root / "without-baseline"
        self._make_skill(path, add_baseline=False)
        return path

    def test_make_bundle_and_publish_require_matching_full_review(self):
        messages, review = self._candidate()
        bundle = localization.make_bundle(messages, review, "ja", skill_dir=self.skill_dir)
        self.assertEqual(bundle["language"], "ja")
        self.assertEqual(bundle["messages"], messages)

        for status in ("REVISE", "INCOMPLETE"):
            failed_review = copy.deepcopy(review)
            failed_review["status"] = status
            with self.subTest(status=status), self.assertRaisesRegex(
                localization.LocalizationError, "status must be PASS"
            ):
                localization.make_bundle(messages, failed_review, "ja", skill_dir=self.skill_dir)

        changed_hash = copy.deepcopy(review)
        changed_hash["hashes"]["read"]["messages_sha256"] = "0" * 64
        with self.assertRaisesRegex(localization.LocalizationError, "does not bind the expected messages"):
            localization.make_bundle(messages, changed_hash, "ja", skill_dir=self.skill_dir)

        partial_review = copy.deepcopy(review)
        partial_review["per_key"].pop(next(iter(localization.MESSAGE_KEYS)))
        with self.assertRaisesRegex(localization.LocalizationError, "cover every message key"):
            localization.make_bundle(messages, partial_review, "ja", skill_dir=self.skill_dir)

        unsafe = dict(messages, blocked_count="{items[0]}")
        unsafe_review = self._review(
            localization.current_source_hashes(self.skill_dir),
            localization.messages_hash(unsafe),
        )
        with self.assertRaisesRegex(localization.LocalizationError, "unsupported placeholder access"):
            localization.make_bundle(unsafe, unsafe_review, "ja", skill_dir=self.skill_dir)

        published = localization.publish(messages, review, "ja", skill_dir=self.skill_dir)
        self.assertEqual(published, self.skill_dir / "user-locales" / "ja.json")
        self.assertEqual(
            localization.get_bundle("ja", skill_dir=self.skill_dir)["messages_sha256"],
            localization.messages_hash(messages),
        )

        original_bytes = published.read_bytes()
        bad_review = copy.deepcopy(review)
        bad_review["status"] = "REVISE"
        with self.assertRaises(localization.LocalizationError):
            localization.publish(messages, bad_review, "ja", skill_dir=self.skill_dir)
        self.assertEqual(published.read_bytes(), original_bytes)

    def test_manual_edit_and_source_change_block_shared_reuse_and_publish(self):
        messages, review = self._candidate()
        published = localization.publish(messages, review, "ja", skill_dir=self.skill_dir)
        tampered = json.loads(published.read_text(encoding="utf-8"))
        tampered["messages"]["close"] = "hand-edited"
        self._write_json(published, tampered)
        with self.assertRaisesRegex(localization.LocalizationError, "messages_sha256"):
            localization.get_bundle("ja", skill_dir=self.skill_dir)

        # A fresh, fully reviewed candidate can repair a damaged cache owned by
        # this module after it has passed all candidate checks.
        published = localization.publish(messages, review, "ja", skill_dir=self.skill_dir)
        self.assertEqual(
            localization.get_bundle("ja", skill_dir=self.skill_dir)["messages"],
            messages,
        )

        # Restore the valid published bundle, then change a source without changing
        # the saved review fingerprints. The old review cannot publish again.
        original_bytes = published.read_bytes()
        english_path = self.skill_dir / "scripts" / "locales" / "en.json"
        english_path.write_bytes(english_path.read_bytes() + b"\n")
        with self.assertRaisesRegex(localization.LocalizationError, "baseline review is stale"):
            localization.publish(messages, review, "ja", skill_dir=self.skill_dir)
        self.assertEqual(published.read_bytes(), original_bytes)

    def test_invalid_placeholder_historical_snapshot_is_rejected_and_repairable(self):
        messages, review = self._candidate()
        bundle = localization.make_bundle(messages, review, "ja", skill_dir=self.skill_dir)
        corrupted = copy.deepcopy(bundle)
        corrupted["messages"]["chart_desc"] = "{title:.2f}"
        changed_hash = localization.messages_hash(corrupted["messages"])
        corrupted["messages_sha256"] = changed_hash
        for phase in localization.REVIEW_PHASES:
            corrupted["semantic_review"]["hashes"][phase]["messages_sha256"] = changed_hash

        with self.assertRaisesRegex(localization.LocalizationError, "frozen placeholder contract"):
            localization.validate_bundle(
                corrupted,
                language="ja",
                check_current_sources=False,
                skill_dir=self.skill_dir,
            )

        snapshot_path = self.temp_root / "plan" / "locale-snapshot.json"
        self._write_json(snapshot_path, corrupted)
        saved = localization.snapshot(
            "ja",
            snapshot_path,
            messages=messages,
            review=review,
            skill_dir=self.skill_dir,
        )
        validated = localization.validate_bundle(
            json.loads(saved.read_text(encoding="utf-8")),
            language="ja",
            check_current_sources=False,
            skill_dir=self.skill_dir,
        )
        self.assertEqual(validated["messages"], messages)

    def test_changed_sources_invalidate_shared_reuse_but_not_historical_snapshot(self):
        messages, review = self._candidate()
        snapshot_path = self.temp_root / "plan" / "locale-snapshot.json"
        localization.snapshot(
            "ja",
            snapshot_path,
            messages=messages,
            review=review,
            skill_dir=self.skill_dir,
        )
        historical = json.loads(snapshot_path.read_text(encoding="utf-8"))
        validated = localization.validate_bundle(
            historical,
            language="ja",
            check_current_sources=False,
            skill_dir=self.skill_dir,
        )
        self.assertEqual(validated["messages"], messages)

        english_path = self.skill_dir / "scripts" / "locales" / "en.json"
        english_path.write_bytes(english_path.read_bytes() + b"\n")
        localization.validate_bundle(
            historical,
            language="ja",
            check_current_sources=False,
            skill_dir=self.skill_dir,
        )
        with self.assertRaisesRegex(localization.LocalizationError, "stale for the current source"):
            localization.validate_bundle(
                historical,
                language="ja",
                check_current_sources=True,
                skill_dir=self.skill_dir,
            )
        with self.assertRaisesRegex(localization.LocalizationError, "stale"):
            localization.get_bundle("ja", skill_dir=self.skill_dir)

    def test_snapshot_protects_foreign_targets_and_accepts_candidate_as_fallback(self):
        messages, review = self._candidate()
        foreign_path = self.temp_root / "foreign" / "locale-snapshot.json"
        foreign_path.parent.mkdir(parents=True)
        foreign_bytes = b'{"generator":"someone-else"}\n'
        foreign_path.write_bytes(foreign_bytes)
        with self.assertRaisesRegex(localization.LocalizationError, "not owned"):
            localization.snapshot(
                "ja",
                foreign_path,
                messages=messages,
                review=review,
                skill_dir=self.skill_dir,
            )
        self.assertEqual(foreign_path.read_bytes(), foreign_bytes)

        original_replace = localization.os.replace
        user_locale_dir = self.skill_dir / "user-locales"

        def fail_persistent_publish(source, destination):
            if Path(destination).parent == user_locale_dir:
                raise PermissionError("simulated read-only persistent locale directory")
            return original_replace(source, destination)

        with mock.patch.object(localization.os, "replace", side_effect=fail_persistent_publish):
            with self.assertRaisesRegex(localization.LocalizationError, "cannot atomically write"):
                localization.publish(messages, review, "ja", skill_dir=self.skill_dir)

            fallback = self.temp_root / "deliverable" / "locale-snapshot.json"
            saved = localization.snapshot(
                "ja",
                fallback,
                messages=messages,
                review=review,
                skill_dir=self.skill_dir,
            )
        self.assertTrue(saved.is_file())
        saved_bundle = json.loads(saved.read_text(encoding="utf-8"))
        self.assertEqual(saved_bundle["messages"], messages)
        self.assertEqual(saved_bundle["semantic_review"]["status"], "PASS")
        self.assertFalse((user_locale_dir / "ja.json").exists())

    def test_snapshot_refuses_partial_candidate_and_protects_source_paths(self):
        messages, review = self._candidate()
        output = self.temp_root / "out" / "locale-snapshot.json"
        with self.assertRaisesRegex(localization.LocalizationError, "must be supplied together"):
            localization.snapshot("ja", output, messages=messages, skill_dir=self.skill_dir)
        source_path = self.skill_dir / "scripts" / "locales" / "en.json"
        with self.assertRaisesRegex(localization.LocalizationError, "cannot replace a localization source"):
            localization.snapshot(
                "ja",
                source_path,
                messages=messages,
                review=review,
                skill_dir=self.skill_dir,
            )

    def test_explicit_language_switch_updates_same_plan_directory(self):
        plan_dir = self.temp_root / "language-switch"
        output = plan_dir / "locale-snapshot.json"
        module_path = SCRIPTS / "localization.py"
        prefix = [sys.executable, "-X", "utf8", str(module_path), "snapshot",
                  "--skill-dir", str(self.skill_dir), "--output", str(output)]

        def call(language, *flags):
            return subprocess.run(prefix + ["--language", language, *flags],
                                  cwd=ROOT, text=True, capture_output=True)

        created = call("en")
        self.assertEqual(created.returncode, 0, created.stderr)
        original = output.read_bytes()
        denied = call("zh-CN")
        self.assertEqual(denied.returncode, 2)
        self.assertEqual(output.read_bytes(), original)

        raw = json.loads((ROOT / "tests" / "fixtures" / "plan.en.json").read_text(encoding="utf-8"))
        input_path = plan_dir / "plan-input.json"
        schedules = []
        for language in ("en", "zh-CN", "en"):
            switched = call(language, "--replace-language")
            self.assertEqual(switched.returncode, 0, switched.stderr)
            bundle = localization.validate_bundle(
                json.loads(output.read_text(encoding="utf-8")), language=language,
            )
            raw["language"] = language
            raw["localization"] = {"snapshot": output.name,
                                   "messages_sha256": bundle["messages_sha256"]}
            self._write_json(input_path, raw)
            generated = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPTS / "build_plan.py"),
                 str(input_path), "--output", str(plan_dir)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            schedule = json.loads((plan_dir / "schedule.json").read_text(encoding="utf-8"))
            self.assertEqual(schedule["language"], language)
            fields = ("id", "kind", "start", "finish", "duration", "depends_on", "resources", "status")
            schedules.append([{key: item.get(key) for key in fields} for item in schedule["tasks"]])
            for filename in ("plan.md", "gantt.svg", "gantt.html", "schedule.json"):
                self.assertTrue((plan_dir / filename).is_file())
        self.assertEqual(schedules[0], schedules[1])
        self.assertEqual(schedules[0], schedules[2])

    def test_language_switch_preserves_invalid_or_foreign_snapshot(self):
        output = self.temp_root / "protected-snapshot.json"
        valid = localization.get_bundle("en", skill_dir=self.skill_dir)
        cases = [
            dict(valid, generator="another-generator"),
            dict(valid, version=2),
            dict(valid, language="not/a/tag"),
            dict(valid, language="EN"),
            dict(valid, messages_sha256="0" * 64),
        ]
        for existing in cases:
            with self.subTest(existing=existing.get("language"), version=existing.get("version")):
                self._write_json(output, existing)
                before = output.read_bytes()
                with self.assertRaises(localization.LocalizationError):
                    localization.snapshot("zh-CN", output, skill_dir=self.skill_dir,
                                          replace_language=True)
                self.assertEqual(output.read_bytes(), before)

        self._write_json(output, valid)
        before = output.read_bytes()
        with mock.patch.object(localization.os, "replace", side_effect=PermissionError("read only")):
            with self.assertRaisesRegex(localization.LocalizationError, "cannot atomically write"):
                localization.snapshot("zh-CN", output, skill_dir=self.skill_dir,
                                      replace_language=True)
        self.assertEqual(output.read_bytes(), before)

    def test_snapshot_language_switch_does_not_overwrite_persistent_bundle(self):
        messages, review = self._candidate()
        target = localization.publish(messages, review, "ja", skill_dir=self.skill_dir)
        before = target.read_bytes()
        with self.assertRaisesRegex(localization.LocalizationError, "persistent user locale"):
            localization.snapshot("en", target, skill_dir=self.skill_dir, replace_language=True)
        self.assertEqual(target.read_bytes(), before)
        foreign_language = localization.make_bundle(messages, review, "fr", skill_dir=self.skill_dir)
        self._write_json(target, foreign_language)
        before = target.read_bytes()
        with self.assertRaisesRegex(localization.LocalizationError, "another language"):
            localization.publish(messages, review, "ja", skill_dir=self.skill_dir)
        self.assertEqual(target.read_bytes(), before)

    def test_snapshot_rejects_symlinks_even_with_language_switch(self):
        target = self.temp_root / "real-snapshot.json"
        localization.snapshot("en", target, skill_dir=self.skill_dir)
        link = self.temp_root / "linked-snapshot.json"
        real_symlink = True
        try:
            link.symlink_to(target)
        except OSError:
            real_symlink = False
        before = target.read_bytes()
        if real_symlink:
            with self.assertRaisesRegex(localization.LocalizationError, "symbolic link"):
                localization.snapshot("zh-CN", link, skill_dir=self.skill_dir, replace_language=True)
        else:
            # Windows may prohibit creating links without Developer Mode.
            # Exercise the refusal branch without changing machine settings.
            original = Path.is_symlink
            with mock.patch.object(Path, "is_symlink", autospec=True,
                                   side_effect=lambda path: path == link or original(path)):
                with self.assertRaisesRegex(localization.LocalizationError, "symbolic link"):
                    localization.snapshot("zh-CN", link, skill_dir=self.skill_dir, replace_language=True)
        self.assertEqual(target.read_bytes(), before)

    def test_cli_sources_validate_publish_and_snapshot(self):
        messages, review = self._candidate()
        messages_path = self.temp_root / "candidate.json"
        review_path = self.temp_root / "review.json"
        self._write_json(messages_path, messages)
        self._write_json(review_path, review)
        module_path = SCRIPTS / "localization.py"
        prefix = [sys.executable, "-X", "utf8", str(module_path)]
        common = ["--skill-dir", str(self.skill_dir)]

        sources = subprocess.run(
            prefix + ["sources"] + common,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(sources.returncode, 0, sources.stderr)
        sources_payload = json.loads(sources.stdout)
        self.assertEqual(set(sources_payload["messages"]), {"en", "zh-CN"})

        validated = subprocess.run(
            prefix + [
                "validate",
                "--language",
                "ja",
                "--messages",
                str(messages_path),
            ] + common,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertTrue(json.loads(validated.stdout)["valid"])

        published = subprocess.run(
            prefix + [
                "publish",
                "--language",
                "ja",
                "--messages",
                str(messages_path),
                "--review",
                str(review_path),
            ] + common,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(published.returncode, 0, published.stderr)
        self.assertTrue((self.skill_dir / "user-locales" / "ja.json").is_file())

        output_path = self.temp_root / "cli-plan" / "locale-snapshot.json"
        saved = subprocess.run(
            prefix + [
                "snapshot",
                "--language",
                "ja",
                "--output",
                str(output_path),
                "--messages",
                str(messages_path),
                "--review",
                str(review_path),
            ] + common,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(saved.returncode, 0, saved.stderr)
        self.assertEqual(
            json.loads(output_path.read_text(encoding="utf-8"))["messages_sha256"],
            localization.messages_hash(messages),
        )

        rejected = subprocess.run(
            prefix + [
                "validate",
                "--language",
                "../ja",
                "--messages",
                str(messages_path),
            ] + common,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("language", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
