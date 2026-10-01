# 论文功能升级验收记录

## 模型任务分配优化验收（2026-10-01）

补充：按用户后续要求，子模型一次返修仍失败（或达到子模型尝试上限）时，由 task revise 自动切换主模型修复。沿用原合同、必要草稿和证据，当前 Codex 会话取得接力 prompt，API/CLI 按 orchestrator Profile 和 --execute 调用；主模型默认1次修复仍失败再 block。执行与结果日志及 INDEX.tasks 明确记录 main/main-repair、接管原因、主模型次数；修复后仍需独立评审和 accept。

补充验证：195项全量测试通过；新增7项覆盖主会话接力、主Profile实际路由（mock响应）、外部调用授权边界、主修复后再验收、失败次数限制、接力重跑保持最小返修上下文、源变更阻断及子模型次数上限接管。最后增加主模型结果来源记录后，另重跑16项评审/接管回归；未调用真实API或修改连接/密钥。

按《模型任务分配要求.md》增量完成。主模型负责计划与验收（commander-reviewer），子模型按合同执行（primary-executor）。沿用当前 Codex/GPT 主会话和现有 DeepSeek 角色连接，其他提供商仍通过原 Profile/适配器选择；本轮没有真实模型或 Zotero 调用。

### 修改摘要与目录

增加 registry.py（稳定身份/连接索引）与 tasks.py（上下文、提交、评审、返修、正式应用）；wf.py 保留旧命令并加入新入口。文献、Zotero、图谱与复现接口共用 INDEX.json，不新增顶层目录、不新增基础依赖。

```text
config/                       # 模型/Zotero配置，local与Key仍私有
workflow/
  task-contracts.yaml          # 12类任务的输入、输出与验收标准
  task-orchestration.md        # 分工、示例和CLI手册
  templates/ prompts/ vendor/
projects/<project>/
  project.yaml research-profile.yaml
  INDEX.md INDEX.json
  00_inbox/
  10_literature/
    papers/<citekey>/
      meta.yaml
      01_source/
      02_translation/translation.md
      03_reading/reading.md
      04_analysis/analysis.yaml
      05_notes/notes.md
    concepts/<slug>.md
    reading-list.md matrix.md knowledge-map.md knowledge-graph.json
  20_reproduction/<citekey>--<claim-slug>/
    claim.yaml feasibility.md plan.md online/ lab/ results/
  30_outputs/
  .runs/<task-id>/
    task.yaml status.yaml
    context/                  # manifest.yaml context.md files/
    attempts/<n>/             # prompt/response/result/artifact-index/self-check + 草稿
    reviews/<n>/              # 最小评审包、验收标准、证据与链接
    reviews/<n>.yaml           # 真实主模型决定
    revision-requests/ final/ # 返修必要材料、应用记录与备份
tools/ tests/
```

目录按需创建。项目 init/index 会生成 INDEX.json；当前仓库只有 _template，没有为用户猜测研究方向或创建真实项目。

### ID、连接与合同

- ID：project/paper/concept/principle/topic/task 各使用 `<type>:<slug>`；公式为 `formula:<citekey>:<formula-id>`，claim 为 `claim:<citekey>:<claim-slug>`，尝试为 `attempt:<task-id>:<n>`，其他产物为 `artifact:<artifact-id>`。分析/译文/精读分别为 analysis/translation/reading 前缀。移动和重命名保留已存 ID，旧路径/citekey/Zotero key 使用持久 aliases。
- INDEX.json 仅保存对象定位、锚点、哈希、链接和任务状态，可删除重建，重复运行字节稳定。任务输入与输出使用 ArtifactRef；生成的 path 不是主键。短公式/原理 id 保留旧兼容，跨对象连接用 object_id；概念旧类别 type 保留，object_type 指明 concept。
- 正式文件自身 links 是关系来源，含 rel/target/evidence/confidence/status，图谱由索引解析并派生。无证据或悬空关系报告并跳过；自动相似仅 candidate，新 verified 关系需主模型逐条 link_checks。人工地图、matrix 和清单备注保留。
- task-contracts.yaml 覆盖现有 12 类路由；无合同、验收标准、必需输入或类型不匹配则不派发。上下文只展开指定章节/行号或 YAML 对象，具有硬大小限制、哈希、缓存与截断标记。主模型默认只收摘要、产物引用、标准与证据索引；API 抽查必须显式提供必要片段。
- 子模型提交 result/artifacts 草稿，新草稿登记独立 ID；自检和 mock 都不能通过验收。主模型 accept 须所有标准通过并核对来源；revise 须映射失败 criterion。子模型一次返修仍失败或达到最多3次子模型尝试上限即由主模型接手，主模型默认1次；返修只带问题及相关材料，未修改草稿自动沿用。
- accept 才应用正式文件并刷新任务状态、INDEX.json、图谱、地图和 INDEX.md；输入、合同或目标变化会拒绝陈旧应用。运行错误会回滚正式文件与连接视图，并保留审计备份。
- Zotero 默认 CLI 预览，--apply 才同步；按稳定 aliases 去重，collection/tag 连接 topic。私有复现读取同一索引/ArtifactRef，并提交同一结果与评审包；专业实验执行仍待后续配置。

### CLI

```powershell
python tools/wf.py index my-research --json
python tools/wf.py validate --contracts
python tools/wf.py validate --links my-research
python tools/wf.py task run my-research projects/my-research/00_inbox/task.yaml
python tools/wf.py context my-research task-id
python tools/wf.py task status my-research task-id
python tools/wf.py task submit my-research task-id --attempt 1 --result projects/my-research/00_inbox/result.yaml
python tools/wf.py task review my-research task-id --attempt 1
python tools/wf.py task review my-research task-id --attempt 1 --review projects/my-research/00_inbox/review.yaml
python tools/wf.py task accept my-research task-id --attempt 1
python tools/wf.py task revise my-research task-id --attempt 1 --review projects/my-research/.runs/task-id/reviews/1.yaml
```

旧 run/run --main 与旧路径任务继续可用，草稿不自动应用；ArtifactRef 新任务进入新闭环。真实外部调用沿用 --execute 明确授权。完整可复制任务、提交和按需 --evidence 抽查示例见 [任务手册](task-orchestration.md)。

### 验证结果

- `python -m unittest discover -s tests -q`：188 项通过，含原 110 项回归与新增 78 项；覆盖稳定 ID/改名/重建、重复/悬空、合同拒绝、最小上下文/评审、草稿登记、来源失效、accept 联动/回滚、增量返修、Zotero 别名及人工内容保护。
- 最后补齐核心连接字段后，针对 registry 与原文献升级重新执行 59 项回归，通过；评审 9 项再次检查。
- `validate --contracts`、离线 `doctor --offline --share-check`、原 mock/fixture demo、`git diff --check` 通过。结构检查不代表科学内容或真实服务认证已核验。
- SHA-256 比对：.env、config/models.local.yaml、tools/adapters.py 与本轮开始时一致。没有写入 Git 提交、推送、原始论文或个人认证；测试在临时目录进行。

### 后续待确认（3项）

1. 提供研究方向/项目及第一篇真实论文，验证精读质量与证据覆盖。
2. 用小任务验证实际 DeepSeek/API 网络与账户连接，并根据结果调整任务范围与成本。
3. 后续配置专业复现扩展的实验输入、指标与执行权限。

以下保留上轮文献升级验收记录；其测试数和“下一步配置模型”仅描述当时阶段。

日期：2026-10-01。范围：统一编号目录、可选 Zotero 只读同步、跨论文知识图谱、通用私有复现接口；模型分工由用户下一步配置。

## 修改摘要

- 五个顶层目录保持 config/workflow/projects/tools/tests，基础依赖仍为 PyYAML、Python 3.11+。
- 新论文直接生成编号目录，四核心文件职责保持；旧目录复制迁移、备份元数据、报告冲突，兼容旧任务包路径。
- Zotero local/web/export 接入使用标准库 GET/JSON，支持 Better BibTeX/CSL，按 DOI/item key 去重，标题＋年份给人工确认建议。
- 同步只改书目及附件引用，保护人工字段、翻译、精读、分析与进度；重复同步保持 meta/source-links 不变，缺服务/Key 不阻断基础工作流。
- 图谱离线确定性生成第一性原理、综述和概念候选关联，附证据/权重/置信度；保留地图人工区与审核备注，输入变化使旧核验过期。
- 公共复现保持通用 claim/feasibility/plan/online/lab/results，project.yaml 新增私有扩展声明，本轮不执行专业实验。
- 文件写入使用同目录暂存与原子替换；index/graph/migrate/zotero sync 支持不写文件的 dry-run。
- 分享检查新增 Zotero 本地配置与编号原文目录，密钥检测区分代码调用和真实值，输出仅显示位置。

## 新目录树

```text
config/
├── README.md
├── models.example.yaml
└── zotero.example.yaml
workflow/
├── literature.md
├── zotero.md
├── reproduction.md
└── templates/paper/
    ├── meta.yaml
    ├── 01_source/.gitkeep
    ├── 02_translation/translation.md
    ├── 03_reading/reading.md
    ├── 04_analysis/analysis.yaml
    └── 05_notes/notes.md
projects/<project>/
├── project.yaml
├── research-profile.yaml
├── INDEX.md
├── 00_inbox/
├── 10_literature/
│   ├── README.md
│   ├── papers/<citekey>/          # 与上述论文模板一致
│   ├── concepts/<slug>.md
│   ├── reading-list.md
│   ├── matrix.md
│   ├── knowledge-map.md
│   └── knowledge-graph.json
├── 20_reproduction/<citekey>--<claim>/
└── 30_outputs/
tools/
├── wf.py
├── literature.py
├── adapters.py
├── zotero.py
├── knowledge.py
└── storage.py
tests/
├── test_wf.py
├── test_model_integration.py
├── test_literature_upgrade.py
└── fixtures/zotero/
```

模型及 Zotero 的 .local.yaml、.env、原文和运行日志仅本机保留，不属于公开分享集。

## 使用与迁移

先创建项目或使用已有项目，将下列 my-research 换成项目名。

```powershell
python tools/wf.py bootstrap
python tools/wf.py zotero status my-research
python tools/wf.py zotero sync my-research --dry-run
python tools/wf.py zotero sync my-research

python tools/wf.py graph my-research --dry-run
python tools/wf.py graph my-research
python tools/wf.py index my-research
python tools/wf.py validate my-research

python tools/wf.py migrate my-research --dry-run
python tools/wf.py migrate my-research
```

Zotero 默认为 disabled；启用和模式选择见 [Zotero 手册](zotero.md)。图谱算法、字段、标记区、旧路径迁移细节见 [文献手册](literature.md)。迁移不删除原件，目标冲突需人工合并，旧原件核对引用后由用户手动清理。索引/图谱只做结构和确定性候选计算，不替代科学核验。

## 测试与结果

```powershell
python -m unittest discover -s tests -b
python tools/wf.py doctor --offline --share-check
python tools/wf.py demo
git diff --check
```

- unittest：110 项通过（原 80 项适配编号路径/提示版本后继续保留，新增 30 项）。
- 新增覆盖：目录与跨平台 citekey、复制迁移/冲突/备份/重复执行、旧任务路径、本地/Web API fixture 与分页/GET/重定向、Better BibTeX/CSL、去重/字段归属/人工保护、附件链接/可选复制、网络/Key/配置失败回退、图谱节点/边/原理聚类/综述相似、前置排序、标记区与审核备注、dry-run、损坏条目继续扫描、schema/证据检查、原子写失败保留原件、实际 Git 忽略/密钥脱敏及误报回归。
- offline doctor/share-check：通过；.env、models.local.yaml、zotero.local.yaml 均忽略且未跟踪，明显真实密钥风险 0。ARS 已核对的两处假 Key 仍按原规则标注；未修改 vendor。
- demo：通过“创建论文 → 本地 Zotero mock 导出同步 → 图谱 → validate → mock 模型任务”；不联网、不需要 Key，临时目录清理，projects 无真实研究项目或演示残留。
- git diff --check：通过。未执行用户工作区的 git add/commit/push。
- SHA-256 校验：用户 .env、config/models.local.yaml、tools/adapters.py 与升级前一致；没有修改主/子连接或分工，未调用真实模型 API。
- Python 语法/重复定义和关键模板 YAML 重复字段检查通过。

## 能力边界与后续待配置

本轮完成工程功能及离线验收，真实 Zotero 本地/Web 连接尚未测试；真实论文翻译、精读与科学图谱质量尚未验收。PDF 提取/OCR 和专业复现实验未实现，embedding 不属于硬依赖。

没有阻断本轮实现的待确认项。后续三项由用户选择：
1. Zotero 来源模式、库/集合与分类标签映射。
2. GPT 和 DeepSeek 的角色分工、审核顺序及调用权限。
3. 首篇真实论文与研究画像，用于科学内容验收。
