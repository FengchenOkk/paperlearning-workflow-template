# 路线图

## 通篇理解与基础学习升级（2026-10-01）

- [x] LIT-006：每篇论文按需添加 `06_synthesis/summary.md` 与 `concept-guide.md`，分别提供连贯通篇讲解及从底层原理到器件/指标的学习路径；原文、译文、精读、分析和全局概念卡相互链接，进度仍只写 meta。
- [x] OPS-010：新增 study plan/coverage、精确分段、YAML 字段上下文、完整上下文预检和长草稿返修分段；已有任务、模型接口与目录兼容。
- [x] OPS-011：208 项离线回归通过；指定论文主文10页/11段译文、综合总结、12概念/12公式学习指南完成主会话核验，真实子模型返修失败后主模型接管并单独验收成功。真实研究成果仍在本地忽略项目内。
- [x] OPS-012：论文模块收尾逐条复核返修/接管记录；超限或一次子模型返修仍失败的任务沿用现有主模型接管与再审核，旧阻断任务记录后继对应关系。当前没有待接管论文任务，补充简明处置手册，不更改目录、连接、适配器或已验收科学正文。
- [ ] TODO(user)：取得补充材料/原始数据以核对反演、统计与动态证据；当前分析保持 partial。
- [ ] TODO(user)：后续配置具体线上复现目标与执行方式。

使用见 [通读与学习手册](workflow/study-guide.md)，验证见 [升级验收](workflow/upgrade-validation.md)。以下为此前阶段历史记录。

## 模型任务分配与连接闭环（2026-10-01）

- [x] OPS-009：首次真实Zotero入库、DeepSeek调用与主会话接力分析已执行；正文/概念/公式及来源链接完成验收。修复任意标签生成无效topic ID的问题，保留原始标签和正常历史ID；补充回归及离线测试配置隔离。198项回归覆盖，首轮197通过，隔离问题修复后所属30项测试复测通过。真实研究成果在本地忽略项目中，不随公开工作流分享。

- [x] OPS-008：移除 `projects/_template` 和 `.gitkeep` 占位；`projects/` 只保存真实项目，内部初始化定义统一到 `workflow/layouts/`。新项目自带完整文件职责说明，196 项离线测试通过。

- [x] OPS-007：子模型返修失败自动创建主模型修复尝试，原合同/输入/草稿延续；主Profile独立路由，现有会话接力、外部调用需--execute，默认1次主修复仍失败则block。主模型修复仍单独验收，195项测试通过。

- [x] CFG-004：主模型计划/验收，子模型执行；12类任务合同与现有 routing 一致，当前连接与Key保持。
- [x] OPS-005：稳定ID、ArtifactRef、可重建INDEX.json、哈希检测、最小上下文和评审包；旧目录/路径/字段继续兼容。
- [x] OPS-006：结果草稿登记、显式main评审、accept正式应用与连接视图更新；失败回滚、子模型最多3次尝试及主模型接手修复、未改草稿沿用。
- [x] ZOT-002 / GRAPH-002：别名优先入库，topic关系，统一源links；图谱端点/证据经机器索引解析，人工区保留。
- [x] REP-004 接口：claim/公式/原理/概念可通过ArtifactRef接入通用结果与评审流程；专业执行仍待配置。
- [x] 188项离线测试通过，合同/分享检查及mock演示通过；保护文件哈希一致。
- [x] 首篇真实论文的正文科学内容已验收；具体课题目标与补充材料仍待用户确认。
- [x] 小规模真实API连接验证；观察到截断/结构化失败并完成主模型接力。
- [ ] TODO(user)：进一步验证真实API任务成本、稳定性和返修成功率。
- [ ] TODO(user)：后续配置私有复现执行。

使用见 [任务分工手册](workflow/task-orchestration.md)，结构和验证见 [验收记录](workflow/upgrade-validation.md)。以下为此前阶段历史记录。

## Zotero 与论文知识图谱升级（2026-10-01）

- [x] LIT-005：meta.yaml 入口与 01_source～05_notes 编号目录；复制迁移、冲突报告、原件保留和旧任务路径兼容。
- [x] ZOT-001：可选只读 local/web/export，Better BibTeX/CSL 导入，DOI/item key 去重，人工内容保护与附件引用。
- [x] GRAPH-001：离线知识图谱、第一性原理与综述候选聚类、Jaccard/IDF、前置顺序、桥梁论文与缺口；证据/置信度和核验过期记录。
- [x] OPS-004：原子写入、dry-run 不写文件、损坏条目继续扫描、Zotero 本地配置忽略及分享检查。
- [x] REP-003 接口：project.yaml 私有扩展声明、通用读写接口；不执行专业复现。
- [x] 110 项离线测试、doctor --offline --share-check、mock/fixture demo、Git diff 检查通过；用户 .env、models.local.yaml 和模型适配器哈希保持。
- [ ] TODO(user)：选择真实 Zotero 模式/库/集合并验证连接。
- [ ] TODO(user)：后续重新规划 GPT/DeepSeek 分工；本轮保持模型配置。
- [ ] TODO(user)：提供首篇真实论文与研究画像进行科学内容验收。

详情见 [升级验收](workflow/upgrade-validation.md)；接入见 [Zotero 手册](workflow/zotero.md)。以下为此前阶段历史记录。

## 主/子模型通用 API 接入（2026-10-01）

- [x] CFG-003：共享 model_profiles 管理主/子连接，可独立选择提供商、模型、接口与自定义密钥变量；旧 subagent_profiles/逐角色配置保留兼容，本地配置不改写。
- [x] OPS-003：run --main 调用主 API/CLI 处理同一任务包，原 run 继续调用子模型；日志增加 main/subagent 目标与主模型角色，未变更原数据合同。
- [x] 支持 Chat Completions 与 Anthropic Messages；其他协议可用 command。主 API 负责文本计划/汇总/核验，文件和工具由运行 agent/使用者处理，未添加自主工具循环。
- [x] 密钥可用任意合法 api_key_env 和 api_key_aliases；DeepSeek 兼容 ds_apikey，进程候选优先于 .env，不将本地密钥导出到宿主进程或记录进配置/日志。CLI 的本地变量只传给其子进程。
- [x] 更新 AGENTS 主/子调度提示与主模型合同，新增 workflow/model-setup.md 简明手册，README 统一指向手册；五个顶层目录和三个工具模块保持。
- [x] 本机已识别 DeepSeek Key；一次官方 API 最小请求成功返回 OK（仅短测试文本，非思考模式，64 token 上限），未发送论文或研究资料。
- [x] 最终合并回归与分享检查：80 项测试、doctor --offline --share-check、demo 全部通过；其他提供商的主/子独立协议调用使用模拟响应验证，未使用其真实 Key。

复现功能未扩展，科学内容仍待真实论文验收。GitHub 模板由用户自行同步、提交与推送；本轮仅更新本地公开模板。以下为此前阶段历史记录，旧版行为和测试数不代表当前状态。

## Profile 通用性对比与验收（2026-10-01）

原实现具备通用任务格式和四适配器，但只适合本机的逐角色配置；缺 Key 会阻止 doctor/真实执行，未达到无密钥分享要求。本轮增量补齐，不改写已有 local/.env，不迁移研究资料。

| 配置要求 | 原实现 | 当前结果 |
| --- | --- | --- |
| 五个顶层目录、文献/复现/任务/日志/原 CLI | 已具备 | 保持；新增 doctor --share-check 参数 |
| 主模型认证在仓库外，仅引用 Profile | 只有会话继承和 Profile 意图 | 模板 auth: external / api_key_env: null；只检查 Codex 命令，不读取认证；支持 manual 主模型 |
| 子模型共享 Profile、减少重复 | 逐角色重复连接字段 | subagent_profiles + 全局默认 + 角色覆盖，内存解析，兼容旧配置 |
| 全局一处切换服务 | 需逐角色改 | 角色 profile 为 null/省略时继承全局，避免固定 manual 覆盖全局 |
| 有 Key 自动调用、无 Key 可用 | --execute 可调用，缺 Key 报错 | 已选 Profile + --execute 自动调用；缺 Key/配置无效/外部失败转 waiting-manual；普通 run 保留预览 |
| bootstrap、doctor、demo 引导 | 引导有限，缺 Key 阻断 doctor | 检查 Python/PyYAML，创建缺失目录，不覆盖配置；doctor 不联网、不打印 Key；demo 强制 mock |
| 环境变量优先、不保存 Key | 基本具备 | 保留，递归拒绝 YAML 认证字段，YAML 错误不显示原始行 |
| 忽略私密资料与分享检查 | 基础 .gitignore | 补忽略项、Git 实际追踪检查、明显密钥模式扫描；只报告位置 |
| 三种模式的 README | 只面向本机配置 | Codex+DeepSeek、无任何 Key、其他兼容模型三模式及误传 Key 撤销步骤 |
| 新旧功能兼容 | 42 项测试 | 54 项 unittest 通过，旧 CLI、文献/复现、Profile、回退、脱敏、Git ignore 覆盖 |

与要求示例的两处有意调整：角色默认 profile: null，保证 default_subagent_profile 切换确实生效；DeepSeek 使用官方当前 deepseek-flash，而非示例 deepseek-chat。API 接口沿用 Chat Completions，其他协议需 command/专用适配器。API 子角色仍由主模型调度，不是自主工具执行循环；主模型 Profile 不自动启动或修改客户端。

本轮检查：54 项测试通过；doctor --offline --share-check 和 demo 通过。分享扫描未发现明显真实密钥模式；ARS 原测试两处假 Key 已人工核对并按文件路径/摘要标注，不豁免其他测试文件。当前没有 Git 仓库，因此本机仅确认忽略规则声明，实际 Git 追踪/强制提交检查在隔离测试仓库验证。复制/压缩需主动排除私有文件，扫描不包含历史或大文件，不能证明全部资料已脱敏。

真实连接待用户填本地 DEEPSEEK_API_KEY 后验证；当前缺 Key 已自动回退 manual。其余模型配置要求已完成，科学质量仍待第一篇真实论文验收。以下为此前阶段记录，历史测试数与旧行为只描述对应阶段。

## 当前模型接入（2026-10-01）

- [x] CFG-002 配置部分：主模型继承当前 Codex/GPT 会话；阅读、复现分析、核验角色通过 openai_compatible 接入 DeepSeek 官方 deepseek-flash；知识角色保持回退。
- [x] 通用模板保留 manual，本地配置使用 DeepSeek；既有目录、任务和论文/claim 接口保持，未增加依赖。
- [x] 支持 thinking/high 推理与输出上限；日志记录请求参数，截断正文标 partial，空正文失败。
- [x] 42 项 unittest 通过；实际 local 配置四角色 dry-run 通过（含知识回退）；临时目录已清理，无真实 API 调用。
- [ ] CFG-002 连接部分：TODO(user) 在本地 .env 填入 DEEPSEEK_API_KEY，随后检查环境并进行小规模真实连接测试。当前 doctor --offline 正确报告密钥缺失，尚未验证账户权限、网络和真实模型返回。

DeepSeek 当前作为文本子任务模型接入，文件操作、任务编排与最终核验由 Codex 承担；实际复现与自主工具执行仍按 REP-002 后续配置。

## 整体精简计划（2026-09-30）

1. 固定五个顶层目录、数据路径和原 CLI，不新增文件与依赖。
2. 将四个角色的重复规则收敛到 workflow/README.md，执行时统一拼接；保留角色专有任务。
3. 用 YAML 继承压缩配置模板，保证解析内容等价；保留本地配置和环境变量。
4. 对既有功能执行回归、互通和保护文件校验，随后进入模型配置。

## 整体精简结果

- [x] 未新增或删除文件/目录，五个顶层目录与研究资料路径固定，三个工具模块各守原职责。
- [x] 四个角色共同规则只维护一处，run 自动拼接一次，日志哈希覆盖共同规则与专有角色内容。
- [x] 模型模板从 84 行缩到 53 行；YAML 继承后解析内容完全等价，完整配置与差异配置均可用。
- [x] 文档入口和文献/复现共享接口明确，AGENTS 合并重复规则；功能与格式要求保留。
- [x] 38 项 unittest、doctor --offline、demo 全部通过；新旧命令、四角色互通与配置显式值保留均覆盖。
- [x] SHA-256 比对确认：models.local.yaml、.env、复现模板（6 文件）、ARS（2572 文件）均未变化；项目目录没有测试残留。

下一步 CFG-002：开始配置实际模型，再用用户提供的真实论文执行 LIT-004 验收。原有 PDF/科学质量/实验能力边界仍见下文。

## 本轮计划与结果（2026-09-30）

1. 收缩文献模板为四核心文件，契约合并到 schemas.yaml。
2. 保留五个顶层目录、ARS、复现模板、任务包、日志和适配器。
3. 实现分类索引、概念卡、阅读清单、知识统计与学习顺序。
4. 增加模式路由、知识角色回退、预读约束、内容校验与旧格式迁移。
5. 用离线、mock、兼容测试验收，不调用真实模型或实验。

## 当前阶段完成项

- [x] CFG-001：原主从模型配置保留；默认禁用 knowledge-builder，缺失/禁用回退 literature-reader；旧 local 配置内存兼容，密钥来源不变。
- [x] LIT-001：每篇论文 meta/translation/reading/analysis 四文件；逐段全文翻译、11 章精读、公式/概念/上下文/复现线索任务合同。
- [x] LIT-002：单概念卡、单阅读清单、分类 INDEX、知识网络；图关系来源可追溯，循环或缺卡明确阻断学习顺序。
- [x] LIT-003：类型/状态、四文件、公式 ID、概念卡与来源引用、完成内容、清单 citekey 校验。
- [x] OPS-001：原 CLI 和四 adapter 保留；新增 new concept；旧 task schema 路径兼容；原始任务与实际角色分别记录。
- [x] OPS-002：旧文件保留，缺失新产物自动合并，元数据改动有 .runs 快照；冲突内容提示人工整理。
- [x] REP-001：复现模板和 claim 接口保持；文献输入更新为 reading 与 analysis 的 extraction/formulas/reproduction。

## 合并和移除记录

- workflow/schemas/task.schema.json、paper.schema.json、claim.schema.json 合并到 workflow/schemas.yaml；旧路径通过 run 别名兼容。
- 自有 paper/note.md 内容职责进入 reading.md，paper/extraction.yaml 内容职责进入 analysis.yaml。
- 旧项目骨架中的 synthesis/README.md 已移除，综合工作稿按需在 10_literature/ 创建具名文件。
- catalog/、collections/、paper-reader/context-builder、templates/concept/、templates/collection/ 在当前仓库本就不存在，没有删除此类真实数据。
- ARS vendor 原内容和实际研究项目未改写；`projects/` 仅保留项目说明，没有真实论文数据；内部初始化定义统一位于 `workflow/layouts/`。

## 文献重构验收（上一轮）

```powershell
python tools/wf.py bootstrap
python tools/wf.py doctor --offline
python tools/wf.py demo
python -m unittest discover -s tests
```

35 项 unittest 全部通过；doctor --offline 与 demo 通过。测试覆盖新旧 CLI、四核心文件、概念卡、去重频次、前置顺序/循环、分类、清单备注保留、完成内容与引用、预读约束、角色回退、schema 别名、迁移快照和不覆盖旧译文。demo 全部临时运行，不污染 projects，不需要密钥。没有真实模型或实验调用。

## 后续阶段

- LIT-004：以真实论文验收翻译覆盖、精读解释、公式准确性与概念引用，之后决定是否增加 PDF 文本提取（pypdf 可选）。
- LIT-005：联网文献寻找、本地问答、模型响应结构验证或审核后写回；按实际需要新增。
- REP-002：用户详细定义线上代码、模拟、线下实验功能后再实现真实运行。
- CFG-002：已选择当前 Codex/GPT 主模型与 DeepSeek 子模型；待补本地密钥并验证真实连接；YAML 不改变现有 Codex 会话模型。

## 待确认 TODO(user)

1. 研究方向、目标与第一篇真实论文。
2. 全文翻译目标语言、逐段呈现偏好与章节批次。
3. 概念卡深度、精读解释层次、所需数学前置知识。
4. 课题组名称、近期论文及本地代表文献材料。
5. priority/difficulty/importance 的标签含义与阅读顺序。
6. 本地 DEEPSEEK_API_KEY；真实论文外发范围与调用预算按测试任务确定。
7. 实际复现 claim、算力/数据/软件/设备/预算/时间/伦理条件。

## 明确边界

通用模板默认 manual；当前 local 已配置 DeepSeek，但密钥与真实连接待验收。工具准备任务与核验合同，模型草稿需要主模型审核，尚未验收真实译文、科学推导或实验。
PDF 解析/OCR 和可选 ingest 本轮未实现，基础依赖仍只有 PyYAML。
validate 是结构和文件可追溯性检查，不能证明翻译质量、来源定位真实或科学结论正确。
allowed_paths 是协作约定，非外部命令沙箱；fallback 仅处理知识角色缺失/禁用，不自动重试外部服务。
生成区可重建，阅读清单人工备注与 matrix 保留；旧格式不完整时提示整理，不能用迁移掩盖验证问题。
