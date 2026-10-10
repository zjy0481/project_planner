# F2、F1、F3 修复验收与当前限制

日期：2026-10-09。依据：[原流程审查报告](project-planner-workflow-review-2026-10-09.md)。本轮修复由普通 Primary 负责，不更改项目政策或用户已安装的技能副本。

## 修复结果

| 项目 | 修改 | 验证 |
| --- | --- | --- |
| F2：Git 检出改变来源指纹 | 在技能根目录增加 `.gitattributes`，仅三份被哈希来源固定 `text eol=lf`；双语 README 要求保留该隐藏文件并验证两种内置快照 | 完整技能复制到隔离 Git 根，在 `core.autocrlf=true/false` 下实际暂存及重新检出，原始字节和 SHA 不变；英文、中文均能创建快照并生成四种产物 |
| F1：原目录切换计划语言失败 | 增加 `snapshot --replace-language`；仅显式切换允许替换有效、已知版本且归属本技能的计划快照；持久 `user-locales/` 包不作为快照输出 | 同目录英文→中文→英文成功，排程数值、依赖、资源、状态保持一致；无标志拒绝切换；外来文件、未知版本、非法语言、坏证据与写入失败保持旧文件 |
| F3：合法旧式标签被拒绝 | 接受固定全集 26 个 grandfathered 标签，按 IANA Preferred-Value 规范化；无替代值者保留；已知旧别名仍可用于识别已有快照所有权 | 26 项含大小写与幂等性验证；配置 CLI 接受 `i-klingon`、`en-GB-oed` 等且保留自定义字段；旧 `art-lojban` 快照可离线读取、同语言刷新或显式切换 |

F3 的映射依据为 [RFC 5646](https://www.rfc-editor.org/rfc/rfc5646.html) 和日期为 2026-09-17 的 [IANA Language Subtag Registry](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry)。它不将 Deprecated 标签视为非法，也不将合法语言标签等同于已有经核验文案。

## 核验与基线

- `python -X utf8 -m unittest discover -s tests -v`：60 项通过，无跳过项。覆盖原有排程/产物、配置/文案边界和新增的 Git 检出、语言切换及标签兼容回归。
- `skill-creator/scripts/quick_validate.py project-planner`：通过；该检查只证明技能格式合法，不替代行为或语义核验。
- 新的独立 Subagent `/root/baseline_fixes_semantics`，`gpt-6-luna/max`、`fork_turns=none`，在更新后的本地化上下文中对全部 59 个英中键完成逐键语义比较。Primary 回查实际文案、用法与证据，并复测所有 before/read/after 指纹匹配后接受。正式证据保存在 `project-planner/scripts/locales/baseline-review.json`，没有沿用旧逐键 PASS。
- 英中源消息未改：消息 SHA 分别为 `2902e1a4a6abab0e6eda1534e820f67bcd795489c499d20d63158401d6efad34`、`a6c2fc8abfad863323b05e0c2f2dce903ee4715242add339d8a646c5d710cf2f`。更新后的上下文原始字节 SHA 为 `43eabce0b27589d6ae6ed4dd4755c179ea0d59425206272d686a6a7fa7a84bdd`。
- 独立 `gpt-6.1-sol/high` 修复复查另行核对实际差异与可执行边界，执行 34 项不同测试及额外 CLI 探测、核对官方注册表，修后没有剩余 F2/F1/F3 finding。其发现的旧别名快照“能读不能更新”已修正并加入回归。Primary 回查实际 diff、证据与冻结来源后接受修复；所有子代理已停止写入。

## 升级影响

上下文变化按既定协议使旧共享语言包的审查失效；其他语言（包括此前日语运行时包）需按当前上下文重新全量语义核验后才能用于新计划。旧包与历史示例快照不被删除、改名或伪造新证据；已有效的计划快照仍可离线复现。采用新 Preferred-Value 的共享包需发布到规范路径，不自动迁移旧文件。

实际技能偏好保持初始值 `language: null`、`max_parallel: null`、`max_review_revisions: 2`。本轮仅修改仓库中的技能，没有安装或更新用户技能库，也没有推送远端。

## 当前仍有的不足与验证范围

原报告的五项非阻断优化尚未处理，不能将本次三项修复描述为“所有流程不足已消除”：

1. **O1：候选 JSON 格式的文档歧义。** 裸消息对象与 `{ "messages": ... }` 包装的区别仍缺明确示例。
2. **O2：审查模板的委派包装。** 尚未明确如何在保留完整清单的同时适配上级项目委派要求。
3. **O3：中断续作。** 尚未补充恢复冻结轮次上限、已执行轮次与未完成检查的操作规则。
4. **O4：历史快照复用。** 同语言更新是否允许沿用历史有效快照仍是待定产品取舍；本轮保持新计划使用当前来源。
5. **O5：minor 与 PASS 门槛。** reviewer 与 Primary 接受门槛仍需统一说明或产品裁决；本轮不降低既有质量要求。

其他边界：

- 标签助手检查普通 BCP 47 语法、大小写及固定 grandfathered 映射，不提供完整 IANA 注册有效性检查、全部普通子标签别名或扩展语义规范化；例如 `iw` 仍保持 `iw`。这不是新增在线注册表服务。
- Git 属性不会修复已被手动改成 CRLF 的安装副本，也无法阻止更高优先级属性或编辑器改写。安装快照验证仍是必要的；不要用重写 digest/PASS 绕过失败。
- 本机无创建真实符号链接的权限。该测试使用 `Path.is_symlink` 模拟验证拒绝分支及原文件保护；未验证真实 Windows 链接/重解析点行为。
- 未执行联网安装/升级、一次新的完整计划独立审查或浏览器视觉检查。CLI 生成测试证明确定性产物可生成，不证明新计划已经通过交付审查；本轮未改变固定可视文案。
- 未穷举所有操作系统、Git 属性覆盖组合、文件系统并发竞争或多产物事务失败。这些检查没有被写成已通过。

原审查报告作为历史发现保持不变。本文件记录修复后的验收边界，不追改旧报告的来源指纹或当时结论。
