# Planning Input Schema

This contract models ordinary-task duration as rough relative workload and schedule coordinates on one abstract axis. It does not convert workload to hours or working days, use calendar dates, or predict elapsed project time. New skill-flow plans also pin the fixed display messages to a plan-local locale snapshot so the generated files and their review use the same verified language data.

The input is UTF-8 JSON. Run the deterministic generator with:

```text
python -X utf8 "<skill-dir>/scripts/build_plan.py" INPUT.json --output DIR
```

On success it writes `schedule.json`, `gantt.svg`, `gantt.html`, and `plan.md` from one schedule object. Invalid input returns exit code `2` and reports the reason to standard error. The generator reads the supplied plan input and, for snapshot-backed inputs, its explicitly named locale snapshot. It never reads mutable skill configuration or discovers a locale by constructing a path from a language string. The caller resolves skill configuration and verifies or prepares the locale before writing the input.

## Top-level fields

Every required field must appear. `language`, `unit`, and `localization` are optional only for backward compatibility; new skill-flow plans write an explicit language and locale snapshot reference. `assumptions`, `risks`, `requirements`, and `tasks` may be empty arrays. A real project still needs enough tasks to cover its requirements.

| Field | Type | Rules |
| --- | --- | --- |
| `version` | integer | Must be `1`. |
| `language` | canonical language-tag string, optional for legacy input | Omission defaults to `en` for direct generator compatibility. Explicit `null`, an empty string, or a non-string is invalid. The skill workflow always writes the resolved canonical tag. A valid tag alone does not establish localization support: the selected language must resolve to a current verified bundle or a valid plan-local snapshot. |
| `localization` | object, optional for legacy input | New skill-flow plans require `{ "snapshot": "locale-snapshot.json", "messages_sha256": "<canonical message hash>" }`. `snapshot` is a relative path resolved from the directory containing `plan-input.json`; `messages_sha256` must match the messages in that snapshot. The generator verifies both the snapshot language and message hash before rendering. |
| `title` | string | Non-empty project or feature name. |
| `summary` | string | Concise description of scope and goal. |
| `unit` | string, optional | Display label only; omitted values default to the equivalent of “relative work units” in the selected language. The generator preserves a supplied label. It does not convert values. Keep authored explanatory text consistent with the output language and relative-work semantics. |
| `assumptions` | array of strings | Estimation, capacity, technical-boundary, and other planning assumptions. |
| `risks` | array of strings | Known risks and uncertainties. |
| `requirements` | array of objects | Traceable requirement items. |
| `max_parallel` | positive integer or `null` | Capacity limit for ordinary scheduled tasks. `null` means capacity is unknown and the schedule shows theoretical parallelism without a capacity limit. This is a plan value, not an agent-concurrency setting. |
| `tasks` | array of objects | Ordinary tasks, milestones, and external events. |

The `requirements` array may be empty. Otherwise each entry needs a unique, non-empty `id`, `text` containing the original requirement or a faithful target-language paraphrase, and a locatable `source`. Every requirement must be referenced by at least one task's `requirement_ids`. Preserve the original source document verbatim as required by the skill workflow.

## Task fields

Every task object contains all of these fields:

| Field | Type | Rules |
| --- | --- | --- |
| `id` | string | Unique and non-empty. |
| `title` | string | Short, recognizable title. |
| `description` | string | Scope, goal, and boundaries. |
| `requirement_ids` | array of strings | References only defined requirement IDs. |
| `duration` | number | Finite relative workload. An ordinary `task` must be greater than zero. A `milestone` or `external` event must be zero. Use a simple ordinary reference task as `1`; values such as `2` and `3` express roughly two or three times the workload. |
| `depends_on` | array of strings | References only defined task IDs. The full graph must be acyclic. It expresses delivery dependencies only. |
| `resources` | array of strings | Exact-match locks for shared exclusive resources. Reusing a name makes ordinary tasks mutually exclusive. |
| `deliverable` | string | Inspectable result. |
| `acceptance` | array of strings | Conditions for completion and merge readiness. |
| `estimate_basis` | string | Reasoning and assumptions behind the relative-work estimate. Include implementation, tests, documentation, and expected review feedback. |
| `kind` | string | One of the fixed protocol values: `task`, `milestone`, or `external`. |
| `external_ready` | non-negative finite number or `null` | For `external` events only, gives an explicit relative readiness position on the same abstract axis. `null` means unknown and blocks that event and all descendants; `0` may represent an already-ready event. It never represents outside calendar waiting. Every non-external node must set this to `null`. |
| `pr_scope` | string | One independent PR boundary for an ordinary task. For a milestone or external event, explain that it has no code PR. |

`requirement_ids`, `depends_on`, and `resources` cannot contain duplicates. IDs and resource names in them must be non-empty strings. `acceptance`, `resources`, and `requirement_ids` may be empty arrays. The generator allows some descriptive strings to be empty, but a usable plan should provide enough detail for implementation and acceptance.

## Scheduling and relative-work semantics

A dependency is released only after its prerequisite is implemented, accepted, merged, and its interface or data contract is available. A submitted PR alone does not release a dependent task. Record contract design, review, and revision effort in a positive-work ordinary task; a zero-work milestone may then record that the contract is frozen. Mock-based tasks can depend on that milestone, while final integration still depends on the real implementations.

Use `depends_on` for delivery order and `resources` for resource conflicts. Never create a dependency edge merely because two tasks share a person, environment, directory, or other locked resource. Ordinary tasks consume one parallel slot and exclusively hold their listed resources while scheduled. Milestones and external events consume neither.

Unknown external readiness blocks that event and every descendant; the scheduler must not invent start or finish coordinates for the blocked branch. Unrelated branches may still be scheduled. A known `external_ready` is an explicit planning scenario, not a conversion to a calendar wait.

The scheduler uses input order as a stable priority for deterministic topological list scheduling. Identical inputs produce identical results; the algorithm is not a global optimizer. `duration` and bar length express approximate relative workload. `unit` is a label. `start`, `finish`, and labels such as `T+2` express only positions on the abstract axis. None of these values means hours, working days, calendar dates, or actual elapsed time.

## Output and file protection

`schedule.json` echoes the normalized input, including the resolved `language` and `localization` object, and adds each node's `input_index`, `status`, `start`, `finish`, and `blocked_by`, plus generator and schedule metadata. It does not embed the full messages or semantic review. Protocol keys, node kinds, and status values stay fixed regardless of language. The Markdown, SVG, and HTML display text uses the messages in the selected snapshot; SVG and HTML language attributes match it. The standalone artifacts must explain that bar length is relative workload and the axis is not real time.

`locale-snapshot.json` is a separate plan artifact written by the localization helper. It preserves the complete selected messages, source fingerprints, message hash, and verification evidence used to generate and review the plan. New skill-flow plans keep this file beside the four generator outputs. It does not change scheduling semantics or the names of the four primary outputs.

For backward compatibility, an older English or Simplified Chinese input without `localization` may use the corresponding built-in messages and current valid bilingual baseline review. A new skill-flow plan always writes a snapshot, including for `en` and `zh-CN`. A language without an available verified bundle requires a valid snapshot; language selection never silently falls back to English. An explicit `null` language remains invalid even though `language: null` is a valid unset state in the skill-wide configuration.

A new skill-flow input includes this additional field, with the actual hash returned by the localization helper:

```json
{
  "language": "en",
  "localization": {
    "snapshot": "locale-snapshot.json",
    "messages_sha256": "<actual canonical message hash>"
  }
}
```

The HTML is self-contained and offline-capable, embeds the SVG, and provides task-detail interaction. A blocked row's full-row pattern conveys status, not task workload.

The generator replaces only targets bearing its own marker: `schedule.json` is identified by its `generator` field, and other formats by their generation comments. It rejects the entire write if any same-named target belongs to another source, leaving the directory's other files intact. The input file cannot resolve to the same path as any output target.

## Complete legacy-compatible example

This direct-generator example omits the optional locale snapshot to illustrate backward compatibility. The skill workflow always includes the `localization` field and a matching `locale-snapshot.json`.

```json
{
  "version": 1,
  "language": "en",
  "title": "Data export",
  "summary": "Provide asynchronous CSV exports and a download entry point.",
  "unit": "relative work units",
  "assumptions": [
    "Team capacity is unknown, so the schedule shows theoretical parallelism without a capacity limit.",
    "Frontend and backend work can use mocks after the contract is frozen."
  ],
  "risks": [
    "The relative readiness position for object-storage credentials is unknown."
  ],
  "requirements": [
    {
      "id": "R1",
      "text": "Users can request CSV exports.",
      "source": "Requirements document / Export"
    },
    {
      "id": "R2",
      "text": "Users can download completed files.",
      "source": "Requirements document / Download"
    }
  ],
  "max_parallel": null,
  "tasks": [
    {
      "id": "T0",
      "title": "Design and review the export API contract",
      "description": "Define request, status, and download responses and resolve review feedback.",
      "requirement_ids": ["R1", "R2"],
      "duration": 1,
      "depends_on": [],
      "resources": ["export API design"],
      "deliverable": "Reviewed API contract",
      "acceptance": ["Fields, status codes, and error model are agreed."],
      "estimate_basis": "Reference workload of 1; includes design, review, and revision.",
      "kind": "task",
      "external_ready": null,
      "pr_scope": "One documentation PR for the API contract, examples, and compatibility notes."
    },
    {
      "id": "M1",
      "title": "Freeze the export API contract",
      "description": "Record that the reviewed contract is ready for implementation and mock use.",
      "requirement_ids": ["R1", "R2"],
      "duration": 0,
      "depends_on": ["T0"],
      "resources": [],
      "deliverable": "Approved, frozen API contract",
      "acceptance": ["T0 is merged and the contract is marked frozen."],
      "estimate_basis": "Effort is included in T0; this is a zero-work state gate.",
      "kind": "milestone",
      "external_ready": null,
      "pr_scope": "No code PR; records contract approval."
    },
    {
      "id": "E1",
      "title": "Object-storage credentials become available",
      "description": "Wait for the platform team to provide test-environment credentials.",
      "requirement_ids": ["R2"],
      "duration": 0,
      "depends_on": [],
      "resources": [],
      "deliverable": "Test credentials that can be verified",
      "acceptance": ["Upload and download probes succeed in the test environment."],
      "estimate_basis": "Relative readiness position is unknown.",
      "kind": "external",
      "external_ready": null,
      "pr_scope": "No code PR; this is an external delivery gate."
    },
    {
      "id": "T1",
      "title": "Implement the export API",
      "description": "Implement asynchronous export and status lookup against the frozen contract.",
      "requirement_ids": ["R1", "R2"],
      "duration": 3,
      "depends_on": ["M1", "E1"],
      "resources": ["backend export module"],
      "deliverable": "Export API with integration tests",
      "acceptance": ["Requests create export jobs.", "Completed jobs return a download URL."],
      "estimate_basis": "About 3 times the reference task; includes implementation, tests, and review revisions.",
      "kind": "task",
      "external_ready": null,
      "pr_scope": "One backend PR for the export service, route, and integration tests."
    },
    {
      "id": "T2",
      "title": "Implement the export interface",
      "description": "Build export, status, and download views against the frozen contract and a mock.",
      "requirement_ids": ["R1", "R2"],
      "duration": 2,
      "depends_on": ["M1"],
      "resources": ["export page"],
      "deliverable": "Export interface with component tests",
      "acceptance": ["Users can start an export.", "A download entry appears when it completes."],
      "estimate_basis": "About 2 times the reference task; includes UI work, tests, and review revisions.",
      "kind": "task",
      "external_ready": null,
      "pr_scope": "One frontend PR for the export page, API adapter, and component tests."
    },
    {
      "id": "T3",
      "title": "Integrate and test the complete export flow",
      "description": "Replace the mock with the real backend and verify the full export path.",
      "requirement_ids": ["R1", "R2"],
      "duration": 1,
      "depends_on": ["T1", "T2"],
      "resources": ["export test environment"],
      "deliverable": "End-to-end tested export flow",
      "acceptance": ["A real request completes and the resulting file can be downloaded."],
      "estimate_basis": "About 1 times the reference task; includes wiring, end-to-end tests, and review revisions.",
      "kind": "task",
      "external_ready": null,
      "pr_scope": "One integration PR for real API wiring and end-to-end tests."
    }
  ]
}
```

In this example, T0 contains the contract effort and M1 is only the approval gate. T2 can proceed with a mock after M1. T1 remains blocked by unknown external readiness, so T3 also waits for both real implementations. Resource locks are not represented as dependency edges, and all relative positions refer only to the abstract axis.
