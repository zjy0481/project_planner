# project-planner

An explicitly invoked Codex skill that turns a requirements document into independently reviewable PR tasks, a dependency and resource constrained relative schedule, and a local project plan with a Gantt chart. It writes local planning artifacts only: it does not create Issues or PRs and does not implement business code.

简体中文： [README.zh-CN.md](README.zh-CN.md)

## For AI agents: install the skill

Install from the `dev` branch of [the source repository](https://github.com/zjy0481/project_management/tree/dev/project-planner), using only the `project-planner` directory. Do not assume that `main` contains this skill.

Prefer the installed `$skill-installer` and pass it this exact URL:

```text
https://github.com/zjy0481/project_management/tree/dev/project-planner
```

The URL includes `/tree/dev/`; omitting it can make an installer use its default `main` ref. If manual installation is required, copy the complete directory tree, including its metadata, to exactly one chosen scope:

```text
repository scope: <your-repo>/.agents/skills/project-planner
user scope:       ~/.agents/skills/project-planner
source:           <checkout>/project-planner
```

Do not overwrite an existing destination. Do not flatten the directory or copy only `SKILL.md`; preserve `agents/openai.yaml`, `references/`, and `scripts/`. OpenAI's [Codex Skills documentation](https://developers.openai.com/codex/skills) supports `.agents/skills`. An installed tool may use an environment-configured legacy `.codex/skills` destination, so follow the destination it reports and do not create duplicate copies.

After an authorized install, verify all of the following:

- the installed directory is named `project-planner`;
- `agents/openai.yaml` keeps `policy.allow_implicit_invocation: false`;
- `python -X utf8 "<skill-dir>/scripts/build_plan.py" --help` succeeds;
- the skill discovery or refresh operation sees the skill; and
- the agent reports the exact installation location.

Reading or editing this README is not an installation request. An agent must not install the skill or alter configuration without an explicit user request.

## For humans: use the skill and inspect its outputs

Provide a requirements document and the skill will break it into small tasks that can each be developed, tested, and reviewed as a PR. The plan shows what each task delivers, how its workload compares with others, which tasks can run together, and which must wait for earlier work.

### What does the timeline mean?

The chart uses relative positions such as `T+0` and `T+1` to show workload and ordering. One unit has no fixed equivalent in hours or working days. Actual elapsed time depends on development speed, staffing, and waiting, so the skill does not predict how many days the project will take.

Choose a small reference task as 1 relative work unit, then estimate other tasks by comparison. If A involves roughly twice the work of B, assign A 2 units and B 1 unit. When B depends on A, A can span `T+0 → T+2` and B `T+2 → T+3`. When they are independent and capacity and resources allow, both can start at `T+0`.

Bar length compares approximate workload; positions and arrows show the development order. Rough proportions are enough, and a bar twice as long does not imply twice the real elapsed time. External prerequisites are shown separately: unknown readiness blocks dependent work, while any supplied relative readiness position is an explicit planning assumption.

### Start a plan

The runtime needs Python 3.10 or newer and uses only the Python standard library. Invoke it explicitly, for example:

```text
Use $project-planner to read requirements.md and create a local project plan for this feature.
```

The process is requirements → plan and schedule → chart outputs → independent review. The final review requires an agent tool using model `gpt-5.6-sol` at `high` reasoning, plus actual browser or image visual inspection of the rendered Gantt chart. If either capability is unavailable, the review is incomplete and must be reported as incomplete; silently substituting self-review or source-only inspection is not valid.

On success, the generator creates four files from one schedule object:

- `plan.md`: the Chinese project plan with requirement mapping, assumptions, risks, schedule, and task details;
- `schedule.json`: the validated input plus deterministic schedule data;
- `gantt.svg`: a static chart suitable for embedding; and
- `gantt.html`: an offline, self-contained interactive chart.

Start with `gantt.html` to compare workload and see parallel tasks and dependencies; click a task for its details. Read `plan.md` for deliverables, acceptance criteria, and estimation assumptions. The generated plan and chart text are Chinese. The repository's sample output is available here:

![Example Gantt chart](demo/gantt.svg)

[Open the sample plan](demo/plan.md) · [Open the interactive HTML source](demo/gantt.html) · [Inspect the sample schedule](demo/schedule.json)

GitHub displays `demo/gantt.html` as source. Download it and open it locally to use its interactive task details.

The full workflow also records its audit evidence in `review.md`. The plan accounts for dependencies, shared people or environments, and the number of tasks that can run together. Unknown external readiness blocks that event and its descendants; unrelated work can still be scheduled. The scheduler uses input order consistently, but does not guarantee the best possible arrangement.

<details>
<summary>Developers: rebuild the sample and run tests</summary>

The standalone Python command below only rebuilds the four generated artifacts from an existing plan JSON; it does not interpret a requirements document or invoke the AI reviewer.

To reproduce the sample with an output directory separate from the input fixture:

```text
python -X utf8 project-planner/scripts/build_plan.py tests/fixtures/plan.json --output .tmp/project-planner-example
python -X utf8 -m unittest discover -s tests -v
```

The generator refuses to overwrite a non-generated file with the same output name. Read `project-planner/references/schema.md` for the complete input contract and `project-planner/SKILL.md` for the workflow boundaries.

</details>
