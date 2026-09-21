# project-planner

这是一个必须显式调用的 Codex 技能：它把需求文档转换为可独立审查的 PR 任务、受依赖和资源约束的相对排程，以及带甘特图的本地项目计划。它只写入本地规划产物，不创建 Issue 或 PR，也不实现业务代码。

English: [README.md](README.md)

## 面向 AI 代理：安装技能

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

## 面向人类：使用技能并查看产物

技能读取完整需求文档，追踪每条需求对应的任务，区分交付依赖和精确匹配的资源锁，并在 `max_parallel` 约束下排程普通任务。未知外部就绪时间会阻塞该事件及其后代，但不相关的工作仍可排程。列表排程按输入顺序确定性执行，但不保证全局最优。

运行时需要 Python 3.10 或更高版本，只使用 Python 标准库。请显式调用，例如：

```text
使用 $project-planner 读取 requirements.md，为这个功能创建本地项目计划。
```

流程是“需求 → 计划与排程 → 图表产物 → 独立审查”。最终审查需要独立代理工具使用 `gpt-5.6-sol` 模型和 `high` 推理强度，并通过真实浏览器或图像视觉检查查看渲染后的甘特图。任一能力不可用时，审查都必须明确标记为未完成；不能静默改用主代理自审或只检查源文件。

生成成功后，生成器从同一个排程对象写出四个文件：

- `plan.md`：包含需求映射、假设、风险、排程和任务详情的中文项目计划；
- `schedule.json`：经过校验的输入和确定性排程数据；
- `gantt.svg`：适合嵌入的静态图表；
- `gantt.html`：离线、自包含且可交互的图表。

计划和图表中的生成文本为中文。仓库中的示例产物如下：

![甘特图示例](demo/gantt.svg)

[查看示例计划](demo/plan.md) · [查看交互式 HTML 源码](demo/gantt.html) · [查看示例排程](demo/schedule.json)

GitHub 会把 `demo/gantt.html` 显示为源码；下载后在本地打开，才能使用任务详情交互功能。

完整流程还会在 `review.md` 中记录审查证据。下面的 Python 命令只会根据已有的计划 JSON 重建四个生成产物；它不会理解需求文档，也不会调用 AI 审查者。

要复现示例，请使用与输入 fixture 不同的输出目录：

```text
python -X utf8 project-planner/scripts/build_plan.py tests/fixtures/plan.json --output .tmp/project-planner-example
python -X utf8 -m unittest discover -s tests -v
```

如果同名输出文件不是生成器产物，生成器会拒绝覆盖。完整输入契约见 `project-planner/references/schema.md`，工作流边界见 `project-planner/SKILL.md`。
