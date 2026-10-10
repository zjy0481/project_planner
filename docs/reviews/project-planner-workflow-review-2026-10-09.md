# Project Planner 全流程审查

日期：2026-10-09。审查者身份：普通 Primary 的内部 Subagent，无 Project coordinator / Task primary 角色；模型为用户指定的 `gpt-6.1-sol` / `high`。本报告审查当前工作区，不修改实现、真实技能配置、公共文案或运行时语言包。最终接受及修复决策由 Primary 保留。

## 结论与优先级

当前流程已经有完整的需求建模、确定性生成、文案语义核验、计划独立审查、主代理裁决及失败状态闭环。正常生成、配置读取与保存失败、共享文案失效、历史快照离线复现的关键代码分支具备可执行依据。不能把它概括为“流程已无不足”：原目录更新计划的显式语言切换存在一个已经复现的执行断点，常见 Windows Git 检出还会使原本通过的内置基线失效，从而阻止新计划生成。

| 编号 | 性质 | 严重性 | 建议处理顺序 |
| --- | --- | --- | --- |
| F2 | 已复现 Git 检出可移植性缺陷 | P1，适用于 `autocrlf=true` 路径 | 先固定被哈希来源的发布/检出字节，再验证安装副本可创建内置快照 |
| F1 | 已复现缺陷 | P2 | 区分计划快照与持久语言包的语言所有权规则，恢复原目录语言切换 |
| F3 | 已复现兼容性缺口 | P2 | 明确并补齐合法旧式 BCP 47 标签的接受及规范化边界 |
| O1 | 可选清晰度优化 | 非阻断 | 给候选消息文件一个明确的完整格式示例 |
| O2 | 可选适配优化 | 非阻断 | 明确审查内容可以被上级项目要求的委派 brief 包装 |
| O3 | 可选恢复优化 | 非阻断 | 说明续作如何恢复原轮次、冻结上限与未完成审查 |
| O4 | 可选成本优化 | 非阻断 | 区分历史复现、同语言更新与新计划的快照刷新要求 |
| O5 | 可选协议澄清 | 非阻断 | 统一 reviewer 的 minor/PASS 与 Primary 的最终接受门槛 |

本轮不是另一次语言译文全量验收，也没有实际调用新的计划审查者或浏览器验证视觉效果。下文清楚区分脚本复现、已有测试和流程静态核对；没有将“没有经验测量”写成性能或模型可靠性的确定缺陷。

工作单元：`project-planner-workflow-audit`；执行者：`/root/workflow_audit_sol`；汇报对象：负责本次普通会话的 Primary。唯一正式写入边界为本报告，合成复现写入边界为 `.tmp/workflow-audit-sol/`。

## F1：计划快照沿用持久语言包的语言所有权限制，阻断原目录切换语言

- **严重性：P2。** 已获授权的常见更新分支无法按文档命令完成；没有数据丢失或静默降级。
- **位置：** `project-planner/scripts/localization.py:757` 调用 `_check_existing_owner()`；该函数在 `localization.py:675` 要求旧文件语言必须与目标语言相同。对应流程入口为 `project-planner/SKILL.md:22`、`:54`、`:66`，文档限制为 `project-planner/references/localization.md:127`。
- **触发场景：** 已有英文计划和有效 `locale-snapshot.json`；用户要求在同一输出目录将当前计划改成简体中文。两种内置文案及基线均有效。
- **实际行为：** 创建英文快照及同语言替换均退出 `0`；改为 `snapshot --language zh-CN --output <同一目录>/locale-snapshot.json` 退出 `2`，报 `refusing to replace a locale target owned by another language`。旧快照仍为 `en`、字节哈希未变。
- **为什么是缺陷：** 持久包 `user-locales/en.json` 不应被其他语言占据，这是合理保护；计划本地快照则属于当前计划的固定产物，用户明确切换语言后应能更新。技能要求每次使用名为 `locale-snapshot.json` 的快照，却既禁止跨语言替换，也没有给出保留旧快照、另写新快照并更新输入引用的路径。换一个新目录可以绕过，但改变了用户指定的更新目录；擅自删除旧文件不是现有安全流程。
- **证据：** `.tmp/workflow-audit-sol/reproduce.py` 的 `create English snapshot`、`replace with same English language`、`switch existing snapshot to Chinese` 三个 CLI 步骤；详细参数、stdout、stderr、退出码及原文件哈希在 `.tmp/workflow-audit-sol/reproduction-results.json`。使用的是真实已核验内置文案的隔离副本，没有伪造审查记录。
- **最小可行改进：** 保留持久语言包的同语言保护；另定义计划快照的所有权检查，在用户已明确要求切换当前计划语言时允许替换本技能 `generator` / 已知版本 / 合法旧语言的快照。也可采用新的计划本地快照路径并更新引用，但必须明确如何保留旧证据及完成全量生成与独立复审。非本技能文件、未知版本、符号链接等保护继续保留。该修改需要 Primary 裁决，本轮没有实施。

## F2：来源原始字节哈希没有配套检出约束，Windows Git 换行转换阻止新计划生成

- **严重性：P1，条件明确。** 适用于 `core.autocrlf=true` 且没有覆盖属性的 Git 检出，再按 README 复制技能的正常安装路径；当前未转换的工作区不受影响。不是所有下载 ZIP 或字节保真的安装都失败。
- **位置：** `project-planner/scripts/localization.py:318` 对来源原始字节求哈希，`:464`–`:465` 拒绝与 baseline 不匹配的源哈希；`references/localization.md:9` 规定 raw bytes。`README.md:25` / `README.zh-CN.md:25` 允许从 checkout 复制完整技能，但没有固定三份来源的换行字节。仓库对 `scripts/locales/en.json`、`zh-CN.json`、`references/localization.md` 没有相应 Git 属性约束。
- **触发场景：** 用户在 Windows 的 `core.autocrlf=true` 环境检出技能源，或安装工具进入其支持的 Git fallback，再从该副本使用技能。三份来源被 Git 从 LF 转为 CRLF，基线 JSON 中记录的 digest 字符串仍对应发布时的 LF 字节。Git 未设置相关属性时的转换受 `core.autocrlf` 控制；参见 [Git Attributes 官方文档](https://git-scm.com/docs/gitattributes#_text)。
- **实际影响：** 新计划必须调用 `snapshot`；`get_bundle()` / `snapshot` 拒绝过期内置 baseline，因此包括中英文在内的新计划不能生成。它不是新语言翻译缺失，也不代表来源发生语义变化；安装 `--help` 检查可以成功，却不能证明来源基线可用。历史计划的既有快照仍按离线规则可用。
- **证据边界：** Primary 单独指派的只读研究 peer `/root/independent_semantics_flow` 在 `.tmp/workflow-portability` 建立无 commit / remote 的隔离 Git 索引与检出，真实执行 `core.autocrlf=true` 转成 CRLF；源 raw hashes 改变，解码消息和 canonical message hashes 保持一致，bundle/snapshot 被拒绝，实际 CLI 子进程 exit `2`。同一 index 改用 `core.autocrlf=false` 检出恢复原 LF 字节和原 baseline 可用性。详情和命令在[研究证据](../research/project-planner-workflow-portability-2026-10-09.md)。我独立核查了本机配置、属性及安装器 ZIP/Git 路径代码，并在自己的隔离副本重算三项 CRLF hash：与 peer 记录逐项相同；JSON 和消息 hash 不变，snapshot exit `2`（`eol-independent-results.json`）。实际 Git checkout 由 peer 完成，不能把我的字节转换复核写成另一遍 Git 实验。ZIP 不转换字节的结论来自真实安装器代码，没有执行联网安装。
- **最小可行改进：** 为三份被审查和求 raw hash 的来源设置明确的 LF 检出/发布约束，并让约束随受支持的技能副本保存；发布记录针对这些实际稳定字节生成。安装验证除 `--help` 以外应检查内置 bundle 或在隔离输出创建内置 snapshot。保留严格的 raw-byte 三方审查，不应遇到换行变化后仅重写 digest 或沿用未经重新核验的 `PASS`。无需修改用户全局 Git 配置。

## F3：合法旧式 BCP 47 标签被解析器当作非法，接口支持范围没有明示

- **严重性：P2。** 影响旧式合法标签输入、已有设置迁移和被承诺的标签接受范围；不影响目前中英日常规标签。
- **位置：** `project-planner/scripts/localization.py:70`–`:146` 只实现普通语法及大小写规范化，`:86`–`:87` 拒绝单字母语言前缀；`project-planner/scripts/skill_config.py:147` 对外报告这是无效 BCP 47。`tests/test_localization.py:133` 将 `i-klingon` 固定为非法测试数据。权威需求称配置接受合法语言标签，并在查文案前规范化。
- **触发场景：** 用户显式保存 `i-klingon`，或已有配置使用该旧式标签。它对应现代标签 `tlh`；即使用户只保存偏好、尚不要求翻译文案，当前 CLI 也拒绝。
- **复现：** `skill_config.py --config .tmp/workflow-audit-sol/tag-compatibility-config.json set --language i-klingon --confirmed` 的 Python 进程 exit `2`，提示 `invalid BCP 47 language subtag: 'i'`，未创建配置。独立函数调用同样拒绝 `i-klingon` 与 `en-GB-oed`，接受 `tlh` 与 `en-GB-oxendict`；`iw` 和 `he` 分别保持原值，不做 Preferred-Value 映射。CLI 参数、stderr、退出码和未写入证明见 `tag-compatibility-results.json`。
- **规范适用边界：** 已核对研究 peer 保存的 RFC 对应条款和 IANA 字段原文：RFC 5646 §2.1 语法包含 grandfathered，§3.1.6 保留 Deprecated 标签的 valid 性；IANA 的 `i-klingon` 记录标明 grandfathered、Deprecated 和 Preferred-Value `tlh`。§4.5 对生成规范形式采用 SHOULD，Preferred-Value 处理采用注册表信息。这里不把 SHOULD/RECOMMENDED 错写成“每个输入都 MUST 自动映射”；确认问题是合法旧式标签被称为非法以及“规范标签”承诺范围没有说明。Deprecated 不自动等于 invalid。参见 [RFC 5646](https://www.rfc-editor.org/rfc/rfc5646.html)、[IANA Language Subtag Registry](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry)，原文摘录和进一步边界在[研究证据](../research/project-planner-workflow-portability-2026-10-09.md)。
- **最小可行改进：** 根据产品承诺补齐固定 grandfathered 标签及可确定 Preferred-Value 的本地兼容处理，或明确承诺仅覆盖普通语法并提供用户可用的现代替代标签；后一条是收窄当前需求，须 Primary/用户裁决。无需新增在线 registry 服务、全局配置或翻译依赖。不要将未知但合法的语言标签误等同于已有经核验文案。

## 已批准的取舍，不作为缺陷

1. **相对工作量和非最优确定性排程。** 排程是列表调度，使用输入顺序作稳定优先级；条长不等于日历工期。任务容量、资源互斥、未知外部事件和正工作量契约任务的规则相互一致。没有证据要求改为优化器、真实工期模型或新的依赖层。
2. **语义核验与计划审查分开。** 新语言完整逐键核验，计划再审查实际正文、图表和详情。这两层成本是已批准的质量门槛，不能因 JSON 合法或当前计划没显示某键而省掉。新增语言最多初审加两轮修订，计划上限单独冻结。
3. **固定计划审查模型和实际视觉检查。** 缺模型、独立代理或视觉能力时必须 `INCOMPLETE` / 草稿，而不是自动降级自审。这是已批准限制，不能把当前环境不能完成它们当作实现缺陷。`max_review_revisions: 0` 也必须初审。
4. **来源原始字节变更使共享包失效。** 当前代码确实拒绝过期共享文案；计划本地快照离线校验自己的证据，仍能复现历史计划。不能只改哈希、保留旧 `PASS` 来冒充重新语义核验。
5. **偏好与本次语言分离。** 空偏好不先询问；临时语言、文案扩充及成功提示不授权保存偏好。只有已完成并审查交付的计划才追加可选提示，主动配置请求不生成或翻译计划。保存失败准确报告，已有产物保持有效。
6. **审查证据的信任边界。** helper 自动验证全键、占位符、证据形状和哈希绑定，不能以代码证明一个模型实际进行过语义比较。独立身份、逐键实证和 Primary 回查仍是流程职责；没有将人为伪造一整套结构合格 `PASS` 的能力当作本任务新增安全漏洞。

## 可选优化

### O1：候选消息文件的顶层格式不够明确

`references/localization.md:21` 的 “containing only a complete `messages` object” 可被读成裸消息对象，也可被读成 `{ "messages": { ... } }`。helper 在 `localization.py:813`–`:814` 的 `validate` 分支以及 `make_bundle()` 实际接受裸对象，即顶层直接是 `unit`、`plan_title` 等键。

隔离复现中，完全相同的英文消息用 `{ "messages": ... }` 包装后校验退出 `2`，报告全部键缺失和额外 `messages` 键；裸对象退出 `0`。这是格式歧义，不能据此断言英文候选已经通过日语语义核验：本试验只测试文件传输结构。最小改进是在参考文档给出明确的裸对象示例并标注“不要额外包一层 `messages`；正式 bundle 才有该字段”，不必新增第二套输入格式。

### O2：审查模板应留出上级委派规范包装入口

`references/review.md:7` 要求完成模板后逐字发送；`SKILL.md:83` 之后给出直接创建审查者的例子。本项目 `.codex/policies/AGENT_ROLES.md` 第 3 节要求 Sender / Recipient 身份声明，完整子代理规范还要求边界、模型、容量及交付 brief。

上级规范优先，执行者可以且应当在不改变审查检查清单的前提下加合规外包装，所以这不是“必然违规或无法执行”的缺陷。不过未明确说明包装方式容易漏掉项目适配步骤。最小改进为一句明确指令：按当前项目和运行环境的委派要求包装本模板，保留完整审查内容；不要把本项目专有十项格式永久写进通用技能。本项已与 Primary 讨论，按其上级规范优先的解释降为非阻断清晰度问题。

### O3：补充中断续作规则，避免执行者重新猜测冻结上限

`SKILL.md:42` 定义本次请求或技能配置的计划上限；`references/review.md:69`、`:83` 要求记录每轮及冻结上限。现有记录足以支持人工恢复，但没有明确区分“继续同一待决计划”和“用户要求开启一次新的计划修订”。语言文案的初审/两轮计数也没有指定续作应读取哪份历史记录。

可在既有 `review.md` 或候选审查记录中恢复原上限、已执行轮次、未完成检查和三方哈希；文件变化后按现有规则完整复审，不把重新调用技能或共享配置变化自动视为新的初审预算。只需补充恢复段落，无需新全局配置或调度器。本轮没有实际模拟代理重启，不声称当前执行者已经绕过轮次上限。

### O4：历史复现与同语言更新可明确复用计划快照

`SKILL.md:66` 无条件要求生成前创建当前快照，而 `localization.md:129` 和离线生成器允许历史有效快照不受共享源变化影响。隔离副本仅在上下文文档末尾增加一个换行后，新快照被过期基线阻止；原计划仍能生成，四种产物逐字节一致。

历史重现不需要重新准备全部文案；在不切换语言或修复固定文案的前提下更新任务，也可考虑继续使用已有有效快照并重新完整审查计划。最小建议是明确分支，保持“新计划必须使用当前来源”的已批准规则。是否允许同语言更新继续旧快照属于产品取舍，不能以本报告代替用户决定；没有数据证明现有重核验成本不可接受。

### O5：reviewer 与 Primary 对次要问题的接受门槛应写得一致

`references/review.md:62` 允许必需检查完整且没有 material 问题时给 `PASS`；`:67` 则要求每项证据被确认的 finding 都修复才能通过，`:83` 又要求上限耗尽时任何 confirmed issue 都保留草稿。具体场景是计划上限为 `0`、reviewer 只报告 minor 的可读性问题且返回 `PASS`：Primary 按当前后两句仍须保留草稿。

Git 基线的旧审查协议明确使用“没有实质问题”和“两轮后仍有实质问题”门槛；本轮当前 `docs/requirements.md` 又要求每个经核实问题修改并完整复审，因此不能仅凭旧版本认定这是未经批准的回归。本项由 Primary 并行复核提出，我独立读过当前和 Git 基线原文后保留为协议清晰度/产品取舍：明确 minor 是否也阻断最终接受，并统一 reviewer 决策和 Primary 门槛。若严格修复所有问题是当前批准行为，就清楚说明 reviewer 的 `PASS` 仍不等于 Primary 可接受；若只保留实质问题门槛，则须先获得产品裁决再调整。没有测量数据证明 minor 造成了实际预算浪费。

## 要求与检查覆盖映射

| 分支 / 要求 | 实际检查与依据 | 状态与边界 |
| --- | --- | --- |
| 需求进入、语言与配置 | 完整读取授权需求/方案、SKILL、schema；核对原文保存、语言优先级及选择依据记录 | 静态闭环存在；未模拟 LLM 全文需求理解 |
| 正常内置语言计划 | 用真实内置基线创建快照并执行英文 fixture；exit `0`，四产物存在 | 实际脚本通过；本试验不宣称计划独立审查 PASS |
| 新语言准备与复用 | 13 项 localization 测试；核对候选、完整键、模板、逐键审查、三方哈希、发布/快照 | 传输和失效分支通过；本轮未另做真实新语言语义审查 |
| 安装副本来源可移植性 | peer 的真实 Git index/checkout 与 LF 恢复；本审查者独立核对转换 hash、helper 拒绝、配置和安装器代码 | F2 已复现；ZIP 只读代码核验，未联网安装 |
| 合法标签接受与规范化 | RFC/IANA 原文、当前测试和本审查者实际 helper/CLI 探测 | F3 已复现，普通标签以外的有效 grandfathered 输入被误报非法 |
| 保存长期文案失败 | `test_snapshot_protects_foreign_targets_and_accepts_candidate_as_fallback` 模拟持久目录只读 | fallback 通过；合成审查仅用于隔离测试 |
| 偏好配置只读与保存失败 | 4 个配置测试：缺文件虚拟默认、自定义字段保留、原子替换失败、CLI 无成功输出 | 通过；真实安装配置未改变 |
| 源变化与历史计划 | 在隔离副本改变 context 字节；新 snapshot exit `2`；历史生成 exit `0`、四产物哈希完全相同 | 行为符合共享失效/历史复现设计；O4 是便利性建议 |
| 既有计划更新 | 核对保留语言/容量规则，复现 en→zh-CN 同路径快照更新 | F1 失败；同语言替换通过 |
| 配置-only | 核对 SKILL 首段独立入口和 configuration helper；上面的配置测试覆盖保存边界 | 不要求翻译新语言或重新生成计划；无额外流程缺口 |
| 混合语言、显式覆盖、空偏好 | 语言顺序、实质性混合歧义澄清、本次实际语言提示和显式保存授权逐项静态核对 | 文案规则清楚；没有实际对话实验或性能结论 |
| 建模、排程与容量 | 资源锁、普通任务容量、external/milestone 不占容量、unknown 外部阻塞、空列表和语言不变性相关测试 | 共 11 个选定排程/产物检查实际通过 |
| 产物生成与保护 | 非本生成器目标和输入冲突测试；语言快照绑定及 markup 转义测试 | 已执行通过；没有做跨四文件事务故障恢复测试 |
| 文案语义 REVISE / INCOMPLETE | localization 完整协议，确认问题回查、候选修复、全键新审查者及独立轮次边界 | 静态规则存在；未实际创建审查代理 |
| 计划 REVISE / INCOMPLETE | review 完整清单、Primary 裁决、输入/文案分流修正、四产物重生成及七文件三方哈希 | 静态规则存在；没有把小范围自审替代完整复审 |
| 初审及轮次上限 | 计划 `0` 仍初审；文案与计划计数不共用；上限冻结且 draft 退出 | 静态清楚；续作操作建议见 O3 |
| 能力 / 容量不足 | SKILL / review 的指定模型、独立代理、实际视觉能力缺失即 INCOMPLETE；项目子代理规范允许排队/复用并核实容量 | 有安全退出，无静默替代；本身份禁止再委派，未做运行时代理容量实验 |
| 最后交付和偏好保存 | 全产物、审查、视觉、三方哈希及无实质问题才交付；空偏好末尾提示与配置-only 分支分离 | 静态符合批准行为；不能仅以测试通过宣称端到端交付验收完成 |

## 命令、证据与退出码

本审查者工作目录全部为 `D:\strange tools\project-planner`。Python 调用设置 `PYTHONDONTWRITEBYTECODE=1`；测试临时文件使用现有 `tests` 临时目录，审查复现仅写 `.tmp/workflow-audit-sol/`。本审查者没有外部调用、安装、commit、PR、工作树或真实偏好写入。研究 peer 经 Primary 指派读取官方来源，其只读研究与隔离 Git 实验是单独贡献，已逐项说明责任和复核边界。

| 命令 / 检查 | 结果 |
| --- | --- |
| `git status --short`、`git branch --show-current`、`git rev-parse HEAD` | exit `0`；分支 `dev`，HEAD 与分配基线均为 `abb6acd7a086047194174acdbdca33f3286a5460`；既有大量未提交变更保持原样 |
| `python -X utf8 .tmp/workflow-audit-sol/reproduce.py` | 外层 exit `0`；内层准确记录成功和预期拒绝的 CLI exit `0` / `2`，见 reproduction-results |
| `python -X utf8 -m unittest discover -s tests -p test_localization.py -v` | exit `0`，13 项通过 |
| `PYTHONPATH=tests` 后选取 `SkillConfigTests` 的缺配置、字段保留、原子替换失败、CLI 保存失败 4 个测试 | exit `0`，4 项通过 |
| `PYTHONPATH=tests` 后选取 4 个 SchedulingTests、4 个 ArtifactTests，并误将 3 个 ValidationTests 写为 SchedulingTests | exit `1`；8 项实际通过、3 项测试装载失败，原因是审查命令的类名错误，不是实现失败 |
| 将上面 3 个测试纠正为 `ValidationTests.test_unit_defaults_and_empty_lists_are_valid`、`.test_omitted_language_defaults_to_english_and_null_is_invalid`、`.test_language_change_preserves_schedule_and_resource_identity` 后运行 | exit `0`，3 项通过；已覆盖相关检查，未重复那 8 个已通过测试 |
| 在隔离配置路径调用 `skill_config.py ... set --language i-klingon --confirmed` | 直接 PowerShell 包装的工具 exit `1`；随后 Python subprocess 测得实际 CLI exit `2`，配置不存在，见 tag-compatibility-results |
| `git config --show-origin --get core.autocrlf` 和三个源路径的 `git check-attr -a` | exit `0`；系统级 `true`，属性没有输出；未修改设置 |
| 自己隔离副本的 CRLF 字节与 helper 独立复核 | 外层 Python exit `0`；三项 source hash 与 peer 相同、解码消息及 canonical hash 不变、实际 snapshot 子进程 exit `2`，见 eol-independent-results |
| 研究 peer 的 `git init` / `git -c core.autocrlf=true add --all` / `checkout-index --force` 和 false 恢复对照 | 仅 `.tmp/workflow-portability/` 的隔离索引，无 commit/remote；实际 snapshot 子进程 exit `2`，LF 恢复后 bundle 成功。准确参数及指纹见研究报告；未由本审查者重复 Git 操作 |

Python 启动时输出 `Failed to find real location of D:\ProgramData\anaconda3\python.exe`；实际脚本和测试继续运行并给出上述可核对结果。本报告没有把该环境告警误记成所有命令失败。文件读取中一次列举尚不存在的 `docs/reviews` 目录报告缺路径；之后由本报告创建该目录，该情况不影响被审查来源。

本轮审查产物仅为本文件；复现脚本、合成候选、隔离技能副本、日志和来源清单位于忽略目录 `.tmp/workflow-audit-sol/`，不是正式语言发布或计划交付证据。重要检查的源码定位和 CLI 参数保留在本文件与复现脚本，完整来源 SHA-256 在 `source-manifest.json`。

## 审查版本与来源

权威需求是 `docs/requirements.md` 与用户于 2026-10-09 批准的 `docs/design/project-planner-language-catalog-plan.md`，旧语言方案不作覆盖依据。代码观察对象是当前未提交工作区，Git diff 仅帮助定位变化。下表是本轮读取后测量的来源指纹；交付前再次检查相同来源未变，不声称这是此前未执行的三方计划审查。

| 来源 | SHA-256 |
| --- | --- |
| `AGENTS.md` | `abf90d17193ef4cbbada8d0a1171045d726cda0dccf8ad04bf78432770dac96b` |
| `.codex/policies/AGENT_ROLES.md` | `dd69320b7a86e3c8b00973e525241b69708eeb956a4d54163ec95fbcfd73950d` |
| `.codex/policies/SUBAGENT_POLICY_AGENT.md` | `af462acefd8c51ef9a516d176b648846d67fea3ef64e664c02c0fc087e9d6ec6` |
| `docs/requirements.md` | `f4a4338b6f6456f3d243d65985c2202334bbed71e033d5ec8fb81c9712e135ea` |
| `docs/design/project-planner-language-catalog-plan.md` | `d11d45a26ce2325fc176ec018c64b93c1292102230b72cbf0b2cd6194f1c12aa` |
| `project-planner/SKILL.md` | `2d99513472453f61745abb48ce9295b412ffd43d440e0036e4cda235b4301034` |
| `project-planner/references/schema.md` | `bc75ff24060cb5d0f813cfed7aa86e2639204ae6363b1314aea2868be7ba99c7` |
| `project-planner/references/review.md` | `84e9d0b8436b6eb1ff7dc6dcf89840323c785bf755df21f30b85d9e18797baa4` |
| `project-planner/references/localization.md` | `ab95dded1a672e830a75e8df31186477e2ef7406e895efb1eebf429f68f5d376` |
| `project-planner/scripts/build_plan.py` | `dbcb9d5516855cf66a567d7edc61fdb74afa958b990990a73d57d86110d25f1b` |
| `project-planner/scripts/localization.py` | `c3593485f760fd9bf54c115ad59afd194f12971746e9c70246e4328ea169d14c` |
| `project-planner/scripts/skill_config.py` | `c2b1b8745da7e7b0357dbef0a38feb1dff4b64d4d191e2adc8ed8f0651abd01c` |
| `project-planner/scripts/locales/en.json` | `a44e544680c78e9f65751ed1394eca64fbab890a91b6405cc3f6a0763cae7dd2` |
| `project-planner/scripts/locales/zh-CN.json` | `8bb60255bf9b95ac0883186d127da3510e3252a34cbefe3bc49c046a7c7bf3f5` |
| `project-planner/scripts/locales/baseline-review.json` | `52947ede76320c8264abac13a0da83834472837f69ff8b1ecb7d787963e6f54b` |
| `README.md` | `45db0ce6e6c5a44756abcc7e3b856f7cab1a7d9edd1d32d4cec471877de54c38` |
| `README.zh-CN.md` | `16cce99ee8d06204676299097273bfecc2f7ca76ad6bb48c2535241ac66a921b` |
| `docs/research/project-planner-workflow-portability-2026-10-09.md`（研究 peer 交付） | `2cdcc76ea1a5df7f0d15c587d5228ec41a6f3e5f3831550fa1a031a1e15ed8cd` |
| 本机 `C:/Users/goey8/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py` | `110cc7e4e395c2c9ba070d47db7d21be5164591c35015ae364fc9c9905b08de8` |

## 尚未验证项与交付门槛

- 尚未模拟一次真实新语言翻译、独立语义 reviewer 的质量、计划 reviewer 的 REVISE 循环或实际浏览器任务详情；本任务是流程审查，Subagent 身份禁止递归委派。
- 没有实际联网安装/升级或操作用户偏好。安装路径的来源字节可移植性和 BCP 47 已合并独立研究证据；本轮没有穷举所有平台、Git 配置、IANA 标签与扩展形式。
- 没有性能基准、用户实验、真实代理容量耗尽或跨文件 I/O 事务故障实验。关于成本和续作的建议不作为已测缺陷。
- 本报告的局部门槛为 `Unit delivered`（独立审查结果待 Primary 复核），不自动代表工作区改动已接受，也不授权修复、发布或修改政策。
