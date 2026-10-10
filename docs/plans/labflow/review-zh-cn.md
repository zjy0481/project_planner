# LabFlow 简体中文计划审查记录

最终状态：**已通过审查（PASS）**。初审后使用了 1 轮完整修订复审；上限为 2，尚余 1 轮但当前无需继续。此结论针对计划与图表质量，不表示 LabFlow 产品功能已实现或已实跑通过。

## 来源与本次设置

- 原始需求：`D:/strange tools/project-planner/demo/labflow/requirements.md`，v1.1；原文保持不变，36 条需求、32 个验收场景及已确认决定为权威来源。
- 输出语言：`zh-CN`，选择原因是用户明确指定简体中文。技能安装配置的 `language` 仍为 `null`，本次不保存默认语言。
- 文件名：按用户要求使用 `-zh-cn` 后缀。未来其他语言版本可以独立规划、估算和审查，无跨语言语义一致要求。
- 计划容量：`max_parallel=3`，来自需求第 6 节。审查代理容量与该值无关。
- 冻结计划修订上限：`max_review_revisions=2`，初审前从技能配置读取；此后未变更。
- 固定文案消息 SHA-256：`a6c2fc8abfad863323b05e0c2f2dce903ee4715242add339d8a646c5d710cf2f`。快照保存完整 59 项文案、来源/上下文指纹及实际独立逐键核验凭据。

## 计划概览与限制

- 67 个节点：60 个独立 PR 普通任务、5 个内部状态里程碑、2 个外部事件；全部 36 条需求均有普通任务覆盖。
- 正工作量契约设计/评审/修订与零工作量冻结分开；mock 开发与真实接线/正式验收分开；依赖仅在前置完成、验收、合并且接口可用后释放。
- 四种精确互斥锁为 `backend-lead`、`frontend-lead`、`db-reviewer`、`qa-shared-env`。全任务区间检查没有重叠冲突，普通任务并行峰值为 3。
- T01 基础健康检查为工作量参考 1，其他 1/2/3 是粗略比例。横轴、起止和 T+N 都是抽象相对位置，不是小时、工作日、日历日期或实际经过工期。
- 阶段 A 的 MA 位于抽象 T+60，可独立交付；资产真实验收 V08 位于 T+66。T+66 是当前可排程分支终点，不能作为整个项目的结束时间。
- E-ASSET 假设在抽象 T+6 提供真实沙箱/文档/令牌/样例；真实接入自身仍有正工作量。E-SSO 的实际资料就绪未知；E-SSO/J05/J07/V07/V10/W03/A02/MF 共 8 个节点保留 blocked、起止 null。
- 本次未执行虚拟产品的代码实现、实际提供方接入、性能/恢复/升级演练；这些工作与双代表验收都明确安排在计划中。真实性能等未完成条件将阻止对应产品阶段放行。

## 生成与可复现性

使用 `project-planner/scripts/localization.py snapshot` 生成经验证的计划快照。生成器读取 `plan-input-zh-cn.json` 与该相对引用快照，不读取可变全局配置。
由于生成器固定四个标准输出文件名，先生成到 `.tmp/labflow-plan-zh-cn/generated/`，再按用户要求逐字节复制为语言后缀文件；没有手工编辑主输出内容。复制前校验 JSON generator 或真实生成标记，保护非本技能文件。四项最终输出与生成结果逐字节相同，第二次独立生成也逐字节相同。

## 第一轮完整独立审查

- 审查者：`/root/labflow_zh_cn_plan_review_r1`；`gpt-6.1-sol` / `high` / `fork_turns=none`；只读，不继承 Primary 对话。
- 决策：`REVISE`；十项检查均完成，视觉核验 `complete`，1 个 material 和 2 个 minor 问题。
- 视觉方法：mcp__cua_repl 实际渲染 HTML 与独立 SVG，查看首部、核心验收段、阻塞段和尾部；打开 C01/J05/V03/MF 详情，并滚动 C01 长详情末尾。图片仅工具内联显示，未在项目文档嵌入未追踪图片。
- 来源全读、36 条原文比较、PR 边界、交付门、锁/容量、外部阻塞、全输出内存重建一致、语言及快照凭据、工作量语义、真实视觉与七文件稳定性均检查；七文件审前/所读/审后值一致。

### Primary 逐项裁定与修复

- **R1-F1（material）：采纳**。位置：V03 验收第3项、最后一项横向假设。证据：原 V03 要求 REQ-001～026/031～036 全核心无未运行，但只依赖 U07/U08/U09/V02；原 V03 T+54～57、正式性能 V04 T+57～59。A01 已明确依赖 V03/V04/V05/V06/W01，才是合法全量门。 修复：收窄 V03 至浏览器/响应式/文本安全/无障碍；追踪索引中其他证据待对应任务补齐；修改假设，由 A01 汇总全核心。未添加资源串行伪依赖。
- **R1-F2（minor）：采纳**。位置：C03 验收第2项。证据：原摘要同值冲突缺少内容条件；需求 REQ-029 与 J02 明确等时同内容跳过、异内容冲突。 修复：明确旧来源时间跳过、等时同内容跳过/异内容冲突、更新原子提交。
- **R1-F3（minor）：采纳**。位置：gantt SVG/HTML J06/J08/V08 尾端标签。证据：Primary 与独立审查实际截图均见覆盖。原 V08 时间标签起点x1067，而资源起点x1078；短条标签总是置于条右侧。 修复：源绘图脚本仅在右侧空间不足时将短条位置文字放在条左侧，保持条长/坐标/排程和资源内容；增加空间区域回归测试，27项生成器测试全部通过。

绘图修复仅涉及 `project-planner/scripts/build_plan.py` 的短条位置文字锚点，以及 `tests/test_build_plan.py` 的区域边界回归测试。没有改变排程、条长、资源、固定文案或协议。原渲染器在同一回归测试中产生两个末端越界失败，修复后通过。该修复属于本次真实生成暴露的可读性问题，不扩展技能流程。

### 第一轮三方哈希

| 文件（相对项目根） | 字节数 | 审前 SHA-256 | 审查者所读 SHA-256 | 审后 SHA-256 |
| --- | ---: | --- | --- | --- |
| `demo/labflow/requirements.md` | 69524 | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` |
| `docs/plans/labflow/plan-input-zh-cn.json` | 149565 | `d5ebf3b1f9318ccee2c876f334c10ef02727f41ec86d798badc571cfc953fdd1` | `d5ebf3b1f9318ccee2c876f334c10ef02727f41ec86d798badc571cfc953fdd1` | `d5ebf3b1f9318ccee2c876f334c10ef02727f41ec86d798badc571cfc953fdd1` |
| `docs/plans/labflow/schedule-zh-cn.json` | 155656 | `55833c47832577cc83083ac016826dec5732d07ec63a43c486b6a6fedc5cb3cd` | `55833c47832577cc83083ac016826dec5732d07ec63a43c486b6a6fedc5cb3cd` | `55833c47832577cc83083ac016826dec5732d07ec63a43c486b6a6fedc5cb3cd` |
| `docs/plans/labflow/plan-zh-cn.md` | 133487 | `3aa58159a2ea92f7173f200ee0b0806af30af4c4064907e0919867f3caec9973` | `3aa58159a2ea92f7173f200ee0b0806af30af4c4064907e0919867f3caec9973` | `3aa58159a2ea92f7173f200ee0b0806af30af4c4064907e0919867f3caec9973` |
| `docs/plans/labflow/gantt-zh-cn.svg` | 156221 | `2c0aca8ac220fa4a5564f4ac12620732ba1629df9956e0f10442d1077ccbeb07` | `2c0aca8ac220fa4a5564f4ac12620732ba1629df9956e0f10442d1077ccbeb07` | `2c0aca8ac220fa4a5564f4ac12620732ba1629df9956e0f10442d1077ccbeb07` |
| `docs/plans/labflow/gantt-zh-cn.html` | 345521 | `a436bc383df2a474b9c25118d9956e410fd8cc04771424a38c948d6a38c7888b` | `a436bc383df2a474b9c25118d9956e410fd8cc04771424a38c948d6a38c7888b` | `a436bc383df2a474b9c25118d9956e410fd8cc04771424a38c948d6a38c7888b` |
| `docs/plans/labflow/locale-snapshot-zh-cn.json` | 17106 | `5d05ca2137a41fdaddd0064ba73857c1bddf457a9fbaab79e3f05b8a6d9e1408` | `5d05ca2137a41fdaddd0064ba73857c1bddf457a9fbaab79e3f05b8a6d9e1408` | `5d05ca2137a41fdaddd0064ba73857c1bddf457a9fbaab79e3f05b8a6d9e1408` |

## 第二轮完整独立复审

- 审查者：`/root/labflow_zh_cn_plan_review_r2`；`gpt-6.1-sol` / `high` / `fork_turns=none`；全新只读代理，检查完整七文件与全部十项要求。
- 决策：`PASS`；视觉核验 `complete`。
- 视觉方法与证据：mcp__cua_repl 的 Codex In-app Browser 实际渲染 HTML 与独立 SVG，查看首/中/尾和阻塞区、U03/V10 长详情；360px 下 V10 顶部及底部正常换行，clientWidth=scrollWidth=289，无横向溢出。末端短条位置标签已向左放置，不进入右侧说明栏。临时 viewport 已重置、审查标签关闭。
- 审查证据：完整读取需求和全部67节点，36需求正文一致；60普通任务独立PR边界，交付冻结和真实/mock门符合需求；资源锁无冲突、峰值3；精确阻塞闭包8项；只读内存重建 schedule/MD/SVG/HTML 全文相同；工作量及抽象轴无时间换算；快照59消息与逐键证据/来源/三方指纹有效；七文件读取与收尾哈希全部匹配；未发现 material/minor 问题。
- 发现与裁定：未发现问题；Primary 对照原需求、实际输入与生成文件确认三项初审问题均已修复，无剩余确认问题或不完整检查。

### 最终七文件三方哈希与六份产物字节数

| 文件（相对项目根） | 字节数 | 审前 SHA-256 | 审查者所读 SHA-256 | 审后 SHA-256 |
| --- | ---: | --- | --- | --- |
| `demo/labflow/requirements.md` | 69524 | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` | `f4139490c022f7e36498cf440704b34d4c3df2c7cde8b1a5321bf1c0f80175e4` |
| `docs/plans/labflow/plan-input-zh-cn.json` | 150091 | `b30e60f0694a58d105559c05c700b84e6a5dc4025169f17c0455b4674adfbad3` | `b30e60f0694a58d105559c05c700b84e6a5dc4025169f17c0455b4674adfbad3` | `b30e60f0694a58d105559c05c700b84e6a5dc4025169f17c0455b4674adfbad3` |
| `docs/plans/labflow/schedule-zh-cn.json` | 156182 | `1b36bf2af3bd8b08d2456a592166170dc1364baa3b182eaf2abe68e7c3bbf5bd` | `1b36bf2af3bd8b08d2456a592166170dc1364baa3b182eaf2abe68e7c3bbf5bd` | `1b36bf2af3bd8b08d2456a592166170dc1364baa3b182eaf2abe68e7c3bbf5bd` |
| `docs/plans/labflow/plan-zh-cn.md` | 134013 | `6b438d1ce814081b950489d3891e5e6100bb762b16155eb2bb663cd5aae484e9` | `6b438d1ce814081b950489d3891e5e6100bb762b16155eb2bb663cd5aae484e9` | `6b438d1ce814081b950489d3891e5e6100bb762b16155eb2bb663cd5aae484e9` |
| `docs/plans/labflow/gantt-zh-cn.svg` | 157667 | `0771d05625f6a64c8dfb821529b4cbc3666ee44da8bcda8aa8629bc73762ec84` | `0771d05625f6a64c8dfb821529b4cbc3666ee44da8bcda8aa8629bc73762ec84` | `0771d05625f6a64c8dfb821529b4cbc3666ee44da8bcda8aa8629bc73762ec84` |
| `docs/plans/labflow/gantt-zh-cn.html` | 347639 | `0b292f26b28b01bd639765961467c4c6a4515899e266ed4631f964f7ac8d8c9d` | `0b292f26b28b01bd639765961467c4c6a4515899e266ed4631f964f7ac8d8c9d` | `0b292f26b28b01bd639765961467c4c6a4515899e266ed4631f964f7ac8d8c9d` |
| `docs/plans/labflow/locale-snapshot-zh-cn.json` | 17106 | `5d05ca2137a41fdaddd0064ba73857c1bddf457a9fbaab79e3f05b8a6d9e1408` | `5d05ca2137a41fdaddd0064ba73857c1bddf457a9fbaab79e3f05b8a6d9e1408` | `5d05ca2137a41fdaddd0064ba73857c1bddf457a9fbaab79e3f05b8a6d9e1408` |

## Primary 验证与最终交付

- 生成器成功退出，四项输出及快照齐全；验证脚本检查需求覆盖、逐字段输入/排程一致、依赖释放、全部区间资源互斥、容量峰值、精确阻塞集合和 null 坐标。
- 重复生成四项主输出逐字节一致；原始 36 条需求段落均在保留原文中。两轮的审前、审查者所读与审后 SHA-256 逐文件一致。
- `python -X utf8 -m unittest discover -s tests -p test_build_plan.py`：27 项通过。旧渲染器回归证明：2 个末端标签越界被正确捕获。
- skill-creator 的 quick_validate：通过；`git diff --check`：通过。技能全局语言仍 null，其他设置保持原值。
- 剩余计划审查问题：无；必需检查未完成：无。外部身份资料未知是被如实建模的项目条件，继续阻塞产品 B 放行，不影响本计划通过审查。

交付文件：`plan-input-zh-cn.json`、`locale-snapshot-zh-cn.json`、`schedule-zh-cn.json`、`plan-zh-cn.md`、`gantt-zh-cn.svg`、`gantt-zh-cn.html`，以及本记录 `review-zh-cn.md`。全部位于 `docs/plans/labflow/`。
