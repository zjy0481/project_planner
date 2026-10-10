# LabFlow English plan review

**Final status: passed review — PASS.**

This is an independently modeled English plan requested by the user, not a translation of the Chinese demonstration. The Chinese plan was not used as a planning or acceptance oracle.

- Original requirements: `D:\strange tools\project-planner\demo\labflow\requirements.md` (v1.1, unchanged).
- Resolved output language: `en`, explicitly requested for this new plan.
- Fixed maximum full revision-and-review cycles after the initial review: `2`.
- Skill source: `project-planner/SKILL.md` in this checkout; skill defaults were read and not changed.
- Workspace: `D:/strange tools/project-planner`; branch `dev`; base `4a3dcddb5e79229c18c750d789f2ab92bfd23bf9`. Artifacts are uncommitted.

## Plan outline and assumptions

36 requirements, 84 nodes, and 76 ordinary PR tasks. Project capacity is `max_parallel: 3`, from requirements chapter 6.

Resource conflicts use exact-match locks `backend-lead`, `frontend-lead`, `db-reviewer`, and `qa-shared-env`. Dependencies require completed, accepted, merged prerequisites and available contracts. Design/review effort is positive work; freeze milestones and external events have zero work.

Relative workload and `T+N` are abstract positions, not calendar durations. Asset sandbox readiness at `T+6` is a given planning assumption. Enterprise identity readiness is unknown; its real integration and downstream release B remain blocked, while release A remains independently deliverable. The whole project endpoint is unknown.

Blocked nodes: `IDENTITY_READY`, `OIDC_REAL`, `QA_REAL_IDENTITY`, `QA_CROSS_B`, `PERF_B`, `EVIDENCE_B`, `ACCEPT_B`, `B_RELEASE`, `PROJECT_COMPLETE`.

LabFlow itself retains the Simplified Chinese product-interface requirement (REQ-025). Plan language does not change it. Planning review PASS is not evidence that product implementation or business acceptance has occurred.

## Independent review round 1

- Reviewer: `/root/labflow_en_review_r1`; model `gpt-6.1-sol`, reasoning effort `high`, `fork_turns="none"`; read-only.
- Decision: `REVISE`; visual check: complete.
- Visual method and evidence: mcp__cua_repl actual screenshots of HTML and standalone SVG on the loopback preview service; HTML at 1440px and 360px, D_DATA long detail top/bottom, OIDC_REAL blocked detail top/bottom and blocked chart rows. Hidden-tab rendering succeeded after visible-tab creation was unavailable. Viewport reset and reviewer-created tab closure succeeded on the permitted cleanup retry.

### Evidence for all ten checks

1. Read all eight requirements sections and all 84 nodes. REQ-001..036 preserve stable IDs/source locations; substantially faithful stage/security/notification/recovery scope, with three confirmed findings below.
2. All 76 ordinary tasks have concrete deliverables, acceptance, relative estimates and PR scopes; RESERVE_CREATE internal service, RESERVE_KEY public idempotency and ACCOUNT_DISABLE transactional closure are independently defensible. QA PRs exclude product repairs.
3. Positive D_DATA..D_OPS and enterprise design work precede zero-work freeze approvals; mocked UI follows frozen contracts and WIRE_A waits for real accepted implementations. Scheduled prerequisite positions are valid.
4. Capacity3 matches source chapter6; exact four resource locks retained; peak concurrency3, overlapping exclusive locks0, and formal QA waits for positive ENV preparation.
5. Asset event is zero-work/readyT+6. Unknown IDENTITY_READY exactly blocks nine descendants with null positions; A, mocks and real assets remain schedulable.
6. Read-only Python -B in-memory validation rebuilt schedule, Markdown, SVG and HTML exactly. Input/schedule reference the snapshot hash 2902e1a4a6abab0e6eda1534e820f67bcd795489c499d20d63158401d6efad34.
7. FIXTURE reference1 and ordinary1/2/3 ratios; six milestones/two externals zero. All explanation distinguishes workload and relative positions from business/calendar durations; overall endpoint unknown.
8. English authored/fixed text, product remains Chinese, HTML lang=en and SVG xml:lang=en; all59 messages and embedded before/read/after bilingual semantic proof valid. The authored findings remain subject to repair.
9. Real desktop/narrow screenshots and independent SVG show readable captions, legend, bars, intentional ellipses, full long/blocked details and clear hatching. Long details scroll vertically; narrow chart intentionally scrolls horizontally.
10. All seven actual read hashes equal pre-review values and repeated final reviewer measurements. Primary immediately measured matching post-review hashes.

### Primary adjudication and repair

**R1-F1 — material, accepted.** REPORTS.acceptance[1] says creation-before-range zeroes the denominator. Primary independently compared actual input with requirements.md lines267/269 and scenario23/line433: only the range before creation contributes nothing, and a previously created DEV-03 has denominator720 on the reporting day. Repair states the exact report/opening/post-creation intersection, entirely pre-creation zero and creation-day clipping; earlier creation does not zero a later range.
**R1-F2 — material, accepted.** Primary read QUALIFICATION, UI_DIRECTORY/UI_ACCOUNTS/UI_RESERVATIONS, D_API/D_UI and QA_REPORT_UI_A. Backend grant/revoke exists, but UI_RESERVATIONS only displays owner qualifications and no frontend acceptance owns administrator controls. REQ-013 requires manager grant/revoke and owner-only read. Repair adds frozen grant/read/revoke contracts and UI flows, interval/current-history/revoke-confirmation/error controls in existing device administration, explicit WIRE_A delivery and real UI/API verification. Direct validity editing and terminal revival remain forbidden.
**R1-F3 — material, accepted.** Primary compared source section3 fixed-laboratory minimum contract with actual D_API/DEVICE/UI_DIRECTORY: stable two labs/no-add are modeled, but lab-name edit has no concrete delivery acceptance. Repair adds a reviewed authorized administrator name-edit matrix, endpoint and existing catalog UI plus direct/browser verification. IDs, scope and device/history relations remain unchanged; no lab-add or device-migration scope is introduced.
The three tightly related input repairs are performed by Primary after reviewer writers are quiescent and post-review hashes match; no independent implementation helper is needed for these bounded field additions. Existing resource locks/dependencies stay unchanged. UI_DIRECTORY workload increases2->3 to account for the added qualification/name controls, with its PR boundary/estimate updated. All four outputs and the current unchanged English snapshot are regenerated before a fresh full review.

### Three-way file hashes

| File | Bytes | Pre-review SHA-256 | Reviewer-read SHA-256 | Post-review SHA-256 |
| --- | ---: | --- | --- | --- |
| [requirements.md](requirements.md) | 69524 | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` |
| [plan-input-en.json](plan-input-en.json) | 168284 | `90babd84ad37e719f8dcc4674244aacdc1de5895e29481774bbc0363b4108854` | `90babd84ad37e719f8dcc4674244aacdc1de5895e29481774bbc0363b4108854` | `90babd84ad37e719f8dcc4674244aacdc1de5895e29481774bbc0363b4108854` |
| [schedule-en.json](schedule-en.json) | 176078 | `c9d9b0c4bedc72128978ee9f175172122298cda8d07d42f6c7bb6110fd006170` | `c9d9b0c4bedc72128978ee9f175172122298cda8d07d42f6c7bb6110fd006170` | `c9d9b0c4bedc72128978ee9f175172122298cda8d07d42f6c7bb6110fd006170` |
| [plan-en.md](plan-en.md) | 156916 | `b1d7340c078f269b7d33b57a462e56ea57be3fcc002ff2fc72923eba7cf5dc64` | `b1d7340c078f269b7d33b57a462e56ea57be3fcc002ff2fc72923eba7cf5dc64` | `b1d7340c078f269b7d33b57a462e56ea57be3fcc002ff2fc72923eba7cf5dc64` |
| [gantt-en.svg](gantt-en.svg) | 204292 | `d23c0d08dd692931da390d9917b817044876ffd3563482205d2e637ce972d09b` | `d23c0d08dd692931da390d9917b817044876ffd3563482205d2e637ce972d09b` | `d23c0d08dd692931da390d9917b817044876ffd3563482205d2e637ce972d09b` |
| [gantt-en.html](gantt-en.html) | 384243 | `336b5f7f86999af3b31f7d02b2c6b43bf48245655f11381d176f6c93f13f234f` | `336b5f7f86999af3b31f7d02b2c6b43bf48245655f11381d176f6c93f13f234f` | `336b5f7f86999af3b31f7d02b2c6b43bf48245655f11381d176f6c93f13f234f` |
| [locale-snapshot-en.json](locale-snapshot-en.json) | 17294 | `8612e9d5d00d46b4427dc4cbbb02473a4d43876d34b3945a33fb07d4ed115485` | `8612e9d5d00d46b4427dc4cbbb02473a4d43876d34b3945a33fb07d4ed115485` | `8612e9d5d00d46b4427dc4cbbb02473a4d43876d34b3945a33fb07d4ed115485` |

The original requirements and all six plan artifacts matched before, during, and immediately after this complete review.

## Independent review round 2

- Reviewer: `/root/labflow_en_review_r2`; model `gpt-6.1-sol`, reasoning effort `high`, `fork_turns="none"`; read-only.
- Decision: `PASS`; visual check: complete.
- Visual method and evidence: cua_repl actual browser screenshots of rendered HTML and standalone SVG on http://127.0.0.1:8768/; 1440px desktop and 360px narrow layouts, D_DATA long details top/bottom, OIDC_REAL blocked details and actual horizontal chart scrolling (about690px offset). Captions, legend, markers, bars and nine blocked rows were inspected; no material clipping/alignment defect. Viewport override reset; browser returned to English HTML.

### Evidence for all ten checks

1. Read requirements v1.1 all sections1..8, all32 scenarios and confirmed decision table, plus all84 nodes/authored fields. All36 requirement IDs covered. Concrete AUTH_LOCAL, STATE_CLOCK, RESERVE_ACTIONS, MESSAGE_DELIVERY, REPORTS, ID_LINK/ID_MODE and ASSET_APPLY/SYNC_RECOVERY conditions preserve source meaning. Qualification administrator UI and fixed-lab rename now have design/API/UI/wiring/formal-verification ownership; no unsupported scope.
2. 76 ordinary PR tasks, six milestones and two external events. Concrete boundaries such as RESERVE_CREATE/RESERVE_KEY, ID_CALLBACK_MOCK/ID_MODE and SYNC_BATCH/SYNC_RECOVERY are independently defensible. Partial capabilities remain disabled until closure, and formal verification tasks return product fixes to locked implementation owners.
3. Accepted/merged prerequisites with usable contracts release delivery gates. Positive core/B/performance design precedes zero-work freeze approvals; mock UI follows contracts and WIRE_A/WIRE_B wait for real implementations. Real integration has positive effort; PROJECT_COMPLETE waits for both releases. DAG and scheduled dependency assertions passed.
4. All four exact resource identifiers and their applicability are preserved. No hidden unlocked implementation fixes in verification PRs. Actual maximum ordinary concurrency3, no duplicate active exclusive lock at any boundary; max_parallel3 matches source chapter6.
5. ASSET_READY is zero-work at abstract6; IDENTITY_READY is zero-work unknown. Exact nine-node unknown closure is blocked with null positions and correct blocking source; core and real assets remain schedulable, with no guessed external wait/calendar position.
6. Actual seven files read; Python -B full in-memory rebuilding of schedule/MD/SVG/HTML matched all four outputs byte-for-byte. Input and schedule snapshot hash2902e1a4a6abab0e6eda1534e820f67bcd795489c499d20d63158401d6efad34 is correct. CORE_FROZEN12, A_RELEASE83, B_ACTIVATE96..98 and QA_REAL_ASSET102..104 are representative abstract positions; overall endpoint unknown.
7. FIXTURE reference1 and rough ratios1/2/3; nonordinary nodeszero. Assumptions/Markdown/HTML/SVG distinguish workload, abstract position, real business deadlines and elapsed time. Scheduled ordinary finish-start equals workload; blocked hatching only conveys status.
8. English authored and fixed copy, while REQ-025 product interface remains Simplified Chinese. HTML lang=en and SVG xml:lang=en. Snapshot has59 messages and nonempty passing per-key proof; before/read/after source fingerprints and canonical English message fingerprints all match recorded proof and JSON references.
9. Actual desktop/narrow HTML, standalone SVG, D_DATA long full detail and OIDC_REAL blocked detail screens inspected. Narrow details wrap/scroll, chart horizontal overflow was deliberately operated to about690px. Clear captions/legend/markers/hatching and full detail supplement intentional title ellipses; no visual defect.
10. All seven actual measured read SHA-256 and byte sizes equal the pre-review snapshot; no missing/mismatched file. Primary immediately captured identical post-review hashes and independently checked all three tables.

### Primary adjudication and repair

No new material or minor issue was identified. This was a fresh full review of all requirements and six revised artifacts, including actual visuals and all authored fields, not a review limited to the repaired portions.
Primary verified the revised REPORTS clause against source REQ-022 and scenario23, and the added qualification/fixed-lab design, API, UI, wiring and formal-verification acceptance against REQ-013/source section3. The final complete review confirms coverage and correct language semantics; R1-F1, R1-F2 and R1-F3 are closed. All pre/read/post hashes match and every required check is complete.

### Three-way file hashes

| File | Bytes | Pre-review SHA-256 | Reviewer-read SHA-256 | Post-review SHA-256 |
| --- | ---: | --- | --- | --- |
| [requirements.md](requirements.md) | 69524 | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` |
| [plan-input-en.json](plan-input-en.json) | 172268 | `de16ee66e5f8086b3823d6e34e11a3cfcc45f12903c84f42393b772fc535359a` | `de16ee66e5f8086b3823d6e34e11a3cfcc45f12903c84f42393b772fc535359a` | `de16ee66e5f8086b3823d6e34e11a3cfcc45f12903c84f42393b772fc535359a` |
| [schedule-en.json](schedule-en.json) | 180051 | `2d98625ae2550400140c37039077b8fd48b906fc544f8cc119509637db60ac97` | `2d98625ae2550400140c37039077b8fd48b906fc544f8cc119509637db60ac97` | `2d98625ae2550400140c37039077b8fd48b906fc544f8cc119509637db60ac97` |
| [plan-en.md](plan-en.md) | 160822 | `63507e49e3d60fa01ea0c0d7b7fabf8077ebf10212107b5d0b6ed1ac6a61e2e3` | `63507e49e3d60fa01ea0c0d7b7fabf8077ebf10212107b5d0b6ed1ac6a61e2e3` | `63507e49e3d60fa01ea0c0d7b7fabf8077ebf10212107b5d0b6ed1ac6a61e2e3` |
| [gantt-en.svg](gantt-en.svg) | 208023 | `ed08f7ad809d047b5c157e3c41d6f600dc9e39f6d586013b2874bbef98e8bbbe` | `ed08f7ad809d047b5c157e3c41d6f600dc9e39f6d586013b2874bbef98e8bbbe` | `ed08f7ad809d047b5c157e3c41d6f600dc9e39f6d586013b2874bbef98e8bbbe` |
| [gantt-en.html](gantt-en.html) | 391891 | `7d4ed15f3ae403c5229a703291ad7c98b34ab00cc7105ce0f10f45bee1bdf565` | `7d4ed15f3ae403c5229a703291ad7c98b34ab00cc7105ce0f10f45bee1bdf565` | `7d4ed15f3ae403c5229a703291ad7c98b34ab00cc7105ce0f10f45bee1bdf565` |
| [locale-snapshot-en.json](locale-snapshot-en.json) | 17294 | `8612e9d5d00d46b4427dc4cbbb02473a4d43876d34b3945a33fb07d4ed115485` | `8612e9d5d00d46b4427dc4cbbb02473a4d43876d34b3945a33fb07d4ed115485` | `8612e9d5d00d46b4427dc4cbbb02473a4d43876d34b3945a33fb07d4ed115485` |

The original requirements and all six plan artifacts matched before, during, and immediately after this complete review.

## Reproduction and delivery checks

- Generation succeeded. The four canonical generator outputs were copied byte-for-byte to user-requested `-en` filenames; no generated content was hand-edited.
- A second generation from the final input and same snapshot reproduced all four output files byte-for-byte.
- Primary checks confirmed all 36 requirement IDs are covered, capacity never exceeds three ordinary tasks, resource intervals do not conflict, scheduled dependencies finish before successors start, and the unknown-external descendant closure exactly matches blocked nodes with null coordinates.
- Existing renderer regression suite: 27 tests passed; no generator or skill source was changed during this run.
- The final review hashes were checked again against all current files before this record was written.
- Remaining issues: none. Incomplete checks: none. No language default was saved.

The adjacent Chinese artifacts are archival byte copies from a different already reviewed run. Cross-language task counts, estimates, task IDs, and schedules are not acceptance constraints for this independent English run.
