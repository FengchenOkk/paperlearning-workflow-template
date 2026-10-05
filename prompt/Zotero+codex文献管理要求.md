# 任务：升级论文工作流，加入 Zotero 联动与跨论文知识网络，并统一论文目录命名

## 零、总原则

当前仓库已经有一套论文阅读与复现工作流，顶层结构保持不变：

```text
config/
workflow/
projects/
tools/
tests/
```

本轮是增量升级，不新增顶层目录，不破坏已有功能。

必须保留：

- Codex+GPT 主模型、DeepSeek 子模型配置体系
- manual / mock / command / openai_compatible 适配器
- AGENTS 编排、任务包、`.runs/` 日志
- 文献、概念、知识网络、复现模块
- 无 API Key 时可回退到 manual 模式

必须先检查当前仓库，再增量修改。不要覆盖真实论文数据，不要提交真实密钥。

## 一、最终目录蓝图

### 1. 项目内文献目录

```text
projects/<project>/10_literature/
├── README.md
├── papers/
│   └── <citekey>/
│       ├── meta.yaml
│       ├── 01_source/
│       ├── 02_translation/
│       │   └── translation.md
│       ├── 03_reading/
│       │   └── reading.md
│       ├── 04_analysis/
│       │   └── analysis.yaml
│       └── 05_notes/
│           └── notes.md
├── concepts/
│   └── <concept-slug>.md
├── reading-list.md
├── matrix.md
├── knowledge-map.md
└── knowledge-graph.json
```

### 2. 每篇论文的文件夹功能

必须使用固定编号，方便快速识别：

```text
papers/<citekey>/
├── meta.yaml              # 论文身份证：元数据、分类、状态、Zotero 信息
├── 01_source/             # 原始材料：PDF、HTML、提取文本、Zotero 附件链接
├── 02_translation/        # 全文翻译：translation.md
├── 03_reading/            # 详细精读：reading.md
├── 04_analysis/           # 结构化分析：analysis.yaml
└── 05_notes/              # 临时笔记、疑问、灵感：notes.md
```

文件夹含义：

| 文件夹 | 功能 | 是否生成 |
|---|---|---|
| `01_source/` | 原始材料，只读；包含 PDF、提取文本、附件链接 | 部分生成 |
| `02_translation/` | 全文翻译，不是摘要 | 生成 |
| `03_reading/` | 全局定位、逐节精读、上下文、局限、复现线索 | 生成 |
| `04_analysis/` | 公式、概念、结构化抽取、第一性原理 | 生成 |
| `05_notes/` | 临时笔记、疑问、灵感，不作为正式结论来源 | 人工为主 |

`meta.yaml` 放在论文根目录，是入口文件，不放入子文件夹。

### 3. 原论文目录迁移规则

如果已有旧结构，必须提供迁移命令：

```text
旧 translation.md       -> 02_translation/translation.md
旧 reading.md           -> 03_reading/reading.md
旧 analysis.yaml        -> 04_analysis/analysis.yaml
旧 note.md              -> 05_notes/notes.md
旧 source/              -> 01_source/
```

要求：

- 使用 `tools/wf.py migrate <project> [--dry-run]`。
- 迁移时保留原文，不丢数据。
- 目标文件已存在时，不覆盖，输出冲突报告。
- 迁移完成后，旧路径只保留兼容提示，或由用户手动确认后删除。

### 4. workflow 模板

`workflow/templates/paper/` 必须与新论文目录一一对应：

```text
workflow/templates/paper/
├── meta.yaml
├── 01_source/.gitkeep
├── 02_translation/translation.md
├── 03_reading/reading.md
├── 04_analysis/analysis.yaml
└── 05_notes/notes.md
```

`tools/wf.py new paper <project> <citekey>` 必须直接复制出完整的新目录结构。

## 二、meta.yaml

论文元数据、分类、状态和 Zotero 信息统一放在 `meta.yaml`。

```yaml
citekey: TODO
title: TODO
authors: []
year: TODO
venue: TODO
doi: TODO
url: TODO
language: TODO

paper_role: TODO
# survey | classic | group-recent | method | benchmark | application | other

categories: []
topic_tags: []
difficulty: TODO
importance: TODO
reading_priority: TODO

status: unread
# unread | pre-read | reading | deep-read | synthesized

translation_status: none
# none | partial | complete

reading_status: none
# none | partial | complete

analysis_status: none
# none | partial | complete

concept_ids: []
formula_ids: []
first_principle_ids: []
next_action: TODO

zotero:
  library_type: TODO
  library_id: TODO
  item_key: TODO
  collection_keys: []
  tags: []
  attachment_paths: []
  version: TODO
  synced_at: TODO

created_at: TODO
updated_at: TODO
```

## 三、01_source 目录

`01_source/` 只放原始材料，默认只读。

结构建议：

```text
01_source/
├── paper.pdf
├── paper.md
├── attachments/
└── source-links.yaml
```

要求：

- PDF 默认为只读。
- `paper.md` 是提取文本，可重新生成。
- `attachments/` 放 Zotero 附件链接或用户手工复制的附件。
- 默认只记录附件路径，不复制大型 PDF。
- 不把翻译、精读、分析结果放进 `01_source/`。
- Zotero 同步只更新 `meta.yaml` 和 `01_source/` 的附件引用，不覆盖 `02_translation/`、`03_reading/`、`04_analysis/`。

## 四、02_translation 目录

```text
02_translation/translation.md
```

要求：

- 全文翻译，不是摘要。
- 保留章节编号、公式编号、图号、表号、引用标记。
- 术语第一次出现时使用：`中文（English）`。
- 重要术语链接到 `concepts/<concept-slug>.md`。
- 译者补充说明标为 `[译注]`。
- 长论文按章节分块翻译，逐段追加，不覆盖已完成内容。
- 原文为中文时，改为逐段白话转写和术语解释，不做机械翻译。
- 翻译进度由 `meta.yaml.translation_status` 记录。

## 五、03_reading 目录

```text
03_reading/reading.md
```

必须包含固定章节：

```markdown
# 论文精读：<citekey>

## 1. 全局定位
## 2. 论文地图与逻辑链
## 3. 逐节精读
## 4. 方法与公式
## 5. 实验设计与结果
## 6. 前因后果与代表文献
## 7. 局限性与边界条件
## 8. 与当前研究方向的关系
## 9. 复现线索
## 10. 待验证问题
## 11. 证据与来源索引
```

要求：

- 先看全局：研究对象、核心问题、重要性、领域位置、前置概念。
- 抓代表文献：综述、经典、课题组近期工作。
- 每节写清目的、假设、方法、证据、结论。
- 事实、作者声称、实验证据、读者推断、未知必须区分。
- 所有重要结论必须可追溯到 `01_source/` 和页码/段落。
- 第 9 节必须给复现模块提供候选 claim。
- 代表文献没有资料时写 `TODO(user)`，不要编造。

## 六、04_analysis 目录

```text
04_analysis/analysis.yaml
```

结构化分析统一放在这个文件。

```yaml
paper: <citekey>

overview:
  object: TODO
  core_problem: TODO
  why_important: TODO
  contributions: []
  position: TODO
  prerequisites: []

first_principles:
  - id: principle-slug
    statement: TODO
    source_refs: []

review_similarity:
  core_problem: TODO
  method_summary: TODO
  key_concepts: []

formulas:
  - id: eq-1
    label: TODO
    latex: TODO
    name_zh: TODO
    meaning: TODO
    symbols:
      - symbol: TODO
        meaning: TODO
        type_or_dimension: TODO
    assumptions: []
    derivation_steps: []
    intuition: TODO
    special_cases: []
    related_concepts: []
    source_refs: []
    confidence: TODO

concepts:
  - id: concept-slug
    role: introduced
    # introduced | used | compared | extended
    local_meaning: TODO
    source_refs: []
    understanding_status: TODO

extraction:
  claims: []
  method: {}
  data: []
  baselines: []
  metrics: []
  results: []
  limitations: []

reproduction:
  code_url: TODO
  data_url: TODO
  candidates: []
  signals: []

source_refs: []
```

要求：

- `formulas`、`concepts`、`extraction`、`reproduction` 必须保持固定字段。
- 论文没有公式时，`formulas` 可以为空列表，但字段不能缺。
- 第一性原理必须有稳定 `id`，并关联全局概念卡。
- `analysis.yaml` 负责机器可验证数据，`reading.md` 负责解释和推理。

## 七、05_notes 目录

```text
05_notes/notes.md
```

用途：

- 临时笔记
- 疑问
- 想法
- 后续待办
- 与当前论文相关的碎片信息

要求：

- 不作为正式结论来源。
- 正式结论必须进入 `03_reading/reading.md` 或 `04_analysis/analysis.yaml`。
- 可以随时清理，但删除前必须确认没有引用。

## 八、全局概念目录

```text
10_literature/concepts/<concept-slug>.md
```

使用 Markdown + YAML front matter。

```yaml
concept_id: TODO
aliases: []
type: foundational
# foundational | classic | current | emerging
status: not-started
# not-started | learning | understood | needs-review
is_first_principle: false
canonical_statement: TODO
first_defined_in: TODO
first_seen_year: TODO
prerequisites: []
related: []
contrasts: []
papers: []
```

正文至少包含：

1. 一句话定义
2. 为什么需要这个概念
3. 直观理解
4. 形式化定义
5. 公式与符号
6. 前因后果
7. 与相近概念的区别
8. 常见误区
9. 代表文献迷你综述
10. 开放问题

要求：

- 新概念说明替代或修正了什么旧概念。
- 旧概念说明为什么仍然重要。
- 每个概念链接相关论文和相关概念。
- 不自动合并概念，只生成候选建议。

## 九、Zotero 联动

### 1. 配置文件

```text
config/zotero.example.yaml
config/zotero.local.yaml   # gitignored
```

`config/zotero.example.yaml`：

```yaml
zotero:
  enabled: false
  mode: local
  # local | web | export

  local:
    base_url: http://127.0.0.1:23119/api/users/0
    timeout_seconds: 10

  web:
    library_type: user
    library_id: TODO
    api_key_env: ZOTERO_API_KEY

  export:
    path: TODO
    format: better-bibtex-json
    # better-bibtex-json | csl-json

  sync:
    direction: read_only
    attachment_mode: link
    # link | copy
    create_missing_papers: true
    update_metadata: true
    preserve_manual: true
    citekey_source: better-bibtex
```

项目级覆盖放在 `project.yaml`：

```yaml
zotero:
  collections: []
  category_map: {}
  tag_filter: []
  ignore_tags: []
```

要求：

- `ZOTERO_API_KEY` 只放 `.env` 或系统环境变量。
- `config/zotero.local.yaml` 加入 `.gitignore`。
- 默认只读，不修改 Zotero 库。
- 支持本地 API、Web API、Better BibTeX 导出三种模式。
- Zotero 不可用时，工作流必须继续可用。

### 2. CLI

```bash
python tools/wf.py zotero status <project>
python tools/wf.py zotero sync <project> [--dry-run]
python tools/wf.py zotero doctor
```

同步规则：

- 优先使用 Better BibTeX citekey。
- 没有 citekey 时使用 `zotero-<itemKey>`。
- DOI 优先去重，其次 item key，其次标题 + 年份。
- 疑似重复项输出报告，不自动覆盖。
- collection 映射到 `categories`。
- tag 映射到 `topic_tags`。
- 不覆盖人工填写的翻译、精读和分析。
- 不复制 PDF，默认只记录附件路径。
- 测试使用本地 fixture，不访问真实 Zotero。

## 十、跨论文知识网络

### 1. 目标

自动发现：

- 相同第一性原理
- 相似综述
- 高频概念重叠
- 概念前置、继承、对比、替代关系
- 核心桥梁论文
- 方向知识缺口
- 推荐学习顺序

### 2. 数据来源

只使用本地可追溯数据：

- `meta.yaml`
- `02_translation/translation.md`
- `03_reading/reading.md`
- `04_analysis/analysis.yaml`
- `concepts/<concept-slug>.md`
- `reading-list.md`
- `matrix.md`
- Zotero 元数据

### 3. 输出

```text
10_literature/knowledge-graph.json
10_literature/knowledge-map.md
```

`knowledge-graph.json` 结构：

```json
{
  "schema_version": 1,
  "generated_at": "TODO",
  "generated_from": [],
  "nodes": [],
  "edges": [],
  "clusters": [],
  "learning_path": []
}
```

节点类型至少包括：

- `paper`
- `concept`
- `principle`
- `topic`

边类型至少包括：

- `introduces`
- `uses`
- `extends`
- `contrasts`
- `prerequisite`
- `similar-first-principle`
- `similar-review`
- `similar-concept-set`
- `belongs-to-topic`

每条边必须包含：

```yaml
source: TODO
target: TODO
type: TODO
weight: 0.0
confidence: medium
evidence: []
status: candidate
# auto | candidate | verified
```

要求：

- 自动相似边只能是 `candidate`。
- 主模型或 verifier 审核后才可改为 `verified`。
- 不允许静默合并概念。
- 相似算法必须确定性、可解释。
- 不联网也能生成基础图谱。
- 可选 embedding，但不能成为硬依赖。

### 4. 默认算法

1. 概念重叠：Jaccard + IDF 加权。
2. 第一性原理共享：强连接。
3. 综述相似：比较 `core_problem`、`method_summary`、`key_concepts`。
4. 主题标签：相同 category/topic 形成辅助边。
5. 概念共现网络。
6. 可选模型审核候选边。

### 5. knowledge-map.md

必须包含：

```markdown
<!-- GENERATED:BEGIN -->
## 高频概念
## 第一性原理网络
## 相似综述聚类
## 概念前置关系
## 核心桥梁论文
## 推荐学习顺序
## 待验证关联
## 知识缺口
## 孤立概念与孤立论文
<!-- GENERATED:END -->
```

人工补充放在标记外，重新生成时不得覆盖。

## 十一、复现模块通用性与私有扩展

复现模块本轮只优化接口，不实现具体专业复现逻辑。

在 `project.yaml` 中增加：

```yaml
reproduction:
  profile: generic
  private_extension: TODO(user)
  extension_data: {}
```

在 `20_reproduction/README.md` 和 `workflow/reproduction.md` 中说明：

- 公共模板只提供通用 claim、可行性分析、计划、结果目录。
- 不同方向的具体复现实现放在新的 private 仓库。
- 私有仓库读取：
  - `claim.yaml`
  - `research-profile.yaml`
  - `03_reading/reading.md`
  - `04_analysis/analysis.yaml`
- 私有仓库写入：
  - `feasibility.md`
  - `plan.md`
  - `online/`
  - `lab/`
  - `results/`
- 公共模板不得硬编码专业方向。
- 私有仓库内容不得混入公共模板。

## 十二、整体优化

### 1. 稳定性

- 所有写文件操作原子化。
- 所有生成操作幂等，重复执行不破坏人工内容。
- `zotero sync`、`graph`、`index` 支持 `--dry-run`。
- 网络失败、Zotero 未启动、PDF 不存在时给明确提示和 fallback。
- 单个条目损坏不得中断整个扫描。

### 2. 兼容性

- 保持 Python 3.11+。
- 基础依赖仍为 `PyYAML`。
- Zotero 使用标准库 `urllib` + JSON，不强制 `pyzotero`。
- PDF 文本提取仍为可选 `pypdf`。
- 旧论文目录通过 `wf.py migrate` 迁移。
- 旧结构只给警告，不静默删除。

### 3. 准确性

- 所有结论必须有 `source_refs`。
- 所有自动边必须有证据、权重、置信度。
- 事实、作者声称、推断、未知必须区分。
- 禁止编造论文、引用、公式、实验和课题组工作。
- Zotero 同步不得覆盖人工结论。

### 4. 可重复使用性

- 生成文件包含：
  - `schema_version`
  - `generated_by`
  - `generated_from`
  - `generated_at`
- 输出排序稳定。
- 输入变化后可重新生成。
- 新配置必须有 example 和 README。
- 私有复现扩展接口稳定。

### 5. 安全

- `.env`、`config/models.local.yaml`、`config/zotero.local.yaml`、`.runs/` 必须 gitignored。
- `doctor --share-check` 检查：
  - 密钥文件是否被 Git 追踪。
  - 是否存在明显 Key 模式。
  - 是否误提交本地配置。
- 不打印完整 Key。
- README 说明误传 Key 后如何撤销。

## 十三、CLI 更新

保留现有命令，新增：

```bash
python tools/wf.py migrate <project> [--dry-run]
python tools/wf.py zotero status <project>
python tools/wf.py zotero sync <project> [--dry-run]
python tools/wf.py zotero doctor
python tools/wf.py graph <project> [--dry-run]
python tools/wf.py doctor --share-check
```

`wf.py index <project>` 自动生成：

- 项目根 `INDEX.md`
- `10_literature/knowledge-map.md`
- `10_literature/knowledge-graph.json`

`wf.py validate <project>` 增加检查：

- 论文目录是否为标准编号结构。
- `meta.yaml`、`analysis.yaml` 字段是否合法。
- 概念和第一性原理引用是否存在。
- 图谱边是否包含证据和置信度。
- 生成文件是否包含 schema 版本。
- Zotero 元数据是否合法。
- 旧结构是否提示迁移。

`wf.py demo` 必须使用 mock 和本地 fixture 走通：

```text
创建论文 -> Zotero 导出同步 -> 生成知识图谱 -> validate
```

不需要真实 Zotero 和 API Key。

## 十四、测试与验收

必须增加测试：

1. 新论文目录结构创建正确。
2. `wf.py migrate` 正确处理旧目录。
3. Zotero 本地 API fixture 解析。
4. Zotero Web API fixture 解析。
5. Better BibTeX JSON fixture 解析。
6. Zotero 同步去重和人工内容保护。
7. 知识图谱节点和边生成。
8. 第一性原理聚类。
9. 相似综述候选生成。
10. `knowledge-map.md` 人工区域不被覆盖。
11. `--dry-run` 不写文件。
12. `doctor --share-check` 不打印 Key。
13. 无 Zotero、无 API Key 时流程仍可用。
14. `python -m unittest discover -s tests` 通过。

验收标准：

1. 不新增顶层目录。
2. 每篇论文使用统一编号目录：
   `meta.yaml`、`01_source/`、`02_translation/`、`03_reading/`、`04_analysis/`、`05_notes/`。
3. Zotero 可选、只读、可回退。
4. 能生成 `knowledge-graph.json` 和 `knowledge-map.md`。
5. 能发现第一性原理、相似综述、高频概念重叠。
6. 所有自动关联有证据和置信度。
7. 重复运行不破坏人工内容。
8. 无 API Key、无 Zotero 时仍可 bootstrap/doctor/demo。
9. 复现模块保持通用，私有扩展接口清晰。
10. 最终输出：
    - 修改摘要
    - 新目录树
    - Zotero 使用说明
    - 知识图谱生成说明
    - 迁移说明
    - 测试命令和结果
    - 最多 10 条待确认问题

先检查仓库，分阶段实现：

第一阶段：统一论文编号目录与迁移。
第二阶段：Zotero 适配层与同步。
第三阶段：知识图谱与知识框架。
第四阶段：整体工程优化。
第五阶段：测试、文档和验收。

不要破坏现有功能，不要提交真实密钥和私密数据。