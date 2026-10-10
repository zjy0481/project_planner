# Superpowers 的 TDD 规则与可借鉴机制

**调查基线：**只读源码 `C:\Users\goey8\.codex\visualizations\2026\10\07\01a115ed-5019-7091-98d6-54fbb64a9840\superpowers-source`，Git SHA `8ca22dba9a94f28898bbce59f2537ff4d87c747d`。行号均相对该快照。

## 明文规则与作者理由

`skills/test-driven-development/SKILL.md:16-45` 规定新功能、修 bug、重构、行为改变均适用；一次性原型、生成代码、配置文件需询问人类伙伴。实现前必须先有失败测试；先写了实现就删除重做。流程为 RED（最小行为测试并看到预期失败）→ GREEN（最小实现）→ REFACTOR。RED 要因缺少目标行为而失败，测试错误或拼写问题不算；完成前跑项目测试套件，并按名披露既有失败。这是完成门槛，不是每个微循环都跑全套（同文件 113-128、168-190、293-306）。

它的“强制”路径由多层文字门槛组成：按任务类型触发、禁止先写实现、先写则删除、验证 RED 的原因、完成检查表和合理化反例。合理化表把“太简单”“手测过”“已投入时间”等理由逐一驳回，并要求从头做（同文件 222-247）。这要求代理给出过程证据；本次读到的是流程文本，不能据此说有工具自动拦截。

作者认为测试后补会受现有实现影响，未证明测试能抓到目标错误；手测不易复跑、容易漏边界；TDD 可提前抓缺陷、降低回归风险、支持安全重构（同文件 222-236）。这是作者论证，不是本次独立验证的效果。例外须询问人类伙伴，末尾也将伙伴许可列为条件（同文件 323-330）。

`skills/test-driven-development/writing-good-tests.md:20-63、150-169` 进一步要求说明什么真实行为变化会让测试失败，独立推导期望值，测试实际行为而非源文本或 mock；琐碎转发与人类 prose 不必造测试。结束前可用心智变异检查典型错误能否被抓住。具体到依赖替身，应先了解真实副作用，只替换慢或外部操作；若 mock 设置盖过测试逻辑，改用真实组件（同文件 80-145）。重点是测试有效性，不是给每行代码机械配测。这里与 TDD 完成清单“每个新函数/方法都要有测试”（TDD 文件 293-304）有尺度张力；落地时宜按有意义的可观察行为理解，避免为琐碎转发造空测。

## 工作流接口与文本张力

`skills/writing-plans/SKILL.md:34-50、108-125` 将任务定义为可独立测试且值得审查的交付，并把写失败测试、确认、最小实现、验证拆成步骤；但模板预期 RED 为 `function not defined`。这与 TDD 正文要求“失败而非错误”有张力：未定义函数可能只产生异常，不能证明业务断言正确失败。模板应要求断言因预期业务行为失败；导入、测试发现、环境错误先修复后重跑。`verification-before-completion/SKILL.md:14-35、82-97` 要求完成声明有新鲜、完整的验证输出支撑。

审查模板不是两个并行审查者：`skills/subagent-driven-development/task-reviewer-prompt.md:4-19` 规定同一审查者先看 spec 再看代码质量；这是单任务审查，全部任务后另做整分支审查。审查者通常不重跑全套，除非具体疑点需要聚焦测试（同文件 73-85）。

## 可选借鉴（不等于照搬）

1. 保持 grill→决策与需求、planner→spec/tickets/计划的分工；只在实现 ticket 加可观察行为、预期 RED 原因、最小 GREEN 与完成验证字段。
2. 窄化测试质量检查：写明要捕捉的错误，独立给出期望值，优先断言用户可见结果；不为形式给琐碎逻辑堆测试。
3. 例外逐案记录范围、理由、风险及人类批准；对原型、生成物、配置处理，不自动豁免，也不把源文档的“删除重做”扩展为产品硬约束。
4. 新提示可借鉴 `skills/writing-skills/SKILL.md:558-587、633-657` 的验证法：先跑无提示压力基线，再测同场景；措辞微测设无提示对照、每变体至少五次并人工阅读，纪律类指导仍需压力场景。手动复核是为避免把模板回声或反例引用误判为遵从（同文件 579-587）。快照没有 `evals/README.md`；这里只能确认 skill 写有基线方法，不能声称存在独立 evals 目录。

## 证据边界

依据仅为固定快照文档。可确认它用红旗、清单、测试证据和审查提示约束流程；材料不能证明技术钩子会拦截违规，也不能证明强制语气保证模型遵从或带来量化效果。`writing-skills` 是作者提出的验证方法，不是 TDD 已通过独立基准评估的证据。这些只能作为可审计过程设计参考，不能替代项目实测。项目应用时应按测试耗时、真实边界和遗留基线安排验证频率，避免把末尾全套门槛误作每一步全量运行。

## 固定版本源码链接

以下链接对应本次调查的同一提交，便于复查上述文件与行号。

- [TDD 规则与作者解释](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/test-driven-development/SKILL.md)
- [有效测试的写法](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/test-driven-development/writing-good-tests.md)
- [计划编写](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/writing-plans/SKILL.md)
- [完成前验证](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/verification-before-completion/SKILL.md)
- [子代理实施流程](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/subagent-driven-development/SKILL.md)
- [任务审查提示模板](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/subagent-driven-development/task-reviewer-prompt.md)
- [Skill 编写与行为验证方法](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/writing-skills/SKILL.md)
