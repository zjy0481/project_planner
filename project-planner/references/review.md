# Independent Plan Review Protocol

Every generated plan requires a full independent review. Each round uses a new subagent with no parent conversation context. The reviewer is read-only. The primary agent verifies the findings against the requirements and actual files, revises confirmed issues, regenerates the artifacts, and obtains a full review of the same scope.

## Reusable review prompt

Before each review, the primary agent computes SHA-256 for the original requirements, `plan-input.json`, `schedule.json`, `plan.md`, `gantt.svg`, `gantt.html`, and `locale-snapshot.json`. Replace every placeholder below with its actual value and send the completed prompt verbatim.

```text
You are the independent acceptance reviewer for project-planner. Read the files below without editing, creating, or deleting files.

- Original requirements: <SOURCE_REQUIREMENTS_PATH>
- Planning input: <OUTPUT_DIR>/plan-input.json
- Schedule JSON: <OUTPUT_DIR>/schedule.json
- Project plan: <OUTPUT_DIR>/plan.md
- SVG Gantt chart: <OUTPUT_DIR>/gantt.svg
- HTML Gantt chart: <OUTPUT_DIR>/gantt.html
- Fixed-message locale snapshot: <OUTPUT_DIR>/locale-snapshot.json

Resolved output language: <OUTPUT_LANGUAGE>
Language selection reason: <LANGUAGE_SELECTION_REASON>
Maximum full revision-and-review cycles after this initial review: <MAX_REVIEW_REVISIONS>
The revision cap does not reduce the scope of this initial review.

Pre-review SHA-256 snapshot for all seven listed files:
<PRE_REVIEW_SHA256_TABLE>

Read the original requirements in full, then check all of the following:

1. Requirements map accurately and completely to requirement entries and tasks. No unsupported scope has been added.
2. Each ordinary task is one independently deliverable, testable, reviewable, and mergeable PR. Its deliverable, acceptance conditions, estimate basis, and PR scope are concrete.
3. The dependency graph represents genuine delivery gates. A prerequisite must be implemented, accepted, merged, and have its interface or data contract available before dependent work starts. Contract design, review, and revision effort has positive workload; a zero-work milestone only records approval. Mock-based work may proceed after contract freeze, while final integration waits for real implementations.
4. Resource conflicts are represented by exact-match resource locks, not dependency edges. A null max_parallel is described as theoretical parallelism with unknown capacity and no capacity limit.
5. Unknown external readiness blocks the event and every descendant. No calendar date or outside waiting duration is invented. Known relative readiness, ordinary-task workload, and zero-work node values are valid.
6. plan-input.json, schedule.json, plan.md, and locale-snapshot.json agree on language, task details, dependencies, blocked status, relative positions, and key assumptions. The input and schedule reference the snapshot with its actual message hash. IDs, JSON keys, resource names, node kinds, and schedule status values remain unchanged.
7. Check the workload semantics: ordinary-task duration and bar length mean rough relative workload, with one simple task as 1 and other values expressing approximate ratios such as 2 or 3. The unit is a label only. start, finish, and T+N are positions on an abstract axis, not hours, working days, or calendar dates. external_ready is an explicit position on that same axis, never outside calendar waiting; null blocks and 0 can mean ready.
8. Confirm authored plan text and fixed display copy use the resolved output language. Preserve original quotations, identifiers, and names when appropriate. Verify the HTML lang and SVG language attributes. Check that localization does not alter requirement meaning, effort semantics, dependency gates, resource locks, or blocked status. Confirm the locale snapshot contains the messages used by the output and that its recorded source and message fingerprints agree with the semantic-review evidence stored in the snapshot.
9. Use an image-viewing or browser-rendering tool to inspect an actually rendered Gantt chart and the HTML task details. Check readable text; alignment or clipping of bars, labels, legend, details, and long descriptions; clear blocked status; and agreement with the plan. The chart or its explanation must state that bar length means workload and the horizontal axis is not real time. Do not describe it as a real schedule or progress calendar. Source-only inspection is not a visual check. If you cannot complete this inspection, return INCOMPLETE.
10. Compute SHA-256 for every file you actually read from the list above and compare it with the pre-review snapshot. Report every missing file or mismatch. A missing or mismatched hash rules out PASS.

Return the review in <OUTPUT_LANGUAGE>, translating headings and narrative as needed while preserving fixed protocol values. Do not write the review to a file. Use this structure:

# <localized review-result heading>
- <localized decision label>: PASS | REVISE | INCOMPLETE
- <localized visual-check label>: complete | incomplete
- <localized visual-method label>: <tool and rendered object, or reason it could not be completed>

## <localized files-and-hashes heading>
- <absolute path, SHA-256, and whether it matches the pre-review snapshot for each file>

## <localized evidence heading>
- <evidence for each check, with file path, task/requirement ID, or locatable section>

## <localized issues heading>
For each issue:
- <localized severity label>: material | minor
- <localized location label>: <file and ID/section>
- <localized evidence label>: <observed fact>
- <localized impact label>: <effect on correctness, feasibility, or readability>
- <localized recommendation label>: <smallest specific repair>

If there are no issues, say so in the resolved output language. Do not return PASS merely because JSON parses or fields exist. PASS requires every required check to be complete and no material issue to remain.
```

## Primary agent adjudication and record

The primary agent independently verifies every finding against both the requirements and the actual source or plan files; do not accept a reviewer's description as fact without checking it. Record each finding in `review.md` as accepted, partly accepted, or rejected, with specific evidence and any repair. Every finding whose evidence is confirmed must be corrected before a plan can pass. Write the review record's narrative in the resolved output language and preserve the protocol decisions `PASS`, `REVISE`, and `INCOMPLETE`.

For every review round, record:

- The original requirements' absolute path, resolved language, language-selection reason, and fixed `max_review_revisions` value.
- Reviewer model, reasoning effort, `fork_turns`, decision, and visual-inspection method.
- The pre-review snapshot, reviewer-reported hashes for files actually read, and post-review snapshot.
- Each finding, evidence checked against the actual files, primary decision, and repair or reason for rejection.
- For the final input, four generated outputs, and locale snapshot: relative path, byte size, and pre-review, reviewer-read, and post-review SHA-256 values.
- Plan summary, remaining issues, and incomplete checks.
- An explicit final status indicating `passed review` or `draft`, localized to the output language.

Hash checks cover the original requirements plus `plan-input.json`, `schedule.json`, `plan.md`, `gantt.svg`, `gantt.html`, and `locale-snapshot.json`. The locale snapshot contains the complete fixed messages and their verification evidence. The resolved language and snapshot message hash appear in the plan input and schedule. The reviewer must inspect the snapshot and must not read mutable global skill configuration.

After each review, immediately recompute all seven hashes. The pre-review snapshot, reviewer-read hashes, and post-review values must match file by file. If any file is missing or changed, do not pass the review; create a fresh snapshot and repeat the complete review. A changed plan is never covered by a review of only the changed portion.

The initial independent review is mandatory, even when `max_review_revisions` is `0`. That value caps only the number of full revision-and-review cycles after the initial round. Freeze it before the initial review; later changes to global configuration do not alter the current plan's cap. Each cycle corrects the source of an issue: update the input for planning issues, or complete the full localization correction workflow for fixed-message issues. Revalidate and semantically review changed messages, update the snapshot and its input hash, regenerate all four outputs, and start a new independent full plan review with a unique task name. A zero cap does not disable visual or hash checks. If any confirmed issue remains with no full review cycle available, retain draft status and list it. If any required check or designated model call is unavailable, use `INCOMPLETE` and retain draft status. Never claim the plan passed while a confirmed material issue, required incomplete check, or hash mismatch remains.
