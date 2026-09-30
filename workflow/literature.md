# 文献阅读与知识工作流

## 七个阶段

0. 入库与分类：原文放 source/；身份、categories、topic_tags、paper_role、进度唯一写 meta.yaml。
1. 全局预读：先确定研究对象、核心问题、重要性、领域位置与前置知识，再开始翻译或精读。
2. 分段翻译与精读：全文逐段翻译保留编号，中文原文白话转写；固定 11 章解释和证据写 reading.md。
3. 公式与概念深挖：公式、局部概念写 analysis.yaml；一个全局概念一张卡，解释假设、推导、前后关系与边界。
4. 代表文献与领域上下文：综述、经典、课题组近期分开；本地缺失写 TODO(user)，不制造引用。
5. 跨论文知识网络：index 重建分类、阅读清单和知识网络；对比矩阵由人工维护。
6. 验证与综合：verifier 核对翻译、公式、概念与来源，主模型确认进度和复现候选后形成正式输出。

## 四个核心文件

| 文件 | 唯一职责 |
|---|---|
| meta.yaml | 论文身份、分类与状态、concept_ids/formula_ids、下一步 |
| translation.md | 全文翻译/中文白话转写，逐段追加和覆盖记录 |
| reading.md | 全局定位、逻辑链、精读、公式解释、实验、上下文、局限、方向关系、复现线索、疑问和证据索引 |
| analysis.yaml | overview、formulas、concepts、extraction、reproduction 的机器数据 |

source/ 只放原始材料。schema 契约统一在 workflow/schemas.yaml 中；analysis.paper 仅是关联键，不复制身份与状态。
论文状态为 unread/pre-read/reading/deep-read/synthesized；翻译、阅读和分析进度分别 none/partial/complete，统一写 meta。reading/translation front matter 不再维护进度。

## 公式、概念与来源

公式 id 在每篇论文内唯一，结构字段见 schemas.yaml 的 analysis 契约；暂无公式保持空列表。符号需说明 meaning 与 type_or_dimension，置信度为 0..1 或 TODO(user)。
概念卡位于 concepts/<slug>.md，项目内唯一。论文局部概念 role 为 introduced/used/compared/extended；相关卡和前置/对比/关联卡都必须存在。
source_refs、source_files 使用项目相对路径，source_refs 允许 #page=3、#paragraph=2、#eq=1、#L42。来源存在检查不证明定位与科学内容正确。

## 阅读清单、分类与知识网络

reading-list.md 是唯一清单。front matter 的 reading_notes 存 citekey → 阅读理由（字符串或 why_read 对象），topic_paths 存主题 → citekey 列表，reading_order 存推荐顺序；年份、类别、优先级和状态自动从 meta 生成。
手工备注写在生成标记区外，index 保留；没有标记的旧清单不覆盖，提示添加标记。阅读理由和人工顺序优先，未给理由写 TODO(user)，默认按优先级标签字符串稳定排序，不推断重要性。
INDEX 按 category/topic/paper_role/status 分组并展示时间线，论文只存一份，不建物理类别目录。
knowledge-map 按不同论文统计概念频次（meta、analysis、卡 papers 去重），列出未理解概念、前置关系、声明关系连通组、新旧类型分布、学习顺序、孤立点和缺口。存在缺卡或循环时明确阻断，不能伪造完整顺序。
matrix.md 保留手工跨论文比较，index 不覆盖。建议列论文、问题、方法、数据、指标、主要结果、局限、可复现性、方向关系。

## 任务与模型

context.task_type：literature-first-pass、literature-translate、literature-close-read、literature-formula、literature-context；literature-knowledge 交给默认禁用的 knowledge-builder，未配置/禁用时回退 literature-reader。旧 literature-ingest/extract 仍可用。
翻译和精读任务必须通过 context.paper_citekey 或唯一论文输入指明论文；analysis.overview 的 object/core_problem/why_important/position 均有实际内容才可调度。机器前置检查不能代替主模型确认预读质量。
按章节使用 context 中的 section_range 和 append_only: true（角色任务数据，不是新调度配置）；adapter 只返回草稿到 .runs，不自动覆盖 translation 或写入正文。主模型审核后逐段追加，并更新 meta。当前未实现翻译模型、PDF 解析或 OCR；使用 manual/已配置模型处理文本。

## 兼容与迁移

当前真实项目为空，直接收缩自有模板，第三方 ARS 不改。
对旧项目 validate 只输出迁移警告，不删除；index 自动补充缺失新骨架：
- overview → reading 第 1 节，close-reading → 第 3 节，context → 第 6 节，note → 第 10 节；保持旧文本原样待整理。
- extraction → analysis.extraction；旧 method 列表保存在 method.legacy_items，额外字段放 legacy_extraction，原件保留。
- formulas/concepts 的列表合入 analysis 对应字段；未知格式保存在 legacy_* 并提示人工整理。概念全局内容需人工建卡，不能猜测定义。
- 只补缺失 reading/analysis/translation，已有新文件不覆盖；冲突内容仍保留旧文件，需人工合并。
- meta 补字段，triage → pre-read、read/extracted → deep-read；原 meta 副本和操作记录写 .runs/*-migration-*。这只是旧状态映射，不代表精读已重新验证。
- collections/catalog/synthesis 保留并警告。collections 阅读路径合入清单注释；catalog 功能由 INDEX 替代，确认内容后才能清理旧目录；synthesis 工作稿可移到 10_literature 下具名 Markdown 文件，正式版本放 30_outputs。
- 旧 schema 路径在 run 中别名解析为 schemas.yaml#task/paper/claim；不新增空 JSON 文件。旧 local 配置在内存补路由和知识角色回退，保留提供商、密钥变量和复现路由。
迁移不会把不完整旧格式静默标为有效；缺少公式字段/概念卡时按新契约报告待整理。

## 当前能力边界

已提供文件、模式提示、模型调度、分类统计、知识关系排序、校验与迁移。没有自动生成可靠科学解释、完整翻译、真实实验结果或联网文献。ARS 只作按需流程参考，未自动启用其完整流水线。

## 最小任务示例

先用 new paper 创建论文，手工归档原文及已提取的文本，并登记 meta.source_files。将实际任务包放项目 00_inbox，沿用原任务包格式：

```yaml
task_id: first-pass-001
role: literature-reader
objective: 完成全局定位与论文逻辑链，输出带来源的草稿
inputs:
  - research-profile.yaml
  - 10_literature/papers/first-paper/meta.yaml
  - 10_literature/papers/first-paper/source/paper-text.md
allowed_paths:
  - 10_literature/papers/first-paper
context:
  task_type: literature-first-pass
  paper_citekey: first-paper
output_schema: null
source_refs:
  - 10_literature/papers/first-paper/source/paper-text.md
```

运行 `python tools/wf.py run my-research projects/my-research/00_inbox/first-pass.yaml`。manual 在运行目录生成 prompt，人工提供 response；主模型核验后填入 reading 和 analysis 并更新 meta，再执行 index/validate。后续翻译任务换 task_type 为 literature-translate，增加 context.section_range 和 append_only，输入包含已确认的 analysis、原文片段和现有 translation；不会自动覆盖译文。
