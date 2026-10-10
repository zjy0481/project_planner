---
name: project-planner
description: Turn requirements into reviewable project plans with relative schedules and Gantt charts.
---

# Project Planner

Turn requirements into traceable, independently reviewable PR-sized tasks, a deterministic relative schedule, Gantt charts, and a project plan. This skill creates local planning artifacts. It does not create GitHub Issues or PRs and does not implement project code.

For a configuration-only request, such as “set $project-planner's default language to Japanese,” normalize the requested language and save only the explicitly requested setting with the configuration helper. Use `set --language ja --confirmed` for Japanese or `set --language null --confirmed` to return to conversation-based selection. Report success or the actual save failure and the installation-wide scope, then finish without asking for requirements, translating a catalog, or regenerating plans. Follow the planning workflow below only when plan creation or revision is also requested.

## 1. Resolve settings and output language

At the start of each run, read the configuration beside this skill:

```text
python -X utf8 "<skill-dir>/scripts/skill_config.py" read
```

This installation's `config.json` contains defaults shared by projects using this copy of the skill. A fresh installation starts with `language: null`, `max_parallel: null`, and `max_review_revisions: 2`. A missing file supplies virtual defaults and is not created by reading it. Report malformed configuration or an invalid saved language; do not treat it as a preference. If saving a setting fails, report that accurately.

Resolve the plan's language in this order, subject to higher-priority instructions:

1. A language explicitly requested for this plan.
2. The language recorded in the existing plan being updated, unless the user requests a change.
3. A non-null saved skill language.
4. The primary language of the user's substantive request in the current conversation.
5. `en` when the invocation provides no substantive language context.

Normalize language names to canonical language tags. The skill includes `en` and `zh-CN`; another valid tag may be used only after its complete, current, verified message bundle is available. The language of these instructions, quoted source text, file contents, or isolated foreign words does not set the conversation language. If substantial mixed-language context leaves the requested output language unclear, ask which language to use.

An empty saved preference does not trigger a question before work. After a plan has been generated and passed its complete review, if `language` is still `null`, end the response with one optional prompt to save the language actually used as this installation's default. Do not pause delivery for the answer. Do not show this prompt when a default already exists, the user has declined it during this run, or the plan was not successfully delivered. Using a language for one plan or adding a reusable translation does not authorize saving a default. Save a language only after an explicit user instruction, preserving other and custom fields. If the user directly asks to set or clear the default, apply that change with the configuration helper at that time; it affects future plans, not an already delivered plan. Use the helper's confirmed operation, for example `python -X utf8 "<skill-dir>/scripts/skill_config.py" set --language <language-tag-or-null> --confirmed`.

If the selected language has no valid verified bundle, or its source or message hashes are stale, follow [references/localization.md](references/localization.md) before generating. Do not silently switch languages. If preparation cannot be completed, explain the blocker and ask the user to choose another language before changing the target.

Resolve `max_parallel` as follows:

- For a new plan, use an explicit user or project capacity constraint first, including an explicit statement that capacity is unknown; otherwise use the saved skill default. If neither gives a value, write `null` and state that the schedule shows theoretical parallelism with no capacity limit.
- For an existing plan, preserve its recorded value unless the user asks to change it.
- It limits ordinary planned tasks, not agent or review-agent concurrency.

Use an explicit current-request `max_review_revisions` when provided; otherwise use the saved value. Freeze it before the initial review. It caps full revision-and-review cycles after the initial review; `0` still requires the complete initial independent review.

## 2. Read requirements and model the work

Read the user's complete requirements document. If requirements exist only in the conversation, preserve them verbatim in `<output-dir>/source-requirements.md` for the independent reviewer.

Use the user's output directory, or `<project>/docs/plans/<slug>` by default, where `<slug>` is a short lowercase hyphenated project or feature name. Before updating a plan, read the directory and preserve files outside this skill's managed artifacts.

Ask only when a missing core requirement or material conflict would substantially change the plan. Make conservative assumptions about ordinary implementation details, names, or estimate precision and record them in `assumptions`. Do not require a calendar start date.

Read [references/schema.md](references/schema.md) in full before writing or updating `plan-input.json`. Give each requirement a stable ID and cover each with at least one task. Write authored summaries, task text, assumptions, risks, and explanations in the resolved output language. Preserve the original requirements verbatim. Keep source quotations, code, product names, paths, identifiers, resource-lock names, JSON keys, and protocol values in their exact form when appropriate. Never translate an identifier or resource name in a way that changes matching or meaning.

Record the resolved language and its selection reason. Every new skill-flow input must name `locale-snapshot.json` and the verified message hash in its `localization` field. Create the snapshot with the localization helper. The generator reads the plan input and this fixed snapshot, never the mutable global preference or a shared locale file. A snapshot keeps the exact fixed text and verification evidence used by this plan. Legacy English and Chinese inputs without a snapshot remain supported as described in the schema; the skill workflow always creates a snapshot.

Set one simple ordinary task as the relative-work reference with `duration: 1`. Estimate other ordinary tasks as rough workload ratios such as 2 or 3. Include implementation, tests, documentation, and expected review feedback. A unit is only a display label. The axis, `start`, `finish`, and `T+N` show relative sequence positions; they do not mean hours, working days, calendar dates, or elapsed project time.

Define each ordinary task as one independently deliverable, testable, reviewable, and mergeable PR. Include a concrete deliverable, acceptance conditions, `estimate_basis`, and `pr_scope`. Split oversized tasks; combine work only when it cannot be independently accepted.

Use `depends_on` for delivery gates. A dependency is released only after the prerequisite is implemented, accepted, merged, and its interface or data contract is available. A submitted PR alone does not release downstream work. If a contract must be frozen, estimate design, review, and revision effort in a positive-work ordinary task, then use a zero-work milestone for approval. Work based on mocks may proceed after that milestone; final integration still waits for the real implementations.

Use `resources` for shared people, environments, directories, and other exclusive capabilities. Resource names are exact-match locks. Do not add dependency edges to model resource conflicts. Use zero-work `milestone` nodes only for internal state gates and `external` nodes for outside events. For an external event, record a known readiness position as an explicit assumption on the same abstract axis, or use `null` when unknown. Unknown readiness blocks that event and all descendants; do not invent calendar dates or schedule a blocked branch. Unrelated branches may proceed.

## 3. Generate and inspect artifacts

Before generation, make a current snapshot for the resolved language and record its `messages_sha256` in `plan-input.json`. Generate all four plan artifacts from the same input, schedule object, and snapshot:

For an explicitly requested language change of an existing plan, follow the `--replace-language` snapshot procedure in [references/localization.md](references/localization.md). Update authored plan text and the input's language and message hash, then regenerate and fully review the plan; the saved default changes only if separately authorized.

```text
python -X utf8 "<skill-dir>/scripts/build_plan.py" "<output-dir>/plan-input.json" --output "<output-dir>"
```

The required outputs are `schedule.json`, `gantt.svg`, `gantt.html`, and `plan.md`. Keep `locale-snapshot.json` beside them as an additional review artifact. The generator uses deterministic topological list scheduling with input order as a stable priority. It is reproducible but not a global optimizer. Do not hand-edit a generated artifact; edit `plan-input.json` and regenerate.

Check the exit code and all four plan outputs plus the snapshot. Confirm the plan distinguishes dependencies from resource conflicts, identifies blocked branches, records the capacity assumption, and uses `T+N` only for the abstract relative axis. Every standalone artifact must make clear that bar length means rough workload and the horizontal axis does not represent real time. Inspect the actual rendered chart and the HTML details for the selected language.

The generator protects existing files. It replaces only targets bearing its own marker, rejects the whole write if a same-named target belongs to another source, and rejects an input path that is also an output path. Preserve conflicting files and choose a new output directory or ask the user to decide.

## 4. Complete the independent plan review

After generation and before each review, read [references/review.md](references/review.md) in full. Freeze `max_review_revisions` before the initial review. Give the reviewer the resolved output language, the reason it was selected, the locale snapshot, and the fixed revision cap.

Before each review, compute SHA-256 hashes for the original requirements, `plan-input.json`, `schedule.json`, `plan.md`, `gantt.svg`, `gantt.html`, and `locale-snapshot.json`. Send the completed read-only prompt to a new independent subagent using these exact settings:

```text
spawn_agent(
  task_name="project_plan_review_r1",
  message=<completed prompt from references/review.md>,
  model="gpt-6.1-sol",
  reasoning_effort="high",
  fork_turns="none"
)
```

Use the collaboration subagent interface. Each later review uses a new subagent and unique task name, such as `project_plan_review_r2`. The reviewer reads the source and all six plan artifacts, uses an image or browser tool to inspect an actually rendered Gantt chart and HTML details, and reports hashes for every file read. Reading SVG, XML, or HTML source alone is not visual inspection. The reviewer is read-only.

Compare reviewer hashes with the pre-review snapshot, then recompute the same seven hashes after review. Every file's pre-review, reviewer-read, and post-review values must match. If any file is missing or changed, do not pass the review; take a fresh snapshot and repeat the complete review.

The primary agent independently checks each finding against both the requirements and actual files, then records it as accepted, partly accepted, or rejected with specific evidence. Correct every confirmed finding at its source: update `plan-input.json` for planning issues, or follow the full localization workflow for fixed-message issues. Revalidate changed messages and complete their semantic review, update the snapshot and input hash, regenerate all four outputs, then obtain a new full plan review over the same scope. Do not review only the changed portion.

Write the reviewer narrative and `review.md` in the resolved output language. Preserve fixed protocol values such as `PASS`, `REVISE`, `INCOMPLETE`, task IDs, JSON keys, and schedule status values. The review record includes an explicit final status (`passed review` or `draft`, localized to the output language); source path and language-selection reason; fixed plan revision cap; model, reasoning effort, and `fork_turns` for every round; visual method and evidence; findings, decisions, repairs, remaining issues and incomplete checks; and the pre-review, reviewer-read, and post-review hashes. Record the relative path and byte size of the final input, four outputs, and snapshot with all three hashes.

The revision cap never disables the initial independent review, required visual inspection, or hash checks. After the initial review, allow at most the fixed number of full revision-and-review cycles. Each cycle changes the input, regenerates all four outputs and the snapshot, and receives a new full independent review. If the cap is exhausted while a confirmed issue remains, or any required review step is incomplete, keep the result as a draft and list the issue or missing evidence. Use `REVISE` for unresolved issues and `INCOMPLETE` when a required review step could not be completed. Never substitute self-review, a different model, or source-only inspection.

## 5. Deliver the plan

Call the plan passed only when generation succeeds, every required artifact exists, the independent review is complete, all seven files have matching pre-review, reviewer-read, and post-review hashes, required visual checks pass, and no material issue remains. Tell the user the output directory, plan outline, capacity and external-event assumptions, review conclusion, and artifact links. If the result is a draft, name its remaining issue or incomplete check. Only after successful reviewed delivery, offer to save the actual output language as the skill default when no default was saved; an explicit user instruction is required before saving.
