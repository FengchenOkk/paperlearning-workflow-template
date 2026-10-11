# A4：残余 PC 聚合物去除步骤的 METHOD 归属（待用户决定）

用户回复 `A3 accept`，已接受A3的来源归属与独立拾取/转移METHOD分类。此卡只呈现A4；实际decision=null。

| 字段 | 当前对象 |
| --- | --- |
| ID / version | 45fa7f8a-268c-5371-af4d-3184f7ff31d4 / 1 |
| type / layer | METHOD / SEMANTIC |
| epistemic / application state | AUTHOR_CLAIM / CANDIDATE |
| 原冻结输出中的对应对象 | 无；NEW_CANDIDATE，没有对应原人工决定 |
| pipeline / 对象创建器 | source-graph-v6 / local-rule-extractor-v4 |

修正内容：通用提取规则把Methods中的被动去除原句提取为独立METHOD。它是相对于原冻结生产的新对象；原文的“poly- / mer”跨行保持原样，没有补充清洗温度、额外试剂或实验条件。E0不包含新对象。A2a的制作汇编以及历史扩展REVISED_METHOD_VIEW都引用此事实，但不会自动批准这个独立METHOD。本项审核它的类型、原句边界及当前定位；不创建METHOD与PROCESS之间的科学关系边。

原始PDF：[第8页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)。source anchor `fe880ee9-81b8-51e4-8030-87dcfd598462`，span `eb04dcff-2dc1-5c33-bd30-ba60cd0ee94c`，字符 [0, 1146)，bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。证据精度TEXT_BLOCK；anchor包含整块转移/氧化/表征上下文，此对象只取下面一句：

```text
After transfer, the residual PC poly-
mer was completely removed by immersing the samples
in chloroform for 12 h.
```

中文释义：作者描述，在转移后，将样品浸入氯仿12 h，以去除残余PC聚合物。原文“was completely removed”是作者的表述；本次仅核对这句来源和方法归属，不证明去除效果。

![PC去除原文](E:/PaperLearning/.runtime/gate-a-a2a-revision-20261011/review-a4/original-polymer-removal-context.png)

图首“substrate at200°C.”属于A3的转移上下文；A4从“After transfer”开始，到“in chloroform for12h.”结束。后面的“For controlled oxidation”属于A2b，12h对应去除PC步骤。完整源块：

![完整源块](E:/PaperLearning/.runtime/gate-a-reconciliation-20261011/review-a2a/transfer-oxidation-context.png)

技术建议：ACCEPT 此句作为SEMANTIC/AUTHOR_CLAIM的独立METHOD，保留“转移后”、残余PC、氯仿浸泡和12h限定。请判断类型及一句的范围是否合适、溶剂与时间是否忠实、当前源证据是否充分。该建议不是实际人类决定，不评估工艺科学有效性。

source SHA256 `30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`；current evidence fingerprint `f6896cf62390b1d39b6bdce3acd5c694fa218337cb4275a05dc824a95fa1dd62`；prediction key `ef6e9b024ba55f3fd3fd815f230bf3b4167a830f39fdb6ada6c9397fab826190`；parser `1.28.2+layout-v3-notation`。对象来自当前隔离评估DB，应用状态保持CANDIDATE；无SCIENTIFIC_VALIDITY VERIFIED。

等待 A4 ACCEPT / REVISE / REJECT 后才呈现B1。历史记录、冻结gold及模型分数保留；当前人工指标在全部审核完成后计算；Gate B不开始。
