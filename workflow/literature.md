# 文献阅读与知识工作流

## 七个阶段

0. 手动/Zotero 入库分类：原文放 01_source/；身份、分类、进度唯一写 meta.yaml。
1. 全局预读：确认研究对象、核心问题、重要性、领域位置、前置概念和论文逻辑链。
2. 分段翻译与精读：全文逐段翻译保留编号；中文原文白话转写；固定 11 章记录解释和证据。
3. 公式与概念：结构化数据写 04_analysis/analysis.yaml；全局概念一张卡，第一性原理有稳定 id 和概念关联。
4. 代表文献：综述、经典、课题组近期工作分开；缺资料写 TODO(user)，不编造引用。
5. 跨论文网络：index/graph 生成可追溯候选图谱；对比矩阵由人工维护。
6. 核验综合：verifier 和主模型检查科学结论、译文覆盖与候选关系，确认进度后形成正式输出。

## 统一编号目录

```text
10_literature/
├── README.md
├── papers/<citekey>/
│   ├── meta.yaml
│   ├── 01_source/
│   │   └── source-links.yaml          # Zotero 同步时按需生成
│   ├── 02_translation/translation.md
│   ├── 03_reading/reading.md
│   ├── 04_analysis/analysis.yaml
│   └── 05_notes/notes.md
├── concepts/<concept-slug>.md
├── reading-list.md
├── matrix.md
├── knowledge-map.md
└── knowledge-graph.json
```

四个核心事实来源的职责保持：meta 管身份/进度，translation 管全文译文，reading 管解释推理，analysis 管机器数据。05_notes 为临时疑问和灵感，不作为正式结论来源；删除前确认没有引用。原始 PDF、提取文本和附件引用只放 01_source；工具不覆盖已有原文。PDF 解析/OCR 未内置，文本提取可以在外部选用 pypdf，不属于基础依赖。

citekey 保留安全的 Better BibTeX 键和大小写；目录避免大小写碰撞。其他项目、概念与任务标识仍使用小写 kebab-case。来源相对于项目，支持 #page=3、#paragraph=2、#eq=1、#L42；源文件存在检查不证明科学结论正确。

论文状态 unread/pre-read/reading/deep-read/synthesized；翻译、阅读和分析进度 none/partial/complete，仅写 meta，不在正文重复。meta 新增 first_principle_ids 与 zotero 绑定信息；原 source_files/code_links/data_links 保留。

## 翻译、精读与结构化分析

02_translation/translation.md 必须逐段完整翻译，保留章节、公式、图表编号和引用。首次术语写中文（English），概念链接使用 ../../../concepts/<slug>.md，补充标 [译注]；长论文按章节追加并记录覆盖，不能用摘要代替。

03_reading/reading.md 固定 11 节：全局定位、论文地图与逻辑链、逐节精读、方法与公式、实验设计与结果、前因后果与代表文献、局限性与边界条件、方向关系、复现线索、待验证问题、证据与来源索引。先确认第 1/2 节，再进行全文翻译或逐节精读；第 9 节给出候选 claim。事实、作者声称、实验证据、读者推断与未知必须区分。

04_analysis/analysis.yaml 保持 overview/formulas/concepts/extraction/reproduction 固定字段，新增：
- first_principles：id、statement、source_refs，以及可选 concept_ids；未指定关联时 id 对应同名全局卡，不能关联空列表。
- review_similarity：core_problem、method_summary、key_concepts；用于确定性综述比较，不自动抽取或编造正文。
- formulas 仍支持旧 plain_meaning，也接受 meaning 别名；公式 id 唯一，符号带含义和维度，置信度为 0..1 或 TODO(user)。无公式保留空列表。
- 概念局部角色 introduced/used/compared/extended；全局定义在概念卡维护。

第一性原理结论必须有来源；重要公式、概念与抽取结论均需定位到原始证据。schema 只验证结构，科学正确性、完整译文覆盖和作者结论支持度仍由人/模型核验。

概念卡保留原十节与字段，新增 is_first_principle、canonical_statement、extends、replaces。prerequisites/related/contrasts/extends/replaces 仅记录已声明且有来源的关系；不自动合并概念。

## Zotero 联动

见 [Zotero 接入手册](zotero.md)。默认关闭，支持本地 API、Web API、Better BibTeX JSON 和 CSL JSON 导出。只读同步补书目和附件引用，保护人工字段、译文、精读、分析和状态；疑似重复报告不自动覆盖。Zotero 不可用时使用手动入库。

## 清单、分类与跨论文图谱

```powershell
python tools/wf.py index my-research --dry-run
python tools/wf.py index my-research
python tools/wf.py graph my-research --dry-run
python tools/wf.py graph my-research
python tools/wf.py validate my-research
```

index 更新项目 INDEX、reading-list、knowledge-map 和 knowledge-graph.json；graph 只更新图谱及知识地图。dry-run 不写文件、不创建迁移日志。不需要 API Key、Zotero、embedding 或联网。

reading-list 保持唯一清单，front matter reading_notes/topic_paths/reading_order 为人工说明与顺序；生成标记之外的备注保留。INDEX 按 category/topic/paper_role/status 分组并展示时间线，不复制论文。matrix.md 仍为人工对比表，工具不覆盖。

图谱 schema_version=1，包含 generated_by/generated_at/generated_from、nodes、edges、clusters、learning_path、input_hashes 与算法说明。节点至少 paper/concept/principle/topic；边包括 introduces/uses/extends/contrasts/prerequisite、三类 similar-*、belongs-to-topic；另外记录 related/replaces/co-occurs。每条边都有权重、置信度、证据文件与字段、状态。

默认算法：
1. 概念按不同论文去重；相似分数为普通 Jaccard 与 IDF 加权 Jaccard 的平均。IDF=1+ln((1+N)/(1+df))。
2. 相同稳定第一性原理 id 建立强候选边，权重 1；相同 id 不等于科学原理已核验一致。
3. 仅 paper_role=survey 的论文比较 review_similarity 三个字段。英文词及中文二元字符分词，三个 Jaccard 取平均，阈值 0.25；TODO 和空值不贡献相似性。
4. 分类/主题形成辅助边，概念共现只形成候选；前置图决定概念学习顺序，循环或缺卡明确阻断。
5. 第一性原理/综述聚类为候选连通组，桥梁论文用无向候选网络中介中心性排序，不代表质量或真实影响力。

相似和共现边始终 candidate，声明关系为 auto；都不是科学结论。主模型/verifier 核验后可将 JSON 中相应边改为 verified，建议同时写 reviewed_by/reviewed_at/review_note。再次生成仅在输入哈希和证据一致时保留核验；输入变化降回 candidate，不能沿用过期核验。

knowledge-map 固定生成区包含高频概念、第一性原理网络、相似综述聚类、前置关系、桥梁论文、学习顺序、待验证关联、知识缺口和孤立点。人工补充必须放在 `<!-- GENERATED:BEGIN -->` / `<!-- GENERATED:END -->` 外，重建会保留。缺失标记的手工正文不会删除，首次在末尾追加生成区；旧整文件自动视图转为新格式。

图谱使用本地 meta、analysis、概念卡、译文/精读、reading-list、matrix 和已入库 Zotero 元数据记录来源；自动关系主要依据结构化字段，不从自由文本制造“事实”。损坏条目报告并继续扫描；validate 不会把损坏条目当作验收通过。

## 旧目录迁移

```powershell
python tools/wf.py migrate my-research --dry-run
python tools/wf.py migrate my-research
python tools/wf.py index my-research
python tools/wf.py validate my-research
```

translation.md → 02_translation/translation.md；reading.md → 03_reading/reading.md；analysis.yaml → 04_analysis/analysis.yaml；note.md → 05_notes/notes.md；source/ → 01_source/。

迁移采用复制，不移动或删除原件。目标不同则报告冲突，不覆盖；元数据补字段/旧状态映射之前备份至 .runs/*-migration-*/meta.before.yaml，并记录 run.yaml 中的路径映射。核对编号文件和引用后，旧原件由用户手动确认删除。迁移不把旧进度重新标为科学已核验。

最早期 overview/close-reading/context/note 合入对应精读节的“旧内容待整理”；extraction/formulas/concepts 合入分析，未知结构保留 legacy_*。collections/catalog/synthesis 原件保留，人工整理。

index 沿用旧版“补缺失骨架”的安全行为，也可复制生成编号目录，目标文件不覆盖；正式升级建议先显式 migrate 预览。旧平铺文件仍能兼容读取，原件清理后旧任务包/来源路径会定位到对应编号路径。旧相对概念链接兼容提示，手工改为 ../../../concepts/<slug>.md。模型 local、旧任务契约和复现 claim 关联不自动改写。

## 最小任务示例

先创建论文，手工归档原文及提取文本并登记 meta.source_files。实际任务包放项目 00_inbox：

```yaml
task_id: first-pass-001
role: literature-reader
objective: 完成全局定位与论文逻辑链，输出带来源的草稿
inputs:
  - research-profile.yaml
  - 10_literature/papers/first-paper/meta.yaml
  - 10_literature/papers/first-paper/01_source/paper.md
allowed_paths:
  - 10_literature/papers/first-paper
context:
  task_type: literature-first-pass
  paper_citekey: first-paper
output_schema: null
source_refs:
  - 10_literature/papers/first-paper/01_source/paper.md
```

执行 `python tools/wf.py run my-research projects/my-research/00_inbox/first-pass.yaml`。manual 提供 prompt，人工接力 response；适配器输出仅是 .runs 草稿，主模型核验后才写正式文件、更新 meta 和 index/validate。

后续 task_type 保持 literature-translate/close-read/formula/context/knowledge，旧 ingest/extract 仍可用。翻译任务加 section_range 与 append_only: true；无完整 analysis.overview 不允许全文翻译/逐节精读。知识角色缺失或禁用仍回退 literature-reader。本轮未调整 GPT/DeepSeek 分工、没有自动执行科学实验。
