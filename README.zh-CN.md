# project-planner

这是一个必须显式调用的 Codex 技能：它把需求文档转换为可独立审查的 PR 任务、受依赖和资源约束的相对排程，以及带甘特图的本地项目计划。它只写入本地规划产物，不创建 Issue 或 PR，也不实现业务代码。

English: [README.md](README.md)

## 供AI阅读：如何安装技能

请从[源仓库](https://github.com/zjy0481/project_management/tree/dev/project-planner)的 `dev` 分支安装，并且只安装其中的 `project-planner` 目录。不要假定 `main` 分支包含此技能。

优先使用已安装的 `$skill-installer`，并传入这个完整 URL：

```text
https://github.com/zjy0481/project_management/tree/dev/project-planner
```

URL 中的 `/tree/dev/` 不可省略；省略后安装器可能使用默认的 `main` 引用。如果必须手动安装，请保留完整目录树及其元数据，并根据选择的作用域只复制到一个目标：

```text
仓库作用域：<your-repo>/.agents/skills/project-planner
用户作用域：~/.agents/skills/project-planner
来源目录：  <checkout>/project-planner
```

不要覆盖已有目标。不要扁平化目录或只复制 `SKILL.md`；必须保留 `agents/openai.yaml`、`references/` 和 `scripts/`。根据 [OpenAI Skills 官方文档](https://developers.openai.com/zh-Hans/docs/build-skills)，`.agents/skills` 是受支持的目录。已安装的工具也可能使用环境配置的旧式 `.codex/skills` 目录，因此应遵循工具报告的目标位置，不要创建重复副本。

在获得明确安装授权后，检查以下事项：

- 安装目录名称确实是 `project-planner`；
- `agents/openai.yaml` 仍保留 `policy.allow_implicit_invocation: false`；
- `python -X utf8 "<skill-dir>/scripts/build_plan.py" --help` 成功；
- 技能发现或刷新操作能够看到该技能；
- 代理报告准确的安装位置。

仅阅读或编辑本 README 不构成安装请求。没有用户明确请求时，代理不得安装技能或修改配置。

## 面向使用者：如何使用技能并查看结果

准备好一份需求文档，调用 `project-planner`，就可以得到一份开发计划和对应的甘特图。它会把需求拆成便于分别开发、测试和提交 PR 的小任务，帮助你看清：

- 每个任务要做什么，以及怎样才算完成；
- 哪些任务可以同时开工，哪些必须等前面的任务完成；
- 各项工作的工作量大致相差多少，整个项目按什么顺序推进。

### 甘特图中的时间是什么意思？

这条时间轴用来比较工作量、展示任务的先后与并行关系。图中使用 `T+0`、`T+1` 等相对位置，一个单位不对应固定的小时数或工作日数。实际耗时取决于开发效率、人员安排和等待情况，技能不会据此估算项目需要多少天。

估算时，可以选一个简单任务作为 1 个相对工作单位，再粗略比较其他任务的大小。例如，A 的工作量大约是 B 的两倍，就将 A 记为 2，B 记为 1。如果 B 依赖 A，A 可以安排在 `T+0 → T+2`，B 安排在 `T+2 → T+3`；如果两者独立，而且人员和资源允许，也可以都从 `T+0` 开始。

因此，看条长可以比较工作量，看位置和箭头可以了解开发顺序。比例只需大致合理，无需精确到小数；A 的条长是 B 的两倍，也不意味着现实耗时一定是两倍。等待外部交付的条件会单独标明，未知条件保持阻塞；图中若给出外部条件的相对位置，会说明它是规划假设。

### 如何开始

安装后，在对话中明确写出 `$project-planner`，并提供需求文档的路径，或者直接粘贴需求内容。例如：

```text
使用 $project-planner，根据 docs/requirements.md 制定开发计划。
最多安排两个任务同时开发，不需要具体日期。
请生成甘特图和中文规划文档，并完成独立审查。
```

这个技能需要你**显式调用**，不会仅因为对话中提到了项目规划就自动运行。如果你知道参与人数、可同时开展的任务数量或需要等待的外部条件，也可以一并说明。

技能会先拆分任务、安排先后顺序，再生成图表和文档，最后交给独立子代理审查。对于暂时无法确定的条件，它会在计划中说明。例如，某项工作需要等待尚未交付的接口，就会标为等待状态；其他不受影响的任务仍可安排。

### 结果怎么看

通常先看这两个文件就够了：

- **`gantt.html`：看整体安排。** 用浏览器打开，可以比较任务的相对工作量，查看并行安排和依赖关系；点击任务，还能看到交付内容、验收条件和 PR 范围。文件可离线查看。
- **`plan.md`：看具体怎么做。** 这是一份中文规划文档，包含任务说明、完成标准、估算依据，以及需要注意的假设和风险。

此外，`gantt.svg` 是便于插入文档的静态甘特图，`review.md` 记录审查结论与发现的问题。`schedule.json` 保存任务和相对排程的数据，日常查看计划时不必阅读它。

生成的计划和图表以中文呈现。以下是示例：

![甘特图示例](demo/gantt.svg)

[阅读示例规划文档](demo/plan.md) · [获取交互式甘特图](demo/gantt.html)

GitHub 会将 HTML 文件显示为源码。请下载 `gantt.html`，再用本地浏览器打开，即可查看图表和点击任务详情。

### 使用前需要知道

运行环境需要 Python 3.10 或更高版本，生成图表不需要额外安装 Python 库。完整审查还需要环境支持调用 `gpt-5.6-sol`、`high` 推理强度的独立子代理，并能查看实际渲染的图表。如果这些能力不可用，技能会明确说明审查尚未完成。

计划会考虑任务依赖、可同时开展的任务数量，以及共用人员或环境造成的冲突。它提供一份可讨论、可调整的开发安排，不保证找到最优排布，也不会替你创建 PR 或开始编写项目代码。

<details>
<summary>开发者：重建示例与运行测试</summary>

在仓库根目录运行以下命令，可以根据已有的示例数据重新生成图表和规划文档，并运行测试。这只是检查生成工具，不会重新分析需求或调用 AI 审查。

```text
python -X utf8 project-planner/scripts/build_plan.py tests/fixtures/plan.json --output .tmp/project-planner-example
python -X utf8 -m unittest discover -s tests -v
```

如果输出目录已有同名文件，且该文件不是本工具生成的，工具会拒绝覆盖。数据格式见[输入说明](project-planner/references/schema.md)，完整工作流程见[技能说明](project-planner/SKILL.md)。

</details>
