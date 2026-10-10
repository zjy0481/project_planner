# LabFlow planning demo

LabFlow is a fictional shared-laboratory booking and operations platform. Start with the [approved requirements](requirements.md) or the [test guide](test-guide.md). The requirements define 36 items, separate core and enterprise releases, three concurrent ordinary tasks, four exclusive resources, and two external integration gates.

## Simplified Chinese artifacts

- [Project plan](plan-zh-cn.md)
- [Interactive Gantt chart](gantt-zh-cn.html)
- [Static Gantt chart](gantt-zh-cn.svg)
- [Planning input](plan-input-zh-cn.json)
- [Schedule data](schedule-zh-cn.json)
- [Verified fixed-message snapshot](locale-snapshot-zh-cn.json)
- [Independent review record](review-zh-cn.md)

These seven files are byte-for-byte demonstration copies of the reviewed artifacts originally generated in `docs/plans/labflow/`. Their recorded review paths refer to that original run; copying does not constitute another review. The snapshot reference remains valid because the seven files are kept together. The source requirements have not changed.

The local `.gitattributes` files preserve the original bytes of the reviewed source and language-suffixed artifacts, including their original line endings. Keep these hidden files when copying or checking out the demo so that review hashes remain valid across platforms.

## English artifacts

This example was independently planned from the same approved requirements. Its task boundaries and estimates need not match the Chinese example. Status: **passed review — PASS**, after an initial review and one full repair/review cycle, each using a fresh `gpt-6.1-sol/high` reviewer with no parent history. The final plan covers 36 requirements in 84 nodes, including 76 ordinary PR tasks.

- [Project plan](plan-en.md)
- [Interactive Gantt chart](gantt-en.html)
- [Static Gantt chart](gantt-en.svg)
- [Planning input](plan-input-en.json)
- [Schedule data](schedule-en.json)
- [Verified fixed-message snapshot](locale-snapshot-en.json)
- [Independent review record](review-en.md)

## Reading the demonstration

The repository's [English README](../../README.md#preview) and [Simplified Chinese README](../../README.zh-CN.md#效果预览) show screenshots of their corresponding plans. The screenshots are browser captures of the reviewed HTML artifacts; the overview shows only the beginning of each full chart, and the task-detail dialog is scrollable.

- English screenshots: [Gantt preview](images/labflow-gantt-en.jpg) · [Task details](images/labflow-detail-en.jpg)
- Simplified Chinese screenshots: [Gantt preview](images/labflow-gantt-zh-cn.jpg) · [Task details](images/labflow-detail-zh-cn.jpg)

Local screenshot copies and their [source hashes and image-host URLs](images/previews.json) are kept in `images/`. README images were uploaded with PicGo's named `project planner` configuration.

Download the HTML chart and open it locally to inspect task details; GitHub shows HTML source. The chart is self-contained and works offline. The SVG can be viewed directly. Keep the planning input and locale snapshot together when rebuilding.

The bars show rough relative workload. `T+N` gives an abstract position, with no conversion to hours, working days, or calendar dates. Asset sandbox readiness at `T+6` is an explicit planning assumption. Enterprise identity readiness is unknown, so its real-integration branch and release B remain blocked; release A can proceed independently.

Review `PASS` means that the planning artifacts passed review. It does not mean the fictional product has been implemented, tested, or accepted. Independently generated language examples may use different task boundaries and estimates; they are not synchronized translations. LabFlow's own product interface must still be Simplified Chinese under REQ-025.

## Rebuilding the reviewed model

From the repository root, rebuild the Chinese input into a separate temporary directory:

```text
python -X utf8 project-planner/scripts/build_plan.py demo/labflow/plan-input-zh-cn.json --output .tmp/labflow-zh-cn-rebuild
python -X utf8 project-planner/scripts/build_plan.py demo/labflow/plan-input-en.json --output .tmp/labflow-en-rebuild
```

The generator produces its standard `plan.md`, `schedule.json`, `gantt.svg`, and `gantt.html` filenames. The language suffixes in this demo were applied through exact byte copies. Rebuilding does not perform another AI review. A changed input, message snapshot, or rendered artifact needs a new complete independent review before reusing a `PASS` claim.
