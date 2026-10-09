# project-planner

An explicitly invoked Codex skill that turns requirements into independently reviewable PR-sized tasks, a dependency- and resource-constrained relative schedule, and local plan and Gantt artifacts. It does not create Issues or PRs or implement project code.

简体中文：[README.zh-CN.md](README.zh-CN.md)

## Install the skill

For AI-assisted installation, use the `dev` branch and install only the `project-planner` directory from [the source repository](https://github.com/zjy0481/project_management/tree/dev/project-planner). Do not assume `main` contains this skill.

Prefer the installed `$skill-installer` and pass this exact URL:

```text
https://github.com/zjy0481/project_management/tree/dev/project-planner
```

The `/tree/dev/` segment matters because omitting it may select the installer's default branch. If manual installation is necessary, copy the complete skill directory to one chosen scope:

```text
repository scope: <your-repo>/.agents/skills/project-planner
user scope:       ~/.agents/skills/project-planner
source:           <checkout>/project-planner
```

Keep the full directory tree, including `config.json`, `agents/openai.yaml`, `references/`, and `scripts/` (including the configuration helper and language resources). Do not flatten the directory or copy only `SKILL.md`. Do not overwrite an existing installation. When updating a skill, preserve its existing user settings, custom configuration fields, and any `user-locales/` runtime bundles. Keep runtime locale files local; do not publish them with the skill source. The `config.json` beside the installed skill is shared by projects that use that installation; it is separate from Codex settings.

An installer may choose an environment-configured legacy `.codex/skills` destination. Follow the destination it reports and avoid duplicate copies. OpenAI's [Codex Skills documentation](https://developers.openai.com/codex/skills) documents `.agents/skills`.

An agent must not install or alter an installation without an explicit user request. After an authorized install, verify the directory name, the explicit-only invocation policy, that the generator's `--help` command succeeds, that skill discovery sees the skill, and the reported installation path.

Also verify that both built-in locale baselines can produce valid snapshots. Keep the temporary output outside the installed skill directory:

Keep the skill's hidden `.gitattributes` file when copying the directory. It fixes the three fingerprinted source files to LF on Git checkout; converting those files to CRLF invalidates the raw-byte baseline even if their text is unchanged.

```text
python -X utf8 "<skill-dir>/scripts/localization.py" snapshot --language en --output "<temporary-dir>/project-planner-en-snapshot.json" --skill-dir "<skill-dir>"
python -X utf8 "<skill-dir>/scripts/localization.py" snapshot --language zh-CN --output "<temporary-dir>/project-planner-zh-CN-snapshot.json" --skill-dir "<skill-dir>"
```

Each command must exit successfully and create its snapshot. If either fails, treat the installation's built-in source baseline as unavailable; report the failure instead of changing source hashes or review evidence.

## Use the skill

Provide a requirements document and invoke `$project-planner`, for example:

```text
Use $project-planner to read requirements.md and create a reviewed project plan for this feature.
```

The skill creates `plan.md`, `schedule.json`, `gantt.svg`, `gantt.html`, and `review.md` in the requested output directory. Start with `gantt.html` to explore tasks and their dependencies; open a task to see its details. Read `plan.md` for requirement mapping, assumptions, deliverables, acceptance criteria, and estimates. The HTML is self-contained and works offline. GitHub displays it as source, so download it and open it locally for interactive details.

The generator requires Python 3.10 or newer and uses only the Python standard library.

The output language follows this order: an explicit request for this plan, the language recorded in an existing plan being updated, the saved skill default, the primary language of the user's substantive request, then English when the invocation has no substantive language context. Source text, file contents, and isolated foreign words do not set the conversation language; ask only when substantial mixed-language context leaves the requested output unclear. The built-in message sets are Simplified Chinese (`zh-CN`) and English (`en`). Other valid language tags require a complete, current, semantically reviewed message bundle before the plan can be generated; see [the localization workflow](project-planner/references/localization.md). A new installation's `language: null` does not cause an upfront question. After a plan is generated and passes its full review, the skill may offer to save the language actually used as the default. It saves only after an explicit instruction, and translating messages does not change that preference. Older input files without `language` remain usable and default to English; older English and Chinese inputs without a locale snapshot remain compatible. The skill workflow always writes the resolved language and a plan-local locale snapshot. English instructions do not force English output.

The skill's configuration also supports a default `max_parallel` and `max_review_revisions`. For a new plan, an explicit project or user capacity constraint, including an explicit statement that capacity is unknown, takes priority over the saved parallel-task default. When neither supplies a capacity, the plan records unknown capacity and shows theoretical parallelism. `max_parallel` limits ordinary planned tasks, not agents. Updating an existing plan preserves its recorded capacity unless the user asks to change it. The default plan-review cap is two full revision-and-review cycles after the initial review. Setting it to zero still requires the complete initial independent review. Preparing a new message language has a separate limit of one full initial semantic review plus at most two full revision reviews; it does not consume the plan-review cap.

### What the chart means

The chart uses relative positions such as `T+0` and `T+1` to show sequence and workload. One unit has no fixed value in hours or working days; the skill does not predict calendar duration. Choose one simple task as the reference workload of 1, then estimate other tasks by rough comparison. A bar about twice as long means about twice the workload, not twice the real elapsed time.

Dependencies show delivery gates. A dependent task waits until its prerequisite is implemented, accepted, merged, and its interface or data contract is available. Shared people, environments, or other exclusive resources are expressed as resource locks. Unknown external readiness blocks that event and its descendants; any known readiness position is an explicit relative-axis assumption, not a calendar date. Unrelated work can proceed.

### Review requirements

Every generated plan receives an independent read-only review using `gpt-6.1-sol` at `high` reasoning effort, with `fork_turns="none"`, plus actual visual inspection of the rendered Gantt chart and HTML details. The reviewer checks the source requirements, plan input, four generated outputs, and `locale-snapshot.json` against matching pre-review, reviewer-read, and post-review SHA-256 values. If the model, agent, visual inspection, or hash check is unavailable or fails, the result remains a draft and is reported as incomplete. The review limit never disables the initial review. A full repair review uses a new independent subagent and covers the same complete scope.

### Examples

The Chinese sample plan and chart are in [`demo/`](demo/). The English sample is in [`demo/en/`](demo/en/):

- [English plan](demo/en/plan.md)
- [English Gantt chart](demo/en/gantt.svg)
- [English interactive chart](demo/en/gantt.html)
- [English schedule data](demo/en/schedule.json)

The [Japanese plan](demo/ja/plan.md), [interactive chart](demo/ja/gantt.html), and [reviewed message snapshot](demo/ja/locale-snapshot.json) demonstrate an additional language prepared through the translation-review workflow.

GitHub shows the HTML file as source. Download it and open it locally to use the interactive task details.

<details>
<summary>Developers: rebuild the sample and run tests</summary>

From the repository root, the generator rebuilds artifacts from an existing input; it does not interpret requirements or run an AI review.

```text
python -X utf8 project-planner/scripts/build_plan.py tests/fixtures/plan.json --output .tmp/project-planner-example
python -X utf8 -m unittest discover -s tests -v
```

The generator refuses to overwrite a same-named file that it did not generate. Read [the input schema](project-planner/references/schema.md) for the complete data contract and [the skill instructions](project-planner/SKILL.md) for the planning workflow.

</details>
