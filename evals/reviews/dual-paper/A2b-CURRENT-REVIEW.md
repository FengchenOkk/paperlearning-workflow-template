# A2b：WSe₂ 氧化处理的 METHOD 归属（待用户决定）

用户已回复 `A2a accept`，接受修订1中三个组的来源归属与分组边界。该决定不自动批准独立 METHOD 候选；此卡仅审核 A2b。实际 decision=null。

| 字段 | 原人工审核对象 | 当前对象 |
| --- | --- | --- |
| ID | 5089ade4-6914-566d-b785-ffb8ff1fa255 | ca8eacbf-78a0-52be-bdeb-1da5b078a992 |
| version | 1 | 1 |
| 类型 / layer | METHOD / SEMANTIC | METHOD / SEMANTIC |
| epistemic | AUTHOR_CLAIM | AUTHOR_CLAIM |
| 人工决定 | REVISE，human-source-A-a-fabrication-1 | 待本次决定；应用状态 CANDIDATE |

旧人工原话：

> revise，这只是WSe2氧化为TOS的处理，我觉得method最好把整个器件的结构和制备说明清楚，比如hBN、光调制的材料，器件如何搭建等

旧意见指出覆盖范围不足。历史 `human-source-A-a-fabrication-2` ACCEPT 的对象是扩展 REVISED_METHOD_VIEW；历史窄生产对象的 REVISE 保留。E0只保存该REVISE的等价绑定，不会将其升为ACCEPT。A2a当前制作组还引用了这句，但它的 ACCEPT 审核范围是汇编分组；此处需单独判定原句作为材料处理步骤的 METHOD 是否恰当。

本次没有改写原句、类型、数值或条件。审核范围被明确为 WSe₂→TOS 的 UV-ozone 材料处理步骤；它不独自代表整个器件的结构和完整制备。当前图仍只有结构性CONTAINS边，本卡不创建METHOD与PROCESS之间的科学关系。

原始PDF：[第8页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)。精度 TEXT_BLOCK；anchor `fe880ee9-81b8-51e4-8030-87dcfd598462`，span `eb04dcff-2dc1-5c33-bd30-ba60cd0ee94c`，字符 [0, 1146)，bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。anchor覆盖整个转移/氧化/表征源块，当前METHOD只取下面这一句。

```text
For controlled oxidation of as-
exfoliated WSe2 ﬂakes, UV-ozone treatment was per-
formed at 50 °C for 30 min in the UV ozone cleaner
(Samco UV-1), maintaining an oxygen ﬂow rate of
1 L/min, ensuring effective conversion of WSe2 into TOS.
```

中文释义：作者描述，对剥离后的WSe₂薄片采用UV-ozone处理，温度50 °C、持续30 min、设备Samco UV-1、氧流量1 L/min，用于受控氧化并转化为TOS。“ensuring effective conversion”保留为作者表述，本次不证明转化效果或科学有效性。

![氧化原文](E:/PaperLearning/.runtime/gate-a-a2a-revision-20261011/review-a2b/original-oxidation-context.png)

图首的“in chloroform for 12 h.”是前一句去除PC的上下文，属于A4，不是本氧化步骤的时间条件。A2b从“For controlled oxidation”开始，到“into TOS.”结束。完整上下文：

![转移、氧化和光学表征源块](E:/PaperLearning/.runtime/gate-a-reconciliation-20261011/review-a2a/transfer-oxidation-context.png)

技术建议：ACCEPT 此句作为 SEMANTIC/AUTHOR_CLAIM 的独立材料处理 METHOD，并保留50 °C、30 min、Samco UV-1、1 L/min以及WSe₂/TOS限定。此为模型建议，不是用户决定。请判断这个限定范围的METHOD归属是否合适；若要求修改，可指定类型、范围或标题。需要完整器件结构与制备时，应引用对应综合视图和各原始证据，不把这一句冒充完整流程。

source SHA256 `30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`；current evidence fingerprint `5bccb35ed640dec575650e40bf1fffd3c63f7561d3a9285da24f98afff670437`；parser `1.28.2+layout-v3-notation`，当前隔离评估pipeline `source-graph-v6`。该未变的独立对象仍保留原创建器 `local-rule-extractor-v4`。

等待 A2b ACCEPT / REVISE / REJECT 后才呈现A3。历史记录、冻结gold/模型分数不改；当前人工指标在全部审核完成后计算；不创建SCIENTIFIC_VALIDITY VERIFIED，不进入Gate B。
