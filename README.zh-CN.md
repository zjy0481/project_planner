# project-planner

这是一个必须显式调用的 Codex 技能：它把需求文档拆成可独立开发、测试和审查的 PR 任务，并生成受依赖与资源约束的相对排程、甘特图和本地项目计划。它只创建本地规划产物，不创建 Issue 或 PR，也不实现项目代码。

English: [README.md](README.md)

## 安装技能

通过 AI 安装时，请从[源仓库](https://github.com/zjy0481/project_management/tree/dev/project-planner)的 `dev` 分支安装，并且只安装其中的 `project-planner` 目录。不要假设 `main` 分支包含此技能。

优先使用已安装的 `$skill-installer`，并传入以下完整 URL：

```text
https://github.com/zjy0481/project_management/tree/dev/project-planner
```

URL 中的 `/tree/dev/` 不可省略；省略后安装器可能选用默认分支。若需手动安装，请将完整技能目录复制到以下一个作用域：

```text
仓库作用域：<your-repo>/.agents/skills/project-planner
用户作用域：~/.agents/skills/project-planner
来源目录：  <checkout>/project-planner
```

请保留完整目录树，包括 `config.json`、`agents/openai.yaml`、`references/` 和 `scripts/`（含配置助手与语言资源）。不要只复制 `SKILL.md` 或扁平化目录，也不要覆盖已有安装。更新技能时保留用户已有的配置、自定义字段和 `user-locales/` 运行时文案包。运行时语言包仅保存在本地，不随技能源码发布。安装目录旁的 `config.json` 由使用该安装副本的项目共享，它与 Codex 设置分开。

安装工具可能使用环境配置的旧式 `.codex/skills` 目录；请遵循工具报告的位置，不要创建重复副本。OpenAI [Codex Skills 官方文档](https://developers.openai.com/zh-Hans/docs/build-skills)介绍了受支持的 `.agents/skills` 目录。

用户未明确要求安装时，代理不得自行安装或更改安装目录。经授权安装后，应检查安装目录名称、`policy.allow_implicit_invocation: false` 是否保留、生成器的 `--help` 是否成功、技能发现是否能看到该技能，以及准确安装路径。

还应验证两种内置语言都能生成有效快照。临时输出请放在技能安装目录之外：

复制目录时请保留技能内隐藏的 `.gitattributes` 文件。它将三份指纹来源的 Git 检出换行固定为 LF；手动转成 CRLF 会使原始字节基线失效，即使文本内容未变。

```text
python -X utf8 "<skill-dir>/scripts/localization.py" snapshot --language en --output "<temporary-dir>/project-planner-en-snapshot.json" --skill-dir "<skill-dir>"
python -X utf8 "<skill-dir>/scripts/localization.py" snapshot --language zh-CN --output "<temporary-dir>/project-planner-zh-CN-snapshot.json" --skill-dir "<skill-dir>"
```

两个命令都必须成功退出并创建快照。任一命令失败，都表示安装副本的内置来源基线当前不可用；请报告失败，不要改写源哈希或审查证据。

## 使用技能

提供需求文档并显式调用 `$project-planner`，例如：

```text
使用 $project-planner，根据 docs/requirements.md 制定项目计划。
最多安排两个普通任务同时开发，不需要具体日期。
请生成甘特图并完成独立审查。
```

技能会在指定目录生成 `plan.md`、`schedule.json`、`gantt.svg`、`gantt.html` 和 `review.md`。可以先用浏览器打开 `gantt.html` 查看任务、依赖和详情，再读 `plan.md` 查看需求映射、假设、交付物、验收条件与估算。HTML 文件自包含，可离线查看。GitHub 会将其显示为源码；下载后用本地浏览器打开即可交互查看任务详情。

生成器需要 Python 3.10 或更高版本，并且只使用 Python 标准库。

产物语言按以下顺序确定：本次对计划的明确要求、正在更新的既有计划所记录的语言、已保存的技能默认语言、用户当前实质性请求的主要语言；若调用只有技能标记、没有实质性语言上下文，则使用英文。源文档、文件内容和零散外语词不决定对话语言；只有明显混合的实质内容导致目标不清楚时才询问。内置文案支持简体中文（`zh-CN`）和英文（`en`）；其他合法语言标签需要先准备完整、当前且通过语义核验的文案包，详见[本地化流程](project-planner/references/localization.md)。新安装的 `language: null` 不会触发开始时的询问。计划生成且完整审查通过后，技能可提示是否将本次实际使用的语言保存为默认值；只有用户明确要求才会保存，翻译文案也不会改变这个偏好。省略 `language` 的旧输入仍可使用，生成器会默认输出英文；没有文案快照的旧英文、中文输入仍兼容。技能流程会显式写入实际语言及计划本地文案快照。英文指令不会强制英文产物。

技能配置还支持 `max_parallel` 和 `max_review_revisions` 默认值。新计划优先采用用户或项目明确给出的同时开发任务数（包括明确说明容量未知），其次才采用技能默认值；两者都未提供时记录容量未知，并展示不设容量上限的理论并行。`max_parallel` 限制的是计划中的普通任务，不限制代理或审查代理。更新既有计划时，除非用户要求更改，否则保留原容量。计划审查默认最多进行两轮初审后的完整修订与复审；即使设为 0，完整的初次独立审查仍必须执行。准备新语言文案有单独的上限：一次完整初审加最多两轮完整修订复审，不占用计划审查轮次。

### 甘特图表示什么

图中 `T+0`、`T+1` 等位置只表达相对顺序。普通任务条长表示粗略相对工作量，一个单位不对应固定的小时或工作日，技能也不预测现实日历工期。估算时先选一个简单任务作为 1，再大致比较其他任务的工作量。

依赖表示交付门槛：前置工作完成开发、验收通过、PR 合并且接口或数据契约可用后，下游才能开始。共享人员、环境或其他互斥资源由资源锁表示。未知外部就绪条件会阻塞该事件及其后代；如填写已知相对位置，它只是规划假设，不是日历日期。其他不受影响的工作仍可排程。

### 独立审查

每份计划都要经过只读独立审查：使用 `gpt-6.1-sol`、`high` 推理强度、`fork_turns="none"`，并实际查看渲染后的甘特图与 HTML 详情。审查者会对照需求、计划输入、四种生成产物和 `locale-snapshot.json`，逐文件比对审查前、审查者所读、审查后三份 SHA-256。若指定模型、代理、视觉检查或哈希校验无法完成，结果会保留为待决草稿并说明原因。修订轮次上限不会关闭初次审查；每次修订都由新的独立子代理按相同完整范围复审。

### 示例

简体中文示例：[规划文档](demo/plan.md) · [静态甘特图](demo/gantt.svg) · [交互式甘特图](demo/gantt.html)

英文示例：[规划文档](demo/en/plan.md) · [静态甘特图](demo/en/gantt.svg) · [交互式甘特图](demo/en/gantt.html) · [排程数据](demo/en/schedule.json)

日语示例：[规划文档](demo/ja/plan.md) · [交互式甘特图](demo/ja/gantt.html) · [已核验文案快照](demo/ja/locale-snapshot.json)

GitHub 会把 HTML 显示为源码。请下载后用本地浏览器打开，以查看任务详情交互。

<details>
<summary>开发者：重建示例与运行测试</summary>

在仓库根目录运行以下命令，可根据已有输入重建产物并运行测试。生成器只读取输入文件，不会重新分析需求或调用 AI 审查。

```text
python -X utf8 project-planner/scripts/build_plan.py tests/fixtures/plan.json --output .tmp/project-planner-example
python -X utf8 -m unittest discover -s tests -v
```

如果输出目录中有同名且非本工具生成的文件，生成器会拒绝覆盖。完整数据契约见[输入说明](project-planner/references/schema.md)，规划流程见[技能说明](project-planner/SKILL.md)。

</details>
