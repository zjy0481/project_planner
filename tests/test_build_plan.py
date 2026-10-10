import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "project-planner" / "scripts" / "build_plan.py"
FIXTURE = ROOT / "tests" / "fixtures" / "plan.json"
SPEC = importlib.util.spec_from_file_location("build_plan", SCRIPT)
build_plan = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(build_plan)


def task(task_id, duration=1, deps=None, resources=None, kind="task", ready=None, reqs=None, **changes):
    value = {
        "id": task_id,
        "title": f"任务 {task_id}",
        "description": f"描述 {task_id}",
        "requirement_ids": reqs or [],
        "duration": duration,
        "depends_on": deps or [],
        "resources": resources or [],
        "deliverable": f"交付 {task_id}",
        "acceptance": [f"验收 {task_id}"],
        "estimate_basis": "包含开发测试评审合并",
        "kind": kind,
        "external_ready": ready,
        "pr_scope": f"PR {task_id}",
    }
    value.update(changes)
    return value


def plan(tasks, max_parallel=None, requirements=None, **changes):
    value = {
        "version": 1,
        "language": "zh-CN",
        "title": "测试计划",
        "summary": "验证排程",
        "unit": "相对工作单位",
        "assumptions": [],
        "risks": [],
        "requirements": requirements or [],
        "max_parallel": max_parallel,
        "tasks": tasks,
    }
    value.update(changes)
    return value


def schedule(raw):
    return build_plan.build_schedule(build_plan.validate_plan(raw))


class SchedulingTests(unittest.TestCase):
    def by_id(self, result):
        return {item["id"]: item for item in result["tasks"]}

    def test_serial_parallel_and_finish_release(self):
        result = self.by_id(schedule(plan([
            task("A", 2), task("B", 3), task("C", 1, deps=["A"]), task("D", 1, deps=["B"])
        ], max_parallel=2)))
        self.assertEqual((result["A"]["start"], result["B"]["start"]), (0, 0))
        self.assertEqual(result["C"]["start"], 2)
        self.assertEqual(result["D"]["start"], 3)

    def test_multiple_predecessors_wait_for_latest_finish(self):
        result = self.by_id(schedule(plan([
            task("A", 1), task("B", 4), task("C", 2, deps=["A", "B"])
        ])))
        self.assertEqual(result["C"]["start"], 4)
        self.assertEqual(result["C"]["finish"], 6)

    def test_resource_lock_and_unknown_capacity(self):
        result = schedule(plan([
            task("A", 2, resources=["db"]),
            task("B", 1, resources=["db"]),
            task("C", 3, resources=["ui"]),
        ]))
        items = self.by_id(result)
        self.assertEqual((items["A"]["start"], items["B"]["start"]), (0, 2))
        self.assertEqual(items["C"]["start"], 0)
        self.assertEqual(result["scheduling"]["capacity_semantics"], "unbounded_when_null")

    def test_capacity_lock_uses_input_priority(self):
        result = self.by_id(schedule(plan([
            task("A", 2, resources=["a"]), task("B", 1, resources=["b"])
        ], max_parallel=1)))
        self.assertEqual((result["A"]["start"], result["B"]["start"]), (0, 2))

    def test_external_unknown_blocks_only_descendants(self):
        result = self.by_id(schedule(plan([
            task("E", 0, kind="external", ready=None),
            task("BLOCKED", 2, deps=["E"]),
            task("CHILD", 1, deps=["BLOCKED"]),
            task("FREE", 2),
        ], max_parallel=1)))
        self.assertEqual(result["E"]["status"], "blocked")
        self.assertEqual(result["CHILD"]["blocked_by"], ["E"])
        self.assertIsNone(result["BLOCKED"]["start"])
        self.assertEqual((result["FREE"]["start"], result["FREE"]["finish"]), (0, 2))

    def test_external_and_milestone_do_not_consume_capacity_or_resources(self):
        result = self.by_id(schedule(plan([
            task("A", 3, resources=["shared"]),
            task("E", 0, resources=["shared"], kind="external", ready=1),
            task("M", 0, deps=["E"], resources=["shared"], kind="milestone"),
            task("B", 1, resources=["other"]),
        ], max_parallel=1)))
        self.assertEqual(result["E"]["start"], 1)
        self.assertEqual(result["M"]["start"], 1)
        self.assertEqual(result["B"]["start"], 3)

    def test_reverse_order_zero_duration_chain_releases_at_same_time(self):
        result = self.by_id(schedule(plan([
            task("B", 1, deps=["M"]),
            task("M", 0, deps=["E"], kind="milestone"),
            task("E", 0, kind="external", ready=0),
        ])))
        self.assertEqual(result["E"]["start"], 0)
        self.assertEqual(result["M"]["start"], 0)
        self.assertEqual(result["B"]["start"], 0)

    def test_tiny_duration_is_not_treated_as_zero(self):
        result = self.by_id(schedule(plan([task("A", 1e-12), task("B", 1, deps=["A"])])))
        self.assertEqual(result["A"]["finish"], 1e-12)
        self.assertEqual(result["B"]["start"], 1e-12)
        self.assertEqual(build_plan._fmt_time(result["B"]["start"]), "T+1e-12")

    def test_workload_ratios_and_relative_external_ready_share_one_axis(self):
        result = self.by_id(schedule(plan([
            task("REFERENCE", 1),
            task("DOUBLE", 2),
            task("TRIPLE", 3),
            task("READY", 0, kind="external", ready=4),
        ], max_parallel=1)))
        self.assertEqual((result["REFERENCE"]["start"], result["REFERENCE"]["finish"]), (0, 1))
        self.assertEqual((result["DOUBLE"]["start"], result["DOUBLE"]["finish"]), (1, 3))
        self.assertEqual((result["TRIPLE"]["start"], result["TRIPLE"]["finish"]), (3, 6))
        self.assertEqual((result["READY"]["start"], result["READY"]["finish"]), (4, 4))


class ValidationTests(unittest.TestCase):
    def assert_invalid(self, raw, text):
        with self.assertRaises(build_plan.PlanError) as caught:
            build_plan.validate_plan(raw)
        self.assertIn(text, str(caught.exception))

    def test_cycles_and_invalid_values_are_rejected(self):
        cases = [
            (plan([task("A", deps=["B"]), task("B", deps=["A"])]), "循环"),
            (plan([task("A", duration=0)]), "task 类型下必须大于 0"),
            (plan([task("M", duration=1, kind="milestone")]), "milestone 或 external 类型下必须为 0"),
            (plan([task("A", duration=float("inf"))]), "有限非负数"),
            (plan([task("A", deps=["MISSING"])]), "未知依赖"),
            (plan([task("A", reqs=["R2"])], requirements=[{"id": "R1", "text": "x", "source": "s"}]), "未知需求"),
            (plan([task("A")], requirements=[{"id": "R1", "text": "x", "source": "s"}]), "未被任何任务覆盖"),
            (plan([task("A"), task("A")]), "任务 ID 重复"),
            (plan([task("A")], max_parallel=0), "正整数或 null"),
            ({**plan([task("A")]), "version": 1.0}, "严格等于整数 1"),
        ]
        for raw, message in cases:
            with self.subTest(message=message):
                self.assert_invalid(raw, message)

    def test_unit_defaults_and_empty_lists_are_valid(self):
        raw = plan([])
        raw.pop("unit")
        normalized = build_plan.validate_plan(raw)
        self.assertEqual(normalized["unit"], "相对工作单位")

    def test_omitted_language_defaults_to_english_and_null_is_invalid(self):
        raw = plan([])
        raw.pop("language")
        raw.pop("unit")
        normalized = build_plan.validate_plan(raw)
        self.assertEqual(normalized["language"], "en")
        self.assertEqual(normalized["unit"], "relative work units")
        for value in (None, "", "fr", True, [], {}):
            with self.subTest(value=value):
                self.assert_invalid(plan([], language=value), "language")

    def test_language_change_preserves_schedule_and_resource_identity(self):
        raw = plan([task("E", 0, kind="external", ready=None), task("A", 2, resources=["共同资源"]),
                    task("B", 1, resources=["共同资源"]), task("C", 1, deps=["E"])], max_parallel=2)
        chinese = schedule(raw)
        english = schedule({**raw, "language": "en", "title": "Translated title"})
        self.assertEqual(chinese["tasks"], english["tasks"])
        self.assertEqual(chinese["scheduling"], english["scheduling"])
        self.assertEqual(english["tasks"][0]["status"], "blocked")

    def test_explicit_unit_is_not_translated(self):
        result = schedule(plan([], language="en", unit="custom relative units"))
        self.assertEqual(result["unit"], "custom relative units")


class ArtifactTests(unittest.TestCase):
    def snapshot_bundle(self, language="ja", **message_changes):
        """Synthetic review evidence tests transport/validation, not translation quality."""
        loc = build_plan.localization
        messages = {**build_plan.load_messages("en"), "plan_title": "プロジェクト計画",
                    "unit": "相対作業量単位", **message_changes}
        digest = loc.messages_hash(messages)
        sources = {key: "0" * 64 for key in ("en", "zh-CN", "context")}
        review = {"status": "PASS", "per_key": {key: {"status": "PASS", "evidence": "Synthetic transport fixture"}
                  for key in loc.MESSAGE_KEYS}, "reviewer": {"identity": "synthetic-unit-test", "fork_turns": "none"},
                  "hashes": {phase: {"source_hashes": sources, "messages_sha256": digest}
                             for phase in ("before", "read", "after")}}
        return {"generator": loc.GENERATOR, "version": 1, "language": language, "messages": messages,
                "messages_sha256": digest, "source_hashes": sources, "semantic_review": review}

    def snapshot_input(self, root, bundle):
        (root / "locale-snapshot.json").write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
        raw = plan([task("E", 0, kind="external", ready=None), task("A", resources=["exact-resource"]),
                    task("B", deps=["E"])], language=bundle["language"])
        raw.pop("unit")
        raw["localization"] = {"snapshot": "locale-snapshot.json", "messages_sha256": bundle["messages_sha256"]}
        path = root / "plan-input.json"
        path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        return path, raw

    def test_reviewed_new_language_snapshot_and_historical_reproduction(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as tmp:
            root = Path(tmp)
            input_path, raw = self.snapshot_input(root, self.snapshot_bundle())
            with mock.patch.object(build_plan, "load_messages", side_effect=AssertionError("must use frozen snapshot")):
                result = build_plan.run(input_path, root / "out")
                first = {name: (root / "out" / name).read_bytes() for name in build_plan.OUTPUT_NAMES}
                build_plan.run(input_path, root / "out")
                self.assertEqual(first, {name: (root / "out" / name).read_bytes() for name in build_plan.OUTPUT_NAMES})
            self.assertEqual(result["unit"], "相対作業量単位")
            self.assertEqual(result["localization"], raw["localization"])
            public = json.loads(first["schedule.json"])
            self.assertNotIn("_locale_bundle", public)
            self.assertIn("プロジェクト計画", first["plan.md"].decode())
            self.assertIn('<html lang="ja">', first["gantt.html"].decode())
            svg = ET.fromstring(first["gantt.svg"])
            self.assertEqual(svg.attrib["{http://www.w3.org/XML/1998/namespace}lang"], "ja")
            reference = schedule({key: value for key, value in {**raw, "language": "en"}.items() if key != "localization"})
            self.assertEqual(result["tasks"], reference["tasks"])
            self.assertEqual(result["scheduling"], reference["scheduling"])

    def test_invalid_snapshot_fails_before_any_output(self):
        for change in ("message", "review", "language", "binding", "traversal"):
            with self.subTest(change=change), tempfile.TemporaryDirectory(dir=ROOT / "tests") as tmp:
                root = Path(tmp)
                bundle = self.snapshot_bundle()
                if change == "message":
                    bundle["messages"]["close"] = "changed after review"
                elif change == "review":
                    del bundle["semantic_review"]["per_key"]["close"]
                elif change == "language":
                    bundle["language"] = "fr"
                input_path, raw = self.snapshot_input(root, bundle)
                if change == "language":
                    raw["language"] = "ja"
                elif change == "binding":
                    raw["localization"]["messages_sha256"] = "1" * 64
                elif change == "traversal":
                    raw["localization"]["snapshot"] = "../locale-snapshot.json"
                input_path.write_text(json.dumps(raw), encoding="utf-8")
                with self.assertRaisesRegex(build_plan.PlanError, "localization"):
                    build_plan.run(input_path, root / "out")
                self.assertFalse((root / "out").exists())

    def test_fixed_message_markup_is_escaped_in_every_renderer(self):
        text = '</script><img src=x onerror=alert(1)> | [unsafe]'
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as tmp:
            root = Path(tmp)
            bundle = self.snapshot_bundle(plan_title=text, close=text, assumptions=text, legend_task=text)
            input_path, _ = self.snapshot_input(root, bundle)
            build_plan.run(input_path, root / "out")
            for name in ("plan.md", "gantt.svg", "gantt.html"):
                rendered = (root / "out" / name).read_text(encoding="utf-8")
                self.assertNotIn("<img", rendered, name)
                self.assertNotIn("</script><img", rendered, name)
            self.assertIn("\\|", (root / "out" / "plan.md").read_text(encoding="utf-8"))

    def test_both_languages_cover_all_artifacts_and_client_labels(self):
        for language, expected in (("en", "Project plan"), ("zh-CN", "项目计划")):
            with self.subTest(language=language), tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
                raw = plan([task("E", 0, kind="external", ready=None), task("M", 0, kind="milestone")], language=language)
                raw.pop("unit")
                input_path = Path(tmp) / "input.json"
                input_path.write_text(json.dumps(raw), encoding="utf-8")
                output = Path(tmp) / "out"
                result = build_plan.run(input_path, output)
                self.assertEqual(result["language"], language)
                self.assertIn(expected, (output / "plan.md").read_text(encoding="utf-8"))
                svg = ET.fromstring((output / "gantt.svg").read_text(encoding="utf-8"))
                self.assertEqual(svg.attrib["{http://www.w3.org/XML/1998/namespace}lang"], language)
                html_text = (output / "gantt.html").read_text(encoding="utf-8")
                self.assertIn(f'<html lang="{language}">', html_text)
                start = html_text.index('<script type="application/json" id="ui-data">') + len('<script type="application/json" id="ui-data">')
                ui = json.loads(html_text[start:html_text.index('</script>', start)])
                self.assertEqual(ui["blocked"], "Blocked" if language == "en" else "阻塞")
                self.assertEqual(ui["kinds"]["milestone"], "Milestone" if language == "en" else "里程碑")
                self.assertEqual(ui["labels"][0][0], "Status" if language == "en" else "状态")

    def test_english_fixture_has_no_chinese_fixed_labels(self):
        raw = {"version": 1, "language": "en", "title": "Export", "summary": "Export data", "assumptions": [],
               "risks": [], "requirements": [], "max_parallel": None, "tasks": []}
        result = schedule(raw)
        for render in (build_plan.render_markdown, build_plan.render_svg, build_plan.render_html):
            text = render(result)
            self.assertFalse(any('\u4e00' <= char <= '\u9fff' for char in text), render.__name__)

    def test_invalid_locale_fails_before_output_files_are_written(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
            root = Path(tmp)
            locales = root / "locales"
            locales.mkdir()
            for path in build_plan.LOCALES_DIR.glob("*.json"):
                (locales / path.name).write_bytes(path.read_bytes())
            english_path = locales / "en.json"
            messages = json.loads(english_path.read_text(encoding="utf-8"))
            del messages["close"]
            english_path.write_text(json.dumps(messages), encoding="utf-8")
            input_path = root / "input.json"
            input_path.write_text(json.dumps(plan([])), encoding="utf-8")
            output = root / "out"
            with mock.patch.object(build_plan, "LOCALES_DIR", locales):
                with self.assertRaisesRegex(build_plan.PlanError, "message keys"):
                    build_plan.run(input_path, output)
            self.assertFalse(output.exists() and any(output.iterdir()))

    def test_locale_placeholder_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
            locales = Path(tmp)
            for path in build_plan.LOCALES_DIR.glob("*.json"):
                (locales / path.name).write_bytes(path.read_bytes())
            english_path = locales / "en.json"
            messages = json.loads(english_path.read_text(encoding="utf-8"))
            messages["blocked_reason"] = "Blocked {wrong}"
            english_path.write_text(json.dumps(messages), encoding="utf-8")
            with mock.patch.object(build_plan, "LOCALES_DIR", locales):
                with self.assertRaisesRegex(build_plan.PlanError, "placeholders differ"):
                    build_plan.load_messages("en")

    def test_fixture_end_to_end_and_timeline_consistency(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
            completed = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), str(FIXTURE), "--output", tmp],
                text=True, capture_output=True, encoding="utf-8", check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = Path(tmp)
            self.assertEqual({path.name for path in output.iterdir()}, set(build_plan.OUTPUT_NAMES))
            data = json.loads((output / "schedule.json").read_text(encoding="utf-8"))
            markdown = (output / "plan.md").read_text(encoding="utf-8")
            svg = (output / "gantt.svg").read_text(encoding="utf-8")
            html_text = (output / "gantt.html").read_text(encoding="utf-8")
            for item in data["tasks"]:
                self.assertIn(item["id"], markdown)
                self.assertIn(item["id"], svg)
                if item["status"] == "scheduled":
                    self.assertIn(build_plan._fmt_time(item["start"]), markdown)
                    self.assertIn(build_plan._fmt_time(item["finish"]), markdown)
            self.assertIn("application/json", html_text)
            self.assertIn("dependency_release", (output / "schedule.json").read_text(encoding="utf-8"))

    def test_unicode_and_markup_are_safely_escaped(self):
        dangerous = "中文\u0000 </script><img src=x onerror=alert(1)> | [链接]"
        raw = plan([task("安全", title=dangerous, description=dangerous, deliverable=dangerous, pr_scope=dangerous)])
        result = schedule(raw)
        html_text = build_plan.render_html(result)
        svg = build_plan.render_svg(result)
        markdown = build_plan.render_markdown(result)
        self.assertNotIn("</script><img", html_text)
        self.assertNotIn("<img", svg)
        self.assertNotIn("<img", markdown)
        self.assertIn("中文", html_text)
        self.assertNotIn("\u0000", svg)
        self.assertIn("&lt;img", svg)
        self.assertIn("\\|", markdown)

    def test_blocked_html_does_not_claim_whole_plan_completion(self):
        result = schedule(plan([task("E", 0, kind="external", ready=None), task("A", 1)]))
        html_text = build_plan.render_html(result)
        self.assertIn("整体相对终点未知", html_text)
        self.assertIn("可排程相对终点 T+1", html_text)

    def test_short_bar_position_labels_stay_inside_plot(self):
        result = schedule(plan([
            task("base", 64),
            task("last", 1, deps=["base"]),
            task("middle", 1, deps=["base"]),
            task("first", 1),
        ]))
        svg = ET.fromstring(build_plan.render_svg(result))
        ns = {"s": "http://www.w3.org/2000/svg"}
        for task_id in ("last", "middle", "first"):
            with self.subTest(task=task_id):
                row = svg.find(f'.//s:g[@data-task-id="{task_id}"]', ns)
                label = next(text for text in row.findall("s:text", ns) if " → " in (text.text or ""))
                x = float(label.attrib["x"])
                estimated_width = len(label.text) * 6
                if label.attrib.get("text-anchor", "start") == "end":
                    left_edge, right_edge = x - estimated_width, x
                else:
                    left_edge, right_edge = x, x + estimated_width
                self.assertGreaterEqual(left_edge, 300)
                self.assertLessEqual(right_edge, 1060)

    def test_refuses_non_generated_target_and_input_collision(self):
        raw = plan([task("A")])
        result = schedule(raw)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
            root = Path(tmp)
            input_path = root / "input.json"
            input_path.write_text(json.dumps(raw), encoding="utf-8")
            output = root / "out"
            output.mkdir()
            (output / "plan.md").write_text("user file", encoding="utf-8")
            with self.assertRaisesRegex(build_plan.PlanError, "拒绝覆盖"):
                build_plan.write_outputs(input_path, output, result)
            collision = root / "collision"
            collision.mkdir()
            colliding_input = collision / "plan.md"
            colliding_input.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(build_plan.PlanError, "路径冲突"):
                build_plan.write_outputs(colliding_input, collision, result)

    def test_cli_reports_invalid_json_without_traceback(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as tmp:
            root = Path(tmp)
            bad = root / "bad.json"
            bad.write_text("{ bad", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), str(bad), "--output", str(root / "out")],
                text=True, capture_output=True, encoding="utf-8", check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("JSON 解析失败", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)


if __name__ == "__main__":
    unittest.main()
