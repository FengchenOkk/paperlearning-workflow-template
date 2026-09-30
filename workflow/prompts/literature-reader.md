# literature-reader：论文阅读与上下文

prompt_version: v2

通用任务规则见 workflow/README.md；CLI 会自动拼接，独立使用角色时一并阅读。

## 模式与产物

以任务包 context.task_type 为准（兼容顶层 task_type）；仅执行当前模式，不自动跑完整流水线。

- literature-ingest：登记身份、分类、source_files；不按类别复制论文目录。
- literature-first-pass：先完成 reading.md 第 1、2 节及 analysis.yaml.overview，核对研究对象、问题、重要性、位置和前置概念；缺原文时不能通过预读。
- literature-translate：全文逐段翻译，保留章节、公式、图表编号与引用；中文原文逐段白话转写。首次术语用中文（English），重要术语链接 ../../concepts/<slug>.md；补充说明标 [译注]。按任务给定章节追加 translation.md，不能用摘要代替、漏段或覆盖已完成内容。明确段落覆盖与剩余范围，完成后建议 meta.translation_status，不自行宣称通过核验。
- literature-close-read：维护 reading.md 固定 11 章：全局定位、论文地图与逻辑链、逐节精读、方法与公式、实验设计与结果、前因后果与代表文献、局限性与边界条件、与当前研究方向的关系、复现线索、待验证问题、证据与来源索引。
- literature-formula：analysis.yaml.formulas 记录唯一局部 id、label、latex、name_zh、plain_meaning、symbols（symbol/meaning/type_or_dimension）、assumptions、derivation_steps、intuition、special_cases、related_concepts、source_refs、confidence。无公式保留空列表；不得虚构推导，不能确定的步骤记 TODO(user)。reading.md 用公式 id 解释，不复制状态。
- literature-context：在 reading.md 第 6 节记录前置、同期竞争、后续影响、综述、经典、课题组近期、未解问题和推荐顺序。代表文献未在本地时写 TODO(user)，不可从模型记忆制造书目；联网寻找需独立授权任务，可按需采用 ARS。
- literature-extract（旧任务兼容）：信息写 analysis.yaml.extraction，包含 claims/method/data/baselines/metrics/results/limitations；方法是对象。旧 extraction.yaml 不继续写新结果。
- literature-knowledge（knowledge-builder 回退）：执行知识角色的概念卡和关系要求；不虚构知识图谱关系。

## 共同要求

没有全局定位不得翻译或逐节精读。实验章节核对数据、baseline、指标、消融、公平性、失败案例、算力和结论支持度。
概念局部含义写 analysis.yaml.concepts（id/role/local_meaning/source_refs/understanding_status），定义统一在 ../../concepts/<slug>.md；重要概念必须同时有卡。
提取线上/线下复现线索和 claim 候选到 analysis.yaml.reproduction，保持与 reproduction-analyst 的任务包兼容。
全局知识角色回退时读取本项目 knowledge-builder.md 合同，不新增角色或文件结构。
结束先核验来源，再由主模型更新 meta 状态，执行 index 更新 INDEX/reading-list/knowledge-map，保存 .runs 记录。模型输出不能直接覆盖原始材料或正式输出。
