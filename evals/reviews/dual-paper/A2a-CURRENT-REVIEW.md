# A2a：制作/处理摘录汇编（待用户决定）

A1 已按用户原话 `accept` 单独记录为 SOURCE_ATTRIBUTION ACCEPT。此卡仅呈现 A2a；decision=null，技术建议不代替用户决定。

| 字段 | 当前对象 |
| --- | --- |
| ID / version | 796f256a-90e7-5843-b1ef-f78416790de6 / 1 |
| 类型 / layer | PROCESS / SEMANTIC |
| epistemic / application status | AI_INTERPRETATION / CANDIDATE |
| 创建器 / pipeline | local-rule-extractor-v4 / source-graph-v5 |
| 来源 | 原始 PDF 第8页，三个 source anchors |
| prediction key | 6c6cce386755367dcc7aecf9a7fc3a4d9b6070b495ab70f2f9af21565e0130d4 |
| evidence fingerprint | d98c272eab324e059b660897b6cdd6891fffb02101fcde78d52cc145de4a7dec |

冻结原始输出没有对应 PROCESS；E0 不涵盖新对象。上一版未人工审核的 v4 PROCESS `49a9fa05-72a8-54df-b034-b813b6674c5c` 汇编了 SiN 制作、HS 制作、光学/电学表征整块文字。当前 v5 改为具体制作/处理句，SiN 制作另成对象，剔除厚度光学核对、PL/Raman 和片电阻测量描述，并保留跨栏的 PC stamp 原句续接。历史 `human-source-A-a-fabrication-2` ACCEPT 仅批准 REVISED_METHOD_VIEW，不能批准这个生产 PROCESS。

这是 AI 的来源摘录分组；论文没有把以下合并文本列为一个完整流程。未推导统一执行顺序，未评估科学有效性。

当前 node exact text：

```text
TMDs, graphene, and hBN ﬂakes were mechanically
exfoliated onto SiO2/Si substrates.
The HS stack comprising
these exfoliated ﬂakes was fabricated using a dry-transfer
technique facilitated by a polycarbonate (PC) stamp.
Speciﬁcally, ﬂakes were ﬁrst picked up at 120 °C using the
PC polymer and subsequently transferred onto the target
substrate at 200 °C.
After transfer, the residual PC poly-
mer was completely removed by immersing the samples
in chloroform for 12 h.
For controlled oxidation of as-
exfoliated WSe2 ﬂakes, UV-ozone treatment was per-
formed at 50 °C for 30 min in the UV ozone cleaner
(Samco UV-1), maintaining an oxygen ﬂow rate of
1 L/min, ensuring effective conversion of WSe2 into TOS.
Electrical
contacts were fabricated onto the samples using standard
lithographic and metal deposition techniques, enabling
precise voltage biasing and current measurement.
```

来源链接：[原始 PDF 第8页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)。原图与当前证据如下：

![剥离与干法转移原文](E:/PaperLearning/.runtime/gate-a-reconciliation-20261011/review-a2a/exfoliation-context.png)

![转移、清洗、氧化及后续光学表征上下文](E:/PaperLearning/.runtime/gate-a-reconciliation-20261011/review-a2a/transfer-oxidation-context.png)

![电接触所在的片电阻表征完整段落](E:/PaperLearning/.runtime/gate-a-reconciliation-20261011/review-a2a/electrical-contact-context.png)

Anchor `ce800448-3107-5a24-94ac-94187a44d833`，span `8afbd8f8-ffda-520e-bdca-fe357ac604c0`，page 8，字符 [0, 272)，bbox `[56.692108154296875, 674.1483154296875, 290.5409851074219, 732.2403564453125]`。anchor 覆盖整源块，当前对象只取其中制作/处理句。

Anchor `fe880ee9-81b8-51e4-8030-87dcfd598462`，span `eb04dcff-2dc1-5c33-bd30-ba60cd0ee94c`，page 8，字符 [0, 1146)，bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。anchor 覆盖整源块，当前对象只取其中制作/处理句。

Anchor `36f5fa38-19d3-5f4c-a51c-09a43e63d6a0`，span `8002fd82-1f6f-5caa-b8b1-cad43f93dfc0`，page 8，字符 [0, 586)，bbox `[304.7234802246094, 351.87469482421875, 538.5851440429688, 481.2027282714844]`。anchor 覆盖整源块，当前对象只取其中制作/处理句。

技术建议：REVISE 分组边界。机械剥离、PC 干法转移（120 °C 拾取、200 °C 转移）、氯仿12 h去除残余 PC、UV-ozone（50 °C、30 min、Samco UV-1、氧流量1 L/min）都有原文支持。最后的 electrical contacts 句也确实存在，但原段明确讨论 pristine graphene / TOS-doped graphene 的片电阻表征样品。建议保留原句和证据，把它单列为表征样品的制备，避免让汇编暗示它属于同一个 HS 器件制作流程。

需要用户判断：这些摘录是否忠实；PROCESS/AI_INTERPRETATION 分类及当前分组是否合适；最后一句是否应分开。ACCEPT 会接受当前这个包含电接触句的分组；REVISE 会保留有效事实并调整分组；REJECT 会拒绝此汇编对象。建议为模型意见，实际决定仍为空。请仅回复 A2a ACCEPT / REVISE / REJECT。

source SHA256 `30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`。当前对象在隔离复评 DB，审核不产生 SCIENTIFIC_VALIDITY VERIFIED；历史决定与冻结 gold/模型分数保留。完成 A2a 后才呈现 A2b。
