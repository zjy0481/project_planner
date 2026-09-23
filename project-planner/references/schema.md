# 规划输入契约

本契约把普通任务的数字解释为粗略的相对工作量，并用同一抽象轴表达相对顺序。它不把工作量换算为小时、工作日或日历日期，也不预测现实工期。

`plan-input.json` 使用 UTF-8 JSON。生成命令为：

```text
python <skill-dir>/scripts/build_plan.py INPUT.json --output DIR
```

成功时固定生成 `schedule.json`、`gantt.svg`、`gantt.html` 和 `plan.md`；输入校验失败时返回退出码 2，并把原因写入标准错误。四个产物由同一个排程对象生成。

除 `unit` 可省略外，所有顶层字段都必须出现；`assumptions`、`risks`、`requirements` 和 `tasks` 可以为空数组。规划真实项目时仍应提供足以覆盖需求的任务。

## 顶层字段

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `version` | 整数 | 必须为 `1`。 |
| `title` | 字符串 | 非空项目或功能名称。 |
| `summary` | 字符串 | 需求范围和目标的简明摘要。 |
| `unit` | 字符串 | 可省略；默认“相对工作单位”。仅是显示标签，不参与换算；规划文档使用相对工作量标签，不使用现实时间单位。 |
| `assumptions` | 字符串数组 | 估算、容量、技术边界等假设。 |
| `risks` | 字符串数组 | 已知风险和不确定性。 |
| `requirements` | 对象数组 | 原始需求的可追溯条目。 |
| `max_parallel` | 正整数或 `null` | 普通任务并发上限；`null` 表示容量未知，按无容量上限计算理论排程。 |
| `tasks` | 对象数组 | 任务、里程碑和外部事件。 |

每条需求必须包含唯一非空 `id`、原文或忠实改写的 `text`，以及可定位的 `source`。`requirements` 非空时，每条需求至少被一个任务的 `requirement_ids` 引用。

## 任务字段

每项任务都包含以下字段：

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `id` | 字符串 | 唯一且非空。 |
| `title` | 字符串 | 简短可辨识。 |
| `description` | 字符串 | 范围、目标和边界。 |
| `requirement_ids` | 字符串数组 | 只引用已定义的需求 ID。 |
| `duration` | 数字 | 粗略相对工作量；有限数；普通任务必须大于 0，里程碑和外部事件必须为 0。以简单参照任务的 1 为基准，2、3 等只表示约两倍、三倍工作量。 |
| `depends_on` | 字符串数组 | 只引用已定义的任务 ID；整个图必须无环。 |
| `resources` | 字符串数组 | 精确字符串资源锁；同名锁使普通任务互斥。 |
| `deliverable` | 字符串 | 可检查的交付物。 |
| `acceptance` | 字符串数组 | 完成与可合并的验收条件。 |
| `estimate_basis` | 字符串 | 估算依据及相关假设。 |
| `kind` | 字符串 | `task`、`milestone` 或 `external`。 |
| `external_ready` | 数字或 `null` | 仅外部事件可使用同一抽象轴上的非负有限相对偏移；未知为 `null`，已就绪可用 `0`。它是显式情景假设，不换算外部日历等待；其他类型必须为 `null`。 |
| `pr_scope` | 字符串 | 普通任务的独立 PR 边界；里程碑或外部事件说明其无代码 PR。 |

依赖在前置节点结束时释放。普通任务占用一个并发槽，并在运行期间独占其 `resources`；里程碑和外部事件不占并发槽或资源。`external_ready: null` 会阻塞该节点及所有后代，排程不会为它们虚构相对起点或终点。

`requirement_ids`、`depends_on` 和 `resources` 各自不得包含重复项，且其中的 ID 或资源名必须是非空字符串。`acceptance`、`resources`、`requirement_ids` 可以为空数组；生成器允许部分说明文字为空，但规划者应填写足以让人实施和验收的内容。

算法按输入任务顺序作为稳定优先级执行确定性拓扑列表排程。相同输入得到相同结果，但这不是全局最优调度器。`depends_on` 表达交付先后，`resources` 表达资源互斥，两者不能混用。

## 输出约定

`schedule.json` 完整回显输入信息，并为每个节点给出 `input_index`、`status`、`start`、`finish` 和 `blocked_by`，同时记录生成器与排程元数据。`start`、`finish` 和 `T+N` 都是相对坐标，不是现实日期或工期。`plan.md`、`gantt.svg` 和 `gantt.html` 使用同一份排程数据；HTML 离线自包含，嵌入 SVG，并提供任务详情交互。图中的普通任务条长表示 `duration` 工作量；阻塞任务的整行条纹只表示状态，不表示工作量。

生成器只替换带自身标记的既有目标文件：`schedule.json` 依靠 `generator` 字段识别，其他格式依靠生成注释识别。任一同名目标属于其他来源时，整次写入会被拒绝，目录内其他文件保持不变。输入文件不能与任一目标文件是同一路径。

## 小型完整示例

```json
{
  "version": 1,
  "title": "资料导出",
  "summary": "为用户提供异步 CSV 导出，并显示下载入口。",
  "unit": "相对工作单位",
  "assumptions": [
    "团队容量未知，排程展示无容量上限的理论并行",
    "接口契约冻结后，前后端可用 mock 并行开发"
  ],
  "risks": [
    "对象存储凭据的相对就绪偏移尚未确定"
  ],
  "requirements": [
    {"id": "R1", "text": "用户可以请求 CSV 导出", "source": "需求文档/导出"},
    {"id": "R2", "text": "用户可以下载已完成的文件", "source": "需求文档/下载"}
  ],
  "max_parallel": null,
  "tasks": [
    {
      "id": "T0",
      "title": "设计并评审导出接口契约",
      "description": "完成请求、状态与下载响应设计，并处理评审意见。",
      "requirement_ids": ["R1", "R2"],
      "duration": 1,
      "depends_on": [],
      "resources": ["导出接口设计"],
      "deliverable": "评审通过的接口契约文档",
      "acceptance": ["字段、状态码和错误模型已确认"],
      "estimate_basis": "以简单契约任务为 1 个相对工作单位，包含设计、评审和修订",
      "kind": "task",
      "external_ready": null,
      "pr_scope": "一个文档 PR：接口契约、示例与兼容性说明"
    },
    {
      "id": "M1",
      "title": "冻结导出接口契约",
      "description": "标记已评审的契约可以供实现与 mock 使用。",
      "requirement_ids": ["R1", "R2"],
      "duration": 0,
      "depends_on": ["T0"],
      "resources": [],
      "deliverable": "已批准的接口契约",
      "acceptance": ["T0 的契约已合并并标记为冻结"],
      "estimate_basis": "工作量已计入 T0；此节点只是零工作量状态门槛",
      "kind": "milestone",
      "external_ready": null,
      "pr_scope": "无代码 PR；记录契约批准状态"
    },
    {
      "id": "E1",
      "title": "对象存储凭据可用",
      "description": "等待平台团队交付测试环境凭据。",
      "requirement_ids": ["R2"],
      "duration": 0,
      "depends_on": [],
      "resources": [],
      "deliverable": "可验证的测试凭据",
      "acceptance": ["测试环境上传和下载探测成功"],
      "estimate_basis": "外部相对就绪偏移未知",
      "kind": "external",
      "external_ready": null,
      "pr_scope": "无代码 PR；外部交付门槛"
    },
    {
      "id": "T1",
      "title": "实现导出 API",
      "description": "按冻结契约实现异步导出和状态查询。",
      "requirement_ids": ["R1", "R2"],
      "duration": 3,
      "depends_on": ["M1", "E1"],
      "resources": ["后端导出模块"],
      "deliverable": "通过集成测试的导出 API",
      "acceptance": ["请求可创建任务", "完成后返回可下载地址"],
      "estimate_basis": "相对工作量约为参照任务的 3 倍，包含实现、测试和审查修订",
      "kind": "task",
      "external_ready": null,
      "pr_scope": "一个后端 PR：导出服务、路由与集成测试"
    },
    {
      "id": "T2",
      "title": "实现导出界面",
      "description": "基于冻结契约和 mock 实现触发、状态与下载界面。",
      "requirement_ids": ["R1", "R2"],
      "duration": 2,
      "depends_on": ["M1"],
      "resources": ["导出页面"],
      "deliverable": "通过组件测试的导出界面",
      "acceptance": ["可触发导出", "完成后显示下载入口"],
      "estimate_basis": "相对工作量约为参照任务的 2 倍，包含界面、测试和审查修订",
      "kind": "task",
      "external_ready": null,
      "pr_scope": "一个前端 PR：导出页面、API 适配器与组件测试"
    },
    {
      "id": "T3",
      "title": "完成导出端到端集成",
      "description": "用真实后端替换 mock，并验证完整导出流程。",
      "requirement_ids": ["R1", "R2"],
      "duration": 1,
      "depends_on": ["T1", "T2"],
      "resources": ["导出测试环境"],
      "deliverable": "通过端到端测试的导出流程",
      "acceptance": ["真实环境可从请求导出走到下载完成"],
      "estimate_basis": "相对工作量约为参照任务的 1 倍，包含接线、端到端测试和审查修订",
      "kind": "task",
      "external_ready": null,
      "pr_scope": "一个集成 PR：真实 API 接线与端到端测试"
    }
  ]
}
```

此示例中，有工作量的契约工作由 `T0` 估算，`M1` 只表达冻结瞬间。`T2` 可在契约冻结后基于 mock 开始；`T1` 仍受未知外部事件阻塞，`T3` 等待两端真实实现完成。资源锁没有被伪装成依赖边；所有 `T+N` 只表示相对顺序位置。
