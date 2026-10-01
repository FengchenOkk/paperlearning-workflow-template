# 模型分工与任务闭环

主模型是 **commander-reviewer**：拆解目标、决定输入范围、验收子模型草稿，并在子模型返修失败时接手修复；子模型是 **primary-executor**：按契约阅读、提取、分析或核验。`literature-reader`、`reproduction-analyst`、`verifier`、`knowledge-builder` 是任务职责；GPT、DeepSeek 或其他厂商由独立 Profile 选择。当前模型连接不因本轮结构升级自动改变。

工作流执行器负责文件管理、ID 解析、调用、状态和正式应用。当前 Codex 会话可以承担执行器与主模型职责；API 主模型只处理给定文本，不获得自主工具循环。没有 Key 仍可人工接力，mock 仅用于接口测试。

## 1. 稳定 ID 与机器索引

每个研究方向一个项目。核心对象在创建时取得稳定 ID，移动目录、改标题和 Zotero 重同步不改变 ID：

| 对象 | ID |
|---|---|
| 项目 | `project:<project-slug>` |
| 论文 | `paper:<citekey>` |
| 论文分析/翻译/精读 | `analysis:<citekey>` / `translation:<citekey>` / `reading:<citekey>` |
| 概念/原理/主题 | `concept:<slug>` / `principle:<slug>` / `topic:<slug>` |
| 公式 | `formula:<citekey>:<formula-id>` |
| 复现 claim | `claim:<citekey>:<claim-slug>` |
| 任务/尝试 | `task:<task-id>` / `attempt:<task-id>:<n>` |
| 其他产物 | `artifact:<artifact-id>` |

`INDEX.json` 是项目内 ID → 当前路径、锚点、哈希、别名和任务状态的解析入口；`INDEX.md` 是人类视图。索引不保存科学结论，可删除后由 `index` 重建。路径只是定位结果，不是连接主键。Zotero item key 放 aliases 映射到现有 paper ID，不取代论文 ID；citekey 改名须保留旧别名。

分析 YAML 中嵌入的公式/原理保留旧局部短 `id`，新增 `object_id` 保存规范跨文件 ID（例如 formula:Example2026:eq-1），外部连接用 object_id。概念卡原 `type: foundational/classic/current/emerging` 分类继续保留，`object_type: concept` 表示对象类型；机器索引中的 type 为 concept，不混淆学术类别与对象身份。

```powershell
python tools/wf.py index my-research --json
python tools/wf.py validate --links my-research
python tools/wf.py validate --contracts
```

不要手工编辑 `INDEX.json` 的生成内容；正式源文件中的 `id` 和 `links` 才是来源。输入哈希变化时重新构建上下文，旧审核不能继续代表已变化的内容。

核心对象使用统一 `links`：

```yaml
links:
  - rel: uses
    target: concept:example-concept
    evidence:
      - id: paper:Example2026
        anchor: null
    confidence: high
    status: candidate
```

上例仅演示元数据证据引用；实际科学关系须引用可支持关系的 source ArtifactRef ID/anchor，如原文 section-2，不能用文件存在代替科学依据。关系包括 introduces、uses、extends、contrasts、prerequisite、similar-first-principle、similar-review、similar-concept-set、belongs-to-topic、supports-claim、derived-from、generated-from。每条关系有可追溯证据与置信度，target 必须可解析。自动推断只生成 candidate；图谱与知识地图从索引和 links 生成，不另外维护同一关系。真实核验后才能声明 verified，人工说明放 GENERATED 标记之外。

## 2. 契约与 ArtifactRef

`config/models.example.yaml` 的 routing 定义 task_type → role；`workflow/task-contracts.yaml` 定义 role、输入语义类型、预期输出、验收标准、上下文限制与最多 3 次子模型尝试。子模型返修一次仍未通过即交主模型，主模型修复默认另有 1 次机会，由 settings.main_repair_max_attempts 调整。两者必须一致；没有契约或没有验收标准不能派发。扩展任务时一并补路由、契约、角色提示和检查，连接差异仍留在 adapters.py。

新任务使用 ArtifactRef，以 ID 为主键：

```yaml
id: paper:Example2026
type: paper
path: 10_literature/papers/Example2026/meta.yaml
anchor: null
role: input
required: true
hash: "sha256:由索引计算"
```

调用者提供 ID，路径和 hash 由索引解析与校验，不自行填写假 hash。已有输出同样引用稳定 ID；新输出登记 ID、语义类型和受控目标路径，在 accept 后进入正式索引。若产物移动，重新索引并按 ID 解析，不能把旧路径当作对象身份。

契约语义类型与索引实体类型有明确映射：`paper.meta` 对应 `paper`，`paper.source.text` 对应 `source.text`，`paper.translation`/`paper.reading`/`paper.analysis` 对应 translation/reading/analysis，`research.profile` 对应 research-profile。claim.feasibility、claim.plan、verification.report、critique.report 对应 artifact，同时保留 contract_type 区分用途。ArtifactRef.type 记录解析后的实体类型；契约检查其语义，不用任意字符串跳过检查。source 文本和其他产物的具体 ID 请从 INDEX.json 复制，不根据文件名猜测；方向画像默认为 `artifact:<project-slug>:research-profile`。

旧 `run` 与字符串路径任务包保留兼容，不自动变成已验收正式产物。新的 `task run` 使用契约和 ArtifactRef；同一职责可以继续使用原有任意厂商 Profile。

## 3. 先计划，再构建最小上下文

主模型只创建目标明确、依赖可满足的任务，论文全局定位确认后再翻译/逐节精读。任务注明 source 范围和预期输出，缺资料先 block/TODO(user)。在项目中查看可用对象：

```powershell
(Get-Content projects/my-research/INDEX.json -Raw | ConvertFrom-Json).artifacts.PSObject.Properties |
    Select-Object Name, @{Name='type';Expression={$_.Value.type}}, @{Name='path';Expression={$_.Value.path}}
```

实际任务包放 `projects/<project>/00_inbox/<task-id>.yaml`；CLI 的任务路径相对于仓库。执行前先解析 ID 并构建包：

```powershell
python tools/wf.py task run my-research projects/my-research/00_inbox/first-pass.yaml
python tools/wf.py context my-research first-pass
python tools/wf.py task status my-research first-pass
```

可复制的最小任务包：将下面保存为 `projects/my-research/00_inbox/verify-paper-id.yaml`，先将 paper ID 换成 INDEX.json 中真实存在的 ID。这个任务核验入口元数据与引用结构，不声称完成论文科学内容核验；真实论文精读另选 literature-first-pass/close-read 等契约。

```yaml
task_id: verify-paper-id
task_type: verification
role: verifier
objective: "核对给定论文入口的稳定身份、元数据来源与 links，区分已支持、无支持和无法核验；科学内容尚未提供时明确报告未知。"
inputs:
  - id: paper:Example2026
    type: paper
    required: true
outputs:
  - id: artifact:verify-paper-id:verification
    type: artifact
    path: 30_outputs/verify-paper-id-verification.md
    mode: replace
allowed_paths: [30_outputs]
context:
  task_type: verification
output_schema: null
source_refs: []
```

inputs 非空且覆盖契约必需语义类型；outputs 可省略，由契约和索引定位已有产物，含未替换占位符（例如新 concept）时须显式指定 id/path。allowed_paths 必须覆盖正式输出范围，不能指向原始资料。顶层 task_type 与 context.task_type 兼容，同时填写时必须一致。

```powershell
python tools/wf.py task run my-research projects/my-research/00_inbox/verify-paper-id.yaml
python tools/wf.py task run my-research projects/my-research/00_inbox/verify-paper-id.yaml --execute
```

普通运行不发出真实付费请求；已有明确授权时才加 `--execute`。手工模式生成可供人工模型使用的 prompt，待真实回填后才能继续，不能把 waiting-manual 标为 completed。

```text
.runs/<task-id>/
├── task.yaml
├── status.yaml
├── context/
│   ├── manifest.yaml
│   ├── context.md
│   └── files/
├── attempts/<n>/
│   ├── prompt.md
│   ├── response.md
│   ├── result.yaml
│   ├── artifact-index.yaml
│   └── self-check.md
├── reviews/
│   ├── <n>/review-bundle.md
│   ├── <n>/acceptance.yaml
│   ├── <n>/evidence.yaml
│   ├── <n>/links.yaml
│   └── <n>.yaml
├── revision-requests/
└── final/
```

manifest 保存 contract、解析输入、hash、输出和验收标准。context.md 只展开必要原文片段、术语、约束与模板；单文件/总量/字符限制来自 contract。大文件仅引用，截断明确标记；源材料不完整时不得宣称翻译完整或科学核验完成。上下文构建失败、缺必需输入、ID/哈希解析失败时不执行。子模型只读受控包，不自行扫描全仓；协作约定不等于操作系统沙箱。

同一输入/锚点/契约生成相同内容与内容哈希，时间记录和状态日志独立。缓存不绕开输入变更检测。输入原件只读，所有写入采用原子替换；派发草稿期间不改人工正文。

## 4. 子模型提交结果

子模型每次执行以 result bundle 提交：response 是文本草稿，result.yaml 是摘要、ArtifactRef、证据、confidence、未解决问题和逐条自检；artifact-index.yaml 登记草稿产物 ID/path/hash。新的未登记产物必须通过受控 result 登记，不能假称已在正式 INDEX.json 中生效。

```yaml
task_id: first-pass
attempt: 1
status: submitted
summary: "完成指定段落的预读草稿，剩余实验章节待核验"
created_artifacts: []
updated_artifacts: []
evidence: []
unresolved_issues: []
confidence: low
self_check: {}
```

这是字段示例，不是通过记录。新执行接口要求模型响应为含 `result` 与 `artifacts` 的 YAML 对象：artifacts 每项含正式目标 id、type、文本 content、mode。执行器替它创建草稿 ID/文件并填写真实 hash 和 created/updated ArtifactRef；正式目标此时不写入。confidence 只能 high/medium/low，验收标准逐项填写证据，不用 null 或“通过”掩盖未知。

manual 场景可将真实模型响应整理为以下形状，保存到 `projects/my-research/00_inbox/verify-paper-id-result.yaml`。其中 summary/content/self_check 必须由实际核验补齐，示例中的 TODO 不是科学结果：

```yaml
result:
  task_id: verify-paper-id
  attempt: 1
  status: submitted
  summary: "TODO(user)：填写真实核验摘要与边界"
  created_artifacts: []
  updated_artifacts: []
  evidence:
    - id: paper:Example2026
      type: paper
  unresolved_issues: []
  confidence: low
  self_check:
    evidence_traceable: unknown
    supported_unsupported_unknown: unknown
    criterion_mapped_issues: unknown
    structural_vs_scientific_checks: unknown
    no_self_acceptance: unknown
artifacts:
  - id: artifact:verify-paper-id:verification
    type: artifact
    mode: replace
    content: |
      # 核验报告（草稿）
      TODO(user)：填写来源定位、已支持/无支持/未知、对应标准和无法核验范围。
```

```powershell
python tools/wf.py task submit my-research verify-paper-id --attempt 1 --result projects/my-research/00_inbox/verify-paper-id-result.yaml
```

API 返回有效结构时由执行器提交；人工接力须显式 submit，仅保存 response.md 不会推进状态。响应为空、截断、缺 Key 或外部失败时保留可审计状态并转 manual/partial，不能补造结果或重复付费请求。

每次尝试和状态变化写 status.yaml；INDEX.json 反映任务连接与状态。草稿、自检与结构检查都不能单独使正式产物生效。

## 5. 主模型评审与正式应用

先构建评审包：

```powershell
python tools/wf.py task review my-research first-pass --attempt 1
```

评审包只包含目标、验收标准、子模型摘要、产物引用、变更 links、证据索引、未解决问题和 verifier 摘要。主模型据此按需抽查源 ArtifactRef/anchor，不默认重读整篇论文或整个 context。生成评审包本身不代表模型已经审核。

实际主模型或人工评审使用 reviews/<n>/review-template.yaml，填写真实 reviewer/source，再通过 `task review --review <file>` 导入。执行器把有效评审保存 `.runs/<task-id>/reviews/<n>.yaml` 并记录状态，不能只把文件放进目录当作已经登记。示例用于需要返修的情况：

```yaml
task_id: first-pass
attempt: 1
reviewer: main
decision: revise
passed_criteria: [global_position, paper_logic_map]
failed_criteria: [evidence_traceable]
issues:
  - criterion: evidence_traceable
    detail: "实验结果缺原文表格定位"
required_changes:
  - criterion: evidence_traceable
    detail: "补齐原文表格编号及对应段落证据"
evidence_checks: []
next_action: "仅补齐指定证据与受影响段落"
reason: "重要结论当前无法回溯"
```

accept 必须所有契约标准通过、failed_criteria/issues/required_changes 为空，且主模型/人工真实核对必要证据。evidence_checks 每项须有 `ref: {id: ..., type: ..., hash: ...}` 与 `status: verified`，ref 可由评审包复制，hash 由索引提供；其他任务输出、科学结论和来源定位仍须真实抽查。CLI 的结构与 ID 检查不会自动判断科学正确性。revise 列可修复问题并映射 criterion，reject 拒绝不合格结果，block 说明缺资料/输入或达尝试上限，escalate 交使用者决定。执行器不能把空白模板、mock、自检或主观一句“通过”变为 accept。

新增关系保持 candidate。若确已核验并要改成 verified，真实主模型评审需加逐条 `link_checks`，记录 source、target、rel 与 `status: verified`，对应实际核验的关系证据；仅任务整体 accept 不能替代关系审核。

```powershell
# 当前 Codex/人工完成审核后，导入真实评审文件
python tools/wf.py task review my-research verify-paper-id --attempt 1 --review projects/my-research/00_inbox/verify-paper-id-review.yaml

# 已授权的主 API/CLI 评审：自动读取 orchestrator Profile，无需 --main
python tools/wf.py task review my-research verify-paper-id --attempt 1 --execute --evidence projects/my-research/00_inbox/review-evidence.yaml

# 仅当实际 decision 为 accept 才应用
python tools/wf.py task accept my-research verify-paper-id --attempt 1
```

API 主模型只收到评审包及显式选择的小段证据，不能从文件路径自主读取本地文件。需要抽查时，在仓库相对路径 `review-evidence.yaml` 中列出真实 ID/anchor：

```yaml
refs:
  - id: paper:Example2026
    anchor: L1-20
  - id: artifact:verify-paper-id:attempt-1-1
    anchor: "核验报告（草稿）"
```

这两个引用对应上面最小核验例，实际论文任务应选相关 source 文本/公式/译文等来源和目标草稿的必要片段；先确认锚点存在。hash 可从 INDEX.json 复制，执行器会核对 ID、锚点和变化，受上下文大小限制读取片段。模型的 evidence_checks 只应引用实际提供并核对的证据；没有提供足够证据应 revise/block，不假称读过整篇原文。API 无 `--evidence` 却返回 accept 时保留响应转 manual，不能只凭路径获得科学通过。缺 Key 或已有 Codex 会话返回人工接力，使用真实评审文件导入。

```powershell
python tools/wf.py task revise my-research first-pass --attempt 1 --review projects/my-research/.runs/first-pass/reviews/1.yaml
python tools/wf.py task accept my-research first-pass --attempt 2
python tools/wf.py task status my-research
```

返修请求只传上轮未通过标准、必要变更和相关片段，记录对既有上下文的引用，不重复传完整输入。required_changes 可用 artifact_id 指定受影响的正式目标或草稿 ID；需要额外原文时，评审加入 `context_refs: [{id: ..., anchor: ...}]`，必须指定真实必要锚点。执行器带上有关草稿和这些片段，下一次 `task run` 执行子模型返修。多产物任务返修可只提交明确受影响的产物，执行器校验并沿用上轮未修改草稿；未指定影响范围时仍须提交完整输出。

子模型返修后主模型仍判定 revise，或子模型达到 contract.max_attempts 上限时，`task revise` 自动启动主模型修复尝试：沿用原任务 ID、合同、失败标准和必要草稿，记录 execution_target: main、execution_kind: main-repair、接管原因与 main_attempts。默认先由子模型提交第1次草稿，第2次子模型返修仍失败则第3次由主模型修复。主模型默认1次修复仍未通过再 block/escalate；缺资料或权限直接 block，不假造缺失证据。

当前 `adapter: codex` 沿用已有会话，自动生成 `attempts/<n>/prompt.md` 接力包，当前 Codex/使用者读取后完成修复并用 `task submit` 提交。API/CLI 主模型使用已有 orchestrator Profile，外部调用加 --execute；不加则 dry-run，缺 Key 或调用失败转 waiting-manual。重跑 task run 会继续主模型修复，不退回子模型、不重传原始全文。主模型修复仍为草稿，需单独评审和 task accept；没有自动通过。

```powershell
# 第2次是子模型返修且仍失败时，自动创建下一次主模型修复
python tools/wf.py task revise my-research first-pass --attempt 2 --review projects/my-research/.runs/first-pass/reviews/2.yaml
# 或：主API/CLI已获授权时选择这一条（与上条二选一）；Codex仍走接力包
python tools/wf.py task revise my-research first-pass --attempt 2 --review projects/my-research/.runs/first-pass/reviews/2.yaml --execute
```

accept 才由执行器应用审核过的正式产物，并重建 INDEX.json、knowledge-graph.json、knowledge-map.md、INDEX.md；原人工内容和生成区外说明保留。正式目标或源哈希已变化时拒绝过时应用，先重新核验，不能覆盖新人工修改。

## 6. Zotero、图谱和复现互通

Zotero 可选只读：先 status/sync --dry-run，再显式应用；没有 Zotero/Key 使用 export 或手工入库。索引 aliases 先匹配已有论文，collection/tag 映射 topic，并保留旧别名与人工 meta。同步只更新元数据、来源附件引用和连接，不覆盖译文、精读、分析或进度。连接操作见 [Zotero 手册](zotero.md)。

图谱按 INDEX.json 解析本地源对象和统一 links，包含论文、概念、原理、公式、claim、topic、任务和产物节点。边都须有可解析端点、证据、权重、置信度和状态；无证据不连边，坏链接报告并隔离，不破坏其他对象扫描。自动候选关系不能直接升级 verified，输入变化检测和生成区保护继续生效。

复现公共接口只负责 claim、ArtifactRef、结果提交和评审。专业复现仍在私有扩展中配置，不执行实验；扩展通过 INDEX.json 读取论文、公式、概念和 claim，结果使用相同 result/review/accept 流程。不同研究方向不修改公共 ID 体系。

repro-feasibility/repro-plan/verification 契约允许按需传 formula、principle、concept ArtifactRef，不需要复制整份分析。公式/原理解析到所在 analysis.yaml 的 `formulas[n]` / `first_principles[n]` YAML 锚点，由执行器选择对应对象；Markdown 用真实章节或 L 行号锚点。ArtifactRef.type 以机器实体为准，源文件中的短 id 不直接作为跨文件连接。

## 7. 兼容与验收

不新增顶层目录；论文仍为 meta.yaml 入口和 01_source～05_notes，四核心文件职责不变。旧字段/路径保留兼容读取；编号迁移使用复制，冲突不覆盖，旧原件由使用者核对后手动清理。旧 `.runs/<timestamp>-<task-id>` 日志可继续阅读，新闭环放 `.runs/<task-id>`，不改历史结果。

```powershell
python tools/wf.py validate --contracts
python tools/wf.py validate --links my-research
python tools/wf.py validate my-research
python -m unittest discover -s tests
python tools/wf.py doctor --offline --share-check
```

离线测试/doctor 验证接口、状态和连接约束，不证明真实服务认证有效或科学内容质量已核验。分享继续排除 `.env`、local 配置、`.runs/` 和私密研究资料，不修改真实 Key，不自动提交 Git。
