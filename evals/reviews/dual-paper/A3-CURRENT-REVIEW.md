# A3：PC 拾取与转移步骤的 METHOD 归属（待用户决定）

用户回复 `A2b accept`，已接受A2b的来源归属与独立材料处理METHOD分类。此卡只呈现A3；实际decision=null。

| 字段 | 当前对象 |
| --- | --- |
| ID / version | 4431a4f7-9c76-5c5d-a689-0ecd0447246c / 1 |
| type / layer | METHOD / SEMANTIC |
| epistemic / application state | AUTHOR_CLAIM / CANDIDATE |
| 原冻结输出中的对应对象 | 无；NEW_CANDIDATE，没有对应原人工决定 |
| pipeline / 对象创建器 | source-graph-v6 / local-rule-extractor-v4 |

修正内容：通用提取规则将Methods中的被动拾取/转移原句提取为独立METHOD。这是相对于原冻结生产的新对象，不能通过E0获得旧ACCEPT。A2a已接受的制作汇编和历史已接受的扩展REVISED_METHOD_VIEW都引用这些事实，但审核范围不同；本项明确审核这个独立METHOD的类型、原句边界及当前定位。没有改写论文，没有补充样品、基底或操作条件；不创建METHOD与PROCESS的科学关系边。

原始PDF：[第8页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)。source anchor `fe880ee9-81b8-51e4-8030-87dcfd598462`，span `eb04dcff-2dc1-5c33-bd30-ba60cd0ee94c`，字符 [0, 1146)，bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。证据精度TEXT_BLOCK；anchor包含整块转移/氧化/表征上下文，此对象只取以下一句：

```text
Speciﬁcally, ﬂakes were ﬁrst picked up at 120 °C using the
PC polymer and subsequently transferred onto the target
substrate at 200 °C.
```

中文释义：作者描述，先使用PC聚合物在120 °C拾取薄片，随后在200 °C转移至目标基底。先后次序在原文“ﬁrst … subsequently …”中明确给出。该句未独立说明目标基底的材料、停留时间或完整器件搭建方式。

![拾取与转移原文](E:/PaperLearning/.runtime/gate-a-a2a-revision-20261011/review-a3/original-pickup-transfer-context.png)

图首PC stamp是前一句的上下文；A3从“Speciﬁcally”开始，到“substrate at 200 °C.”结束。同一行后面的“After transfer”属于A4的PC去除步骤。完整原块上下文：

![完整源块](E:/PaperLearning/.runtime/gate-a-reconciliation-20261011/review-a2a/transfer-oxidation-context.png)

技术建议：ACCEPT 这句作为SEMANTIC/AUTHOR_CLAIM的独立METHOD，保留PC材料、120 °C拾取、200 °C转移和原文先后次序。请判断类型及一句的范围是否合适、温度对应操作是否准确、当前源证据是否充分。该建议不是人类决定；不评估工艺科学有效性。

source SHA256 `30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`；current evidence fingerprint `7151983b5835cbb72d275e5401840aec7bec7f94cd0edafbb8953310b79288d9`；prediction key `8d2324c7008bc8bc0c0742d2e9d60f14096a0a50b7321bbf10f67eaf138f2276`；parser `1.28.2+layout-v3-notation`。对象来自当前隔离评估DB，应用状态保持CANDIDATE；无SCIENTIFIC_VALIDITY VERIFIED。

等待 A3 ACCEPT / REVISE / REJECT 后才呈现A4。历史记录、冻结gold及模型分数保留；当前人工指标在全部审核完成后计算；Gate B不开始。
