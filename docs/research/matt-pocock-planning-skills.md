# Matt Pocock 规划类 Skills 研究笔记

调查日期：2026-09-30。首要依据是本机已安装的 skill 文件；上游 GitHub `main` 和 GitHub Docs 只作为补充。本文是阅读与比较，没有运行 `/to-spec`、`/to-tickets`、`/triage`，没有写 Issue、设置工具或更改任何 skill。

## 三个核心流程

| Skill | 解决什么问题 | 关键产物与边界 |
| --- | --- | --- |
| `to-spec` | 已经讨论清楚、规模大到要跨多个会话的工作，怎样把决定留给新会话 | 把既定决定综合成 spec，并先与用户确认测试 seam；spec 是决策记录和后续拆票的输入，不负责再作决定或直接代表一项实现工作。当前本机版本要求发布 tracker Issue 并加 `ready-for-agent`。来源：[本机 to-spec](<C:/Users/goey8/.codex/skills/to-spec/SKILL.md>)。 |
| `to-tickets` | 怎样把 spec 或已谈妥的计划拆成可分工、可验收的实现单元 | 每张 execution ticket 是一条窄而完整的 tracer bullet，原则上可单独演示，写清交付、验收和“Blocked by”；本地 Markdown 按依赖顺序一票一文件，真实 tracker 用原生阻塞关系。先向用户展示拆分并调整，再发布。大范围机械重构可用 expand–migrate–contract 例外。来源：[本机 to-tickets](<C:/Users/goey8/.codex/skills/to-tickets/SKILL.md>)。 |
| `triage` | 如何处理别人提交的、尚未整理的 bug、功能请求或（配置允许时）外部 PR | 检查现状与既有拒绝记录，先提出分类/状态建议并等待维护者指示；按需复现或澄清，再留下 agent brief、具体追问或关闭理由。它面向外部输入，不用来重复处理 `to-tickets` 生成的票。来源：[本机 triage](<C:/Users/goey8/.codex/skills/triage/SKILL.md>)、[agent brief 格式](<C:/Users/goey8/.codex/skills/triage/AGENT-BRIEF.md>)、[拒绝请求记录](<C:/Users/goey8/.codex/skills/triage/OUT-OF-SCOPE.md>)。 |

术语要分开看：**spec** 是已决定事项的记录；**execution ticket** 是要交付行为的实现单元；**decision ticket** 是 Wayfinder 地图下待回答的问题，回答后留下决定，本身通常不交付功能。Wayfinder 将模糊的大型工作先画成决策地图，再逐项消雾；地图清晰后回到 `to-spec`，把分散决定收拢成可执行 spec。不要把三种东西当成同一种“任务”。来源：[本机 Wayfinder](<C:/Users/goey8/.codex/skills/wayfinder/SKILL.md>)、[Ask Matt 流程路由](<C:/Users/goey8/.codex/skills/ask-matt/SKILL.md>)。

分诊状态也不等于执行状态或依赖状态。本机 triage 为每项外部输入分配一个类别（`bug` / `enhancement`）和一个状态（`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`）；`ready-for-agent` 表示说明充分、有 brief，适合交给 agent。它没有表达某项工作是否正在实现、已经完成，也不表示所有阻塞项已解除。`to-tickets` 即使给有依赖的票加 `ready-for-agent`，仍另写依赖边。因此建议将“资料已够、可委派”（triage/readiness）、“谁在做/进行到哪”（执行状态）和“被哪些未完成交付挡住”（依赖状态）分别记录和查询。来源：[本机 triage](<C:/Users/goey8/.codex/skills/triage/SKILL.md>)、[本机 to-tickets](<C:/Users/goey8/.codex/skills/to-tickets/SKILL.md>)。

特别要防住 spec 父项被自动领取：本机 `to-spec` 给 spec 加 `ready-for-agent`，但它的意义应是“足够完整，可以作为 agent 输入”，不等于“请直接实现整个 spec”。若自动化只扫描此标签，可能把父 spec 当作执行 ticket；应按记录类型排除 spec，或在自动领取前同时检查它是 execution ticket 且无未完成阻塞项。当前上游 `main` 明确指出这是风险，并建议自动 agent 排除父 spec，或拆票完成后移除其 readiness 标签；本机版本未写出这条防护。[上游 to-spec](https://github.com/mattpocock/skills/blob/main/docs/engineering/to-spec.md)。

## 给个人开发者的 tracker 入门

Tracker（任务跟踪器）是存放工作项、讨论、责任人和状态的地方；它让“想到要做”变成之后找得到、知道能否开始、知道是否做完的记录。刚开始可用仓库里的本地 Markdown：本机约定将每张票存为 `.scratch/<feature>/issues/<序号>-<slug>.md`，简单、可和代码一起管理，阻塞关系靠文字和编号、按顺序手动推进。开始接收他人请求或需要并行协作时，GitHub Issues 能承载描述、评论、指派、标签和子项；GitHub Projects 可把 Issue/PR 放进表格、看板或路线图视图，支持自定义字段（例如优先级或执行状态）。Projects 是组织和查看 Issues 的界面；Issue 仍是工作项本身。[GitHub Issues 概述](https://docs.github.com/en/issues/tracking-your-work-with-issues/learning-about-issues/about-issues)、[Projects 概述](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)。

依赖关系应另建阻塞边，而非只写“先做 A”。GitHub Issues 支持 `blocked by` / `blocking` 原生关系，Issue 页面和 Project 可以显示阻塞；CLI 也能读写这些关系。由此，某张票“说明已齐”可以和“现在能开工”同时保持为两个问题：是否 ready 看 brief，是否可开工看阻塞边是否清空；是否正在进行或已完成则看执行状态/关闭状态。[GitHub issue dependencies 文档](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies)。

## 与 project-planner 的有限对照

本项目 [project-planner skill](<D:/strange tools/project-planner/project-planner/SKILL.md>) 生成按 PR 边界组织的本地规划；其 [schema](<D:/strange tools/project-planner/project-planner/references/schema.md>) 明确区分交付依赖、资源互斥、粗略相对工作量、外部事件和里程碑。一个普通 planner task 可以映射到 execution ticket，但它们不是同一数据结构：planner 还负责需求追踪和相对排程；triage 状态不应代替 planner 的依赖和任务状态。

有限建议：功能工作优先检查 ticket 是否能展示一条端到端行为路径；若先做接口契约、存储基础或其他前置 PR，应说明它为何独立可验收、后续为何依赖它。按层拆分本身不足以判错：如果契约/存储工作有自己的验收，并允许 UI 用 mock 独立验证，就可能是合适的序列。planner 已有“依赖在前置交付验收并合并后释放”的规则，可用于避免把“已拆票”误当成“可开工”。新增执行流程时，再明确分开 readiness、执行状态与依赖是否清空；尤其别让仅按 `ready-for-agent` 拉取的扫描器领取 spec 父项。这些是依据 skills 与 schema 的建议，不是本次对规划器或 skills 的改动授权。

## 可以借鉴的工作理念与相关 skills

这套流程把查明事实与作出决定分开：grilling 要求 agent 自行查找环境事实，将产品决策交给用户；决策的前置条件未解决时，不提前询问依赖它的问题。`grill-with-docs` 同时调用 grilling 和 domain-modeling，把已澄清的术语及时记入词汇表，重要而难逆转的取舍酌情记录为 ADR。ADR 不是每个小决定都要写：本机要求同时满足难逆转、缺少背景会令人意外、存在真实取舍。来源：[grilling](<C:/Users/goey8/.codex/skills/grilling/SKILL.md>)、[grill-with-docs](<C:/Users/goey8/.codex/skills/grill-with-docs/SKILL.md>)、[domain-modeling](<C:/Users/goey8/.codex/skills/domain-modeling/SKILL.md>)。

prototype 用可运行的廉价原型回答一个明确的设计问题；research 用第一手资料回答事实问题；两者为规划提供证据，不代替用户作决定。实现阶段通过 tdd 在约定接口验证行为，code-review 分别检查符合需求与符合代码规范，避免“写得规范但做错功能”被另一维掩盖。小到一次会话能完成的工作可以跳过完整 spec 和拆票流程。来源：[prototype](<C:/Users/goey8/.codex/skills/prototype/SKILL.md>)、[research](<C:/Users/goey8/.codex/skills/research/SKILL.md>)、[tdd](<C:/Users/goey8/.codex/skills/tdd/SKILL.md>)、[code-review](<C:/Users/goey8/.codex/skills/code-review/SKILL.md>)、[流程路由](<C:/Users/goey8/.codex/skills/ask-matt/SKILL.md>)。

对 planner 的改进优先级建议：先检查重大决策是否已明确，再拆分任务；保留普通细节的显式保守假设，重大业务分歧不能伪装成估算假设。每项任务补清当前行为、期望行为、关键接口、非目标与验收方式；通过“完成后能展示什么”检验功能任务粒度。新功能验收应有明确的失败观察，但回归保护标准可以在基线已经通过。可选生成一任务一文件的本地简报，以现有稳定任务 ID 对应；描述仍由同一规划输入生成，实际执行记录与规划排程分别维护。这些都是主代理的设计建议，尚未实现。

不建议照搬极长用户故事、固定 token 数、每个接口都向用户确认的仪式，或直接在 planner 中加入自动发布与实现流程。文档完整性应由覆盖、验收与证据衡量；并行开工还须符合本项目资源和容量约束。项目层面明确拒绝的能力可以借鉴 `.out-of-scope/` 的持久理由记录，但“本轮不做”和“暂时延后”不能自动解释为永久拒绝。来源：[本机 to-spec](<C:/Users/goey8/.codex/skills/to-spec/SKILL.md>)、[拒绝请求记录](<C:/Users/goey8/.codex/skills/triage/OUT-OF-SCOPE.md>)；取舍为主代理建议。

## 版本与资料边界

对照的是 2026-09-30 可见的上游 `main` 页面，不是固定 commit，之后可能变化。上游 `main` 的 `to-spec` / triage / Ask Matt / domain-modeling 资料已使用 `GLOSSARY.md` 记录术语；本机 [domain-modeling](<C:/Users/goey8/.codex/skills/domain-modeling/SKILL.md>) 与 [Ask Matt](<C:/Users/goey8/.codex/skills/ask-matt/SKILL.md>) 仍以 `CONTEXT.md` 为术语记录。另一个已核实的差异是上游 to-spec 的解释文档补充了 spec readiness 标签与自动领取风险说明；核心工作流仍可按本机文件理解，本报告不把上游改动视为本机已安装行为。[上游 domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md)、[上游 to-spec 解释文档](https://github.com/mattpocock/skills/blob/main/docs/engineering/to-spec.md)。

本次还阅读了 [setup-matt-pocock-skills](<C:/Users/goey8/.codex/skills/setup-matt-pocock-skills/SKILL.md>)、[grilling](<C:/Users/goey8/.codex/skills/grilling/SKILL.md>)、[prototype](<C:/Users/goey8/.codex/skills/prototype/SKILL.md>)、Wayfinder 及 triage 附属文档；这里只将它们作为上下游参考，没有实际配置 tracker、运行 grilling/prototype 或处理 Issue。本仓库当前选用哪一种 tracker 未在本次范围内核实，标记为未知。
