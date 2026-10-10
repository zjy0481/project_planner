# Project Planner 本地化流程可移植性核查

日期：2026-10-09。核查范围是 raw-source 指纹与换行转换，以及 `normalize_language` 对 BCP 47 的实际支持边界。没有联网安装技能、修改实现或基线记录，也没有运行项目测试。

## 结论

**A：有条件地受影响，流程能恢复。** 已安装的 `$skill-installer` 默认 `auto` 路径先下载 ZIP，ZIP 解压和后续 `copytree` 不做换行转换，因此该路径按当前脚本不会仅因 Git 的 `core.autocrlf` 改变这些文件。只有 ZIP 下载遇到 HTTP 401、403 或 404 时，`auto` 才回退到 Git；强制 Git 安装、或从本地 Git checkout 手动复制也会受 checkout 换行设置影响。本机 Git 的系统级 `core.autocrlf=true`，三份指纹源没有 EOL 属性。隔离 Git checkout 实验将相同 LF 内容物化为 CRLF：JSON 解析结果和两种语言的 canonical message hash 不变，但三个 raw-source hash 全部改变，旧 baseline 因而被 `get_bundle` 和 snapshot 阻断。用同一个索引以 `core.autocrlf=false` checkout 回 LF 后，原三项指纹和 `get_bundle` 立即恢复。若选择保留转换后的 CRLF，则必须按完整源版本重新审查并更新证据；不能只改写旧 PASS 记录中的 hash。

**B：当前实现提供普通标签语法解析、路径安全检查和大小写规范化，不提供完整 IANA 有效性检查或 Preferred-Value 规范化。** 代码注释明确排除在线注册表，测试却把 RFC 明确列为有效的 `i-klingon` 标成非法；该实现也会接受 `art-lojban`，但不按 IANA 的 Preferred-Value 将其规范化为 `jbo`。RFC 把 `i-klingon` 列入有效的 grandfathered tags；RFC 又规定生成的标签 SHOULD 采用 canonical form，并将 canonical form 定义为使用 IANA 数据逐步处理，含 Preferred-Value 替换。这里的 SHOULD 是推荐级要求，不能转述成实现对旧 tag 的 MUST 拒绝要求。若产品只需要安全的普通语法子集，应把文档和错误语义明确限定为“语法/大小写规范化、不检查注册表或别名”；若承诺完整 BCP 47 canonical form，才需要支持 grandfathered 与注册表 Preferred-Value 映射。

## A：换行、原始指纹和恢复

### 入口行为与路径范围

本机安装器 `C:/Users/goey8/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py` 的 `_prepare_repo`（234–252 行）在 `auto` 下先调用 `_download_repo_zip`，仅对 HTTP 401/403/404 继续 Git 回退；默认值是 `auto`（308–312 行）。下载分支用 `zipfile.extractall`（108–115 行）并经 `shutil.copytree` 复制技能目录（219–223 行），这些步骤没有 Git checkout 的换行过滤。Git 分支则执行 `git clone`、`git checkout`（131–166 行）。项目 README 也将完整目录从 checkout 手动复制作为人工安装路径（README.md:17–23）。因此结论针对这份安装器的真实分支逻辑；没有下载远端仓库或执行实际安装。

Git 官方文档说明，属性未指定时由 `core.autocrlf` 决定是否转换；`text` 转换会把索引内容规范为 LF，而 checkout 时“line endings are normalized to LF in the index”，工作树内容可按配置转成 CRLF（[Git Attributes 文档](https://git-scm.com/docs/gitattributes#_text)）。本机实测 `git config --show-origin --get core.autocrlf` 为 `file:D:/Program Files/Git/etc/gitconfig true`。对 `project-planner/scripts/locales/en.json`、`zh-CN.json`、`project-planner/references/localization.md` 执行 `git check-attr -a` 没有属性输出，仓库根目录和技能目录均没有 `.gitattributes` 文件。现有三份文件分别是 61、61、135 个 LF，均为 0 个 CRLF。

### 隔离复现

所有复现文件均位于 `.tmp/workflow-portability/`。原始技能目录先复制至 `skill-copy`；随后复制完整技能到 `synthetic-git-skill`，在副本执行 `git init`、`git -c core.autocrlf=true add --all`，再对三个指纹源移除副本工作树文件并执行 `git -c core.autocrlf=true checkout-index --force -- <path>`。此实验只创建隔离目录内的本地索引，没有 commit、remote 或真实仓库 Git 元数据修改。

`current_source_hashes` 对 `Path.read_bytes()` 的原始内容执行 SHA-256（`project-planner/scripts/localization.py:310–319`）。副本 checkout 前后结果如下：

| 内容 | EN raw hash | zh-CN raw hash | context raw hash |
|---|---|---|---|
| 原 LF | `a44e544680c78e9f65751ed1394eca64fbab890a91b6405cc3f6a0763cae7dd2` | `8bb60255bf9b95ac0883186d127da3510e3252a34cbefe3bc49c046a7c7bf3f5` | `ab95dded1a672e830a75e8df31186477e2ef7406e895efb1eebf429f68f5d376` |
| Git `core.autocrlf=true` checkout | `3e9f7bec5eecc1d971baaa335ce8d77445ab29b4b77effcc9f99f3411fd9ccee` | `8ab4bae6e39957effb51f424211ec90cda7726bdbec9057c18f6be2915738147` | `d6032c68ec5a7e8577835c1383abc5962fc5e90c215544da07f550289bf1ce0b` |

EN 与 zh-CN 的解码 JSON 在两侧完全相同，canonical `messages_hash` 也完全相同：EN 为 `2902e1a4a6abab0e6eda1534e820f67bcd795489c499d20d63158401d6efad34`，zh-CN 为 `a6c2fc8abfad863323b05e0c2f2dce903ee4715242add339d8a646c5d710cf2f`。因此本次失效仅由 raw bytes 的 CRLF/LF 差异触发，并非文案内容变化。

在 CRLF 副本调用 `get_bundle("en", skill_dir=...)` 得到 `LocalizationError: built-in baseline review is stale for the current source files`。实际 CLI 子进程通过 `subprocess.run([sys.executable, "-B", "-X", "utf8", "project-planner/scripts/localization.py", "snapshot", "--language", "en", "--output", ".tmp/workflow-portability/cli-test-snapshot.json", "--skill-dir", ".tmp/workflow-portability/synthetic-git-skill"], capture_output=True, text=True)` 捕获到 `returncode=2`、空 stdout；stderr 含 `localization: built-in baseline review is stale for the current source files`。`snapshot` 在未提供候选文案时调用 `get_bundle`（`localization.py:733–747`），baseline loader 对源指纹不匹配直接报 stale（436–465 行）。

恢复实验在同一合成索引中将这三份副本文件移除，再用 `git -c core.autocrlf=false checkout-index --force -- <path>` 写回。`current_source_hashes` 随即逐项恢复成表中原 LF 指纹，`get_bundle("en", skill_dir=...)` 成功，命令退出 0。该结果证明字节恢复可复用原 baseline；保留 CRLF 则要走 `references/localization.md:129–133` 所要求的当前来源校验和完整双语审查，不允许绕过审查修改哈希。

**最小稳定化建议：** 在仓库 `.gitattributes` 对确切的指纹源固定 `eol=lf`（或采取等效的可审查配置），使 Git checkout 保持与 ZIP 发行内容一致。另一种路线是把指纹改为归一化文本，但那会改变已批准的 raw-byte 指纹契约，需要另行迁移基线；本次未改实现或证书。

## B：BCP 47 的规范边界

`project-planner/scripts/localization.py:70–146` 的 `_canonicalize_bcp47` 文档写明它处理“ordinary BCP 47 syntax without consulting an online registry”；92 行注释明确不推断注册表 canonical aliases。它按普通语法检查语言、可选 extlang/script/region/variant、extension 与 private-use，并规范大小写；`normalize_language` 在 149–155 行对外提供 path-safe casing。它没有 IANA registry 内容，也没有对有效 subtag 进行注册表查验或 Preferred-Value 替换。`project-planner/scripts/skill_config.py:44,147` 的错误消息仍将拒绝输入描述为“有效的 BCP 47 语言标签”，`project-planner/references/localization.md:9` 使用较宽的“canonical language tags”。

RFC 5646 §2.1 的 `Language-Tag` 语法明确含 `langtag / privateuse / grandfathered`；§2.1 的 irregular 清单包含 `i-klingon`，并称 “These tags are all valid, but most are deprecated”。§2.2.9 区分 well-formed（符合 ABNF）与 valid：有效标签可以是 grandfathered 标签，或由注册表中相关 subtags 构成并满足重复限制；extension 部分还需满足相应 extension 规则。IANA 记录将 `i-klingon` 列为 grandfathered，标记 Deprecated `2004-02-24`，并给出 Preferred-Value `tlh`。RFC §3.1.6 说明带 Deprecated 字段的 tags/subtags 仍 valid，validating processor SHOULD NOT 生成它们；§3.1.7 对 Deprecated 记录的 Preferred-Value 使用 RECOMMENDED 语气。RFC §4.5 写明 tags “SHOULD always be created or generated in canonical form”，并要求 canonicalization 使用 IANA 数据，包括在存在映射时替换 grandfathered/redundant tag 与 subtag 的 Preferred-Value。因此，旧标签不是自动非法；偏好值替换属于规范形式处理，但相关 SHOULD/RECOMMENDED 不能改写成 MUST 拒绝旧输入。

IANA 当前记录的相关字段原文如下；`art-lojban` 与 `i-klingon` 均明确标为 grandfathered，且都有 Preferred-Value：

```text
Type: grandfathered
Tag: art-lojban
Deprecated: 2003-09-02
Preferred-Value: jbo

Type: grandfathered
Tag: i-klingon
Deprecated: 2004-02-24
Preferred-Value: tlh
```

本机只读调用结果与源代码一致：

| 输入 | `normalize_language` 结果 | 规范事实 |
|---|---|---|
| `i-klingon` | 抛 `LocalizationError: invalid BCP 47 language subtag: 'i'` | RFC/IANA 列为有效 grandfathered tag，deprecated，Preferred-Value `tlh` |
| `art-lojban` | 返回 `art-lojban` | 普通解析器接受其形状，但完整 registry canonicalization 应使用 Preferred-Value `jbo` |
| `zh-Hant-CN` | 返回 `zh-Hant-CN` | 普通结构与大小写规范化示例 |

`tests/test_localization.py:102–139` 将 `i-klingon` 放入 invalid 列表；按 RFC 术语，这个测试值是“本实现当前不支持的 grandfathered 输入”，不是“无效 BCP 47 标签”。最小文档修正是限定为“path-safe 普通语法子集与 casing canonicalization，不查询 IANA、不映射 grandfathered / Preferred-Value”；若保留面向任意合法 BCP 47 标签的宽泛承诺，则需要从可信版本化 IANA 数据支持完整有效性与规范化，并改变该测试预期。具体产品选择留给维护者，本核查没有修改任何源文件。

## 一手来源

- [RFC 5646 §2.1、§2.2.9、§3.1.6–3.1.7、§4.5](https://www.rfc-editor.org/rfc/rfc5646.html)：语法、grandfathered、well-formed/valid、Deprecated 与 Preferred-Value 语义。
- [IANA Language Subtag Registry](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry)：`i-klingon -> tlh` 与 `art-lojban -> jbo` 的当前记录。
- [Git Attributes 文档](https://git-scm.com/docs/gitattributes#_text)：文本归一化、`core.autocrlf` 与 `eol` 对 checkout 的影响。
- 本机安装器：`C:/Users/goey8/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py:81–97,108–115,131–166,219–252,294–312`。
- 本地实现和合同：`project-planner/scripts/localization.py:70–155,310–319,436–465,576–599,733–747`；`project-planner/references/localization.md:9,48–55,129–133`；`tests/test_localization.py:102–139`；`README.md:11–23`。

## 限制

Git EOL 行为受机器配置、仓库属性和平台共同影响；本报告验证的是本机系统级 `core.autocrlf=true` 下的隔离 Git index/checkout，未对所有操作系统或 Git 配置组合做穷举。ZIP 分支的“字节不转换”结论来自本机安装器的实际代码路径，没有发起网络下载或执行安装。IANA 注册表可能持续更新；RFC 的语义判断与示例按 2026-10-09 可读到的官方文本核对。
