# 论文通读与概念学习手册

先建立方向项目、归档论文和提取文本，确认 analysis.overview 与 reading 第1/2节。然后按“全文翻译/精读 → 公式和全局概念卡 → 代表文献 → 综合总结和学习指南 → 主模型核验”的顺序推进。适用于任何学科和已配置的模型/API/CLI/manual，不依赖 DeepSeek 或特定论文。

## 从哪里开始阅读

项目 INDEX.md 的“论文通读入口”直接链接四类成果；论文自己的目录中：

| 文件 | 用途 |
|---|---|
| 06_synthesis/summary.md | 连贯理解全文：对象、问题、重要性、论证主线、方法证据、公式机制、结果、代表文献、框架、局限、方向关系与来源 |
| 06_synthesis/concept-guide.md | 对照学习：底层原理→前置概念→方法/器件→论文图表，含符号单位、假设、例题、误区、自测和知识网络 |
| 02_translation/translation.md | 按原文顺序逐段翻译，保留章节/公式/图表/引用；补充解释用[译注] |
| 02_translation/coverage.yaml | 分段范围、源哈希、任务ID和译文标记的覆盖清单 |
| 03_reading/reading.md | 十一节精读、推理过程、图表解释与复现线索 |
| 04_analysis/analysis.yaml | 可被其他任务复用的公式、概念、主张、方法和证据数据 |
| 10_literature/concepts/*.md | 项目共享概念定义；综合成果链接卡片，避免重复维护 |

06_synthesis 按需在验收时生成；新建论文仍保留原有结构，四核心文件不变。summary/guide 是衍生解释，不另存进度；进度只在 meta.yaml。跨论文正式报告另放30_outputs。

## 生成标准任务包

在仓库根目录执行，把 my-research 和 MyPaper2026 替换为实际项目与 citekey：

```powershell
python tools/wf.py index my-research
python tools/wf.py study plan my-research MyPaper2026 --dry-run
python tools/wf.py study plan my-research MyPaper2026
```

plan 不调用模型，不翻译或验证科学内容。它读取 meta.source_files 中已登记的 UTF-8 .md/.txt 原文，生成项目00_inbox/study-* 下的逐段翻译、literature-synthesis 和 literature-learning-guide 任务以及 coverage.yaml。仅有 PDF 时，先提取文本并人工核对阅读顺序和公式；扫描PDF需自行OCR，工具未内置PDF解析。附录/补充材料如需翻译，先取得并登记，缺失时明确范围。

默认片段上限5500字符，可用 --segment-chars 指定500–10000；按完整行切分，不截断单行。对跨页/跨片段句子按原序衔接；图内数字、参考书目和作者名可原样保留，正文与图注完整翻译。固定原文及分段大小后重复plan幂等；已有不同任务或清单会报冲突、保留原件。源改变时重新建任务，不能沿用旧accept。

## 执行、复核、追加

使用plan打印的真实路径和task_id，按 [任务闭环手册](task-orchestration.md) 执行：

```powershell
python tools/wf.py task run my-research projects/my-research/00_inbox/study-HASH/translate-HASH-001.yaml
# 预览通过且已有外部调用授权时，使用同一命令加 --execute
python tools/wf.py task review my-research translate-HASH-001 --attempt 1
# 当前会话实际对照原文审核后，导入真实review.yaml
python tools/wf.py task review my-research translate-HASH-001 --attempt 1 --review projects/my-research/00_inbox/review.yaml
python tools/wf.py task accept my-research translate-HASH-001 --attempt 1
```

以上HASH是占位说明，不可原样执行。必须先验收一个片段，再为下一片段构建上下文，防止目标译文哈希过期。未提交、未评审或manual未完成不算完成；不通过用task revise，沿用既有主模型返修规则。每段content必须有任务给出的首尾translation标记，避免重复或漏追加。审核包含语义、数字、单位、图注和原文编号，结构检查不能代替它。

```powershell
python tools/wf.py study coverage my-research MyPaper2026
python tools/wf.py validate my-research
```

coverage核对源完整范围、源变化、每段标记、非空内容和真实accept记录；不判断译文正确。逐段核验和覆盖均完成后，执行器才能更新meta.translation_status；已有旧论文不强制补清单。

## 形成两份可通读成果

综合总结要求十一节：阅读导航、全局定位、全文主线、方法与证据、公式与机制、结果与意义、代表文献与前因后果、知识框架、局限与待核验、与研究方向的关系、来源索引。

概念指南要求十节：学习导航、底层原理、概念频次与层次、从原理到器件、公式逐步解释、对照论文学习、代表文献导读、知识网络、自测与常见误区、来源与缺口。既解释为什么需要，又说明适用条件；重要新增概念派literature-knowledge进入全局卡和analysis，重要公式派literature-formula，避免只有散落正文。

plan生成的综合任务是起点：执行器按缺口补充已核验章节、卡片、论文证据和代表文献记录，再派发。限定YAML字段/Markdown章节，避免整份大文件反复上传。要区分综述、经典和课题组近期工作，并标记取得全文/只读摘要/仅核对书目；没有材料就保留TODO(user)，不能伪造“已综述”。本文词频、项目论文覆盖数与学习优先级分开报告。

两项任务沿用相同task run→submit→真实review→accept闭环。默认summary使用literature-reader，guide使用knowledge-builder；后者缺失/禁用时按原规则回退literature-reader并记录。不改个人Profile或凭据，旧任务仍兼容。综合输出带study_delivery front matter与来源，正式写入前检查身份、结构和引用；重要结论还须主模型核对原始证据。

## 返修与主模型接管

先查看实际任务状态和本轮评审的问题，不根据模型自检判断是否通过：

```powershell
python tools/wf.py task status my-research task-id
```

| 记录中的情况 | 处理方式 |
|---|---|
| 子模型初稿有可修复问题 | 主模型给真实 revise 评审，再用 task revise 建立一次子模型返修 |
| 子模型一次返修后仍有问题，或已达到合同的子模型尝试上限 | 同一 task revise 自动使用主模型 Profile；保留失败草稿、问题、必要证据与原验收标准，不再循环交给子模型 |
| 主模型为当前 Codex 会话/manual | 读取新尝试的 prompt.md 完成修复，再 submit、真实 review、accept；waiting-manual 表示等待接力，不表示完成 |
| 响应格式错误、尚无有效 result | 保留原响应，由主模型整理或修复后接力提交，再审核；不能补造失败标准或通过记录 |
| 输入锚点、哈希或上下文限制不满足 | 主模型修正任务包；输入已变化则新建 task_id，原失败记录保留并注明后继任务 |
| 缺原文、补充材料或实验数据 | 保留 block/partial 和明确缺口；主模型接管也不能把缺失证据变成已核验 |

子模型上限默认3次，但一次返修仍失败即提前接管；主模型修复默认另有1次机会，仍失败则 block/escalate，不无限重试。主模型修复稿也须提交后再审核。API/CLI调用沿用已有授权和 --execute，未授权时只生成接力包。具体命令见[任务闭环手册](task-orchestration.md#5-主模型评审与正式应用)。

结束时逐条对照失败 criterion 与最终成果，不只查看 accepted 字样；旧失败任务若已有验收通过的后继任务，在收尾记录中建立对应关系，原 blocked 状态不改成 accepted。论文主体成果可验收，科学缺口继续以 meta 和 ROADMAP 记录。

## 上下文与性能

性能优化在输入与重试范围：分段有界、YAML字段锚点、完整上下文检查、可选JSON响应和只返修出错片段。不以缩写译文或省略核验换取速度，也不保证任意模型一次就能返回有效格式。
要求完整上下文的返修遇到长草稿时，执行器按不重叠行锚点拆成有界片段；仍须满足总上下文限制，源变化、单行超限或总量超限时在调用前阻止。这样保持完整草稿而不放宽原有合同限制；旧任务默认行为保留。
