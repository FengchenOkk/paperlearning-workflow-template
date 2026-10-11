# 当前人工源审核评价 — 2026-10-11

用户实际回复 `B2 accept` 已记录。既定七项局部审核完成；按不变的冻结协议，当前 reviewed Gate A：**A PASS / B PASS**。Gate B **NOT_STARTED**，科学有效性 **NOT_ASSESSED**，没有创建应用 verification 或科学 VERIFIED。

| 指标 | A 当前人工源评价 | B 当前人工源评价 | 冻结阈值 |
| --- | --- | --- | --- |
| Precision | 22/22 = 100% | 18/18 = 100% | ≥90% |
| Recall | 16/17 = 94.12% | 16/16 = 100% | ≥80% |
| Matched type accuracy | 16/16 | 16/16 | ≥90% |
| Anchor / page correctness | 16/16 各项 | 16/16 各项 | 100% |
| Selected figure captions | 3/3 | 3/3 | 100% |
| Numbered equation localization | 明确 N/A | 1/1 | 100% / N/A |
| Selected quantities | 10/10 | 11/11 | 100% |
| All-node provenance | 59/59 | 78/78 | 100% |
| All-edge provenance | 58/58 | 77/77 | 100% |
| Integrity ERROR / duplicate warnings | 0 / 0 | 0 / 0 | 零未解决 ERROR |

模型键比较独立保留：当前 v6 A **16/22 = 72.73%**，B **17/18 = 94.44%**；旧 r4 A **16/21 = 76.19%**、B **17/18 = 94.44%** 及全部原报告不修改。人工 precision 使用实际当前窗口全部候选，不缩小分母，不删除 gold，不把实际聊天审核冒充 MODEL_SOURCE_REVIEW。

A 的22个正确身份/类型判定由14项E0原ACCEPT引用、2项原范围内的真实 explanation-only clarification、6个窗口内新ACCEPT对象组成。后者为A1、A2a制作组和光学表征组、A2b、A3、A4。A2a接受的电学表征组在窗口外，未扩大分子/分母；其他全文候选仍未审核。两个 explanation-only 原决定继续保持REVISE，判定正确不等于补造ACCEPT。A的显式ACCEPT引用覆盖为20/22，与协议precision22/22区分。

B由16项E0原ACCEPT引用与B1/B2两项当前真实ACCEPT组成。旧Sb横线和稳定性下标REVISE不改写，当前决定另存。所有35项E0绑定中的5个原REVISE标签保留；原有限授权与来源范围不扩展。A被拒绝的背景LIMITATION仍是冻结gold的缺失项，因此recall保留16/17。

Equation1：同一原PDF、页码、源块文字、offset、bbox和历史定位范围保持不变。本轮直接核对原始PDF像素，根号、分式、下标与历史已接受的视觉转写一致。选定源的读法没有未解决字形歧义；当前自动解析器对短数学横线/根号分式的**自动重构仍未知**，不生成规范化公式、不扩展E0到新符号解释，也不声称科学核验。定位1/1本身没有被当作自动转写通过。A另外两处shifted-glyph unknown位于未选定的源块，保留为全文解析限制。

数量评价逐项引用原21条真实数量审核，核对当前完整源、限定及语义上下文相同；不重新造ACCEPT。已修正的panel labels/Article模板误分类保留原9个实例来源，旧REVISE不改写。

复用本次v6修订已经通过的后端/前端检查和真实公开PDF、两篇原PDF浏览器结果。它们的实现及内容由修订manifest绑定；没有再次启动整套测试或浏览器，也没有把复用结果描述为本轮新运行。

证据：[A评价](paper-a.json)、[B评价](paper-b.json)、[评价manifest](manifest.json)、[评价时完整审核快照](current-source-review-at-evaluation.json)、[完成状态](completion.json)。逐候选判定均有来源、实际决定或澄清引用；新评估器不修改原评估器。当前可变审核账本：[CURRENT_SOURCE_REVIEW](../../../../evals/reviews/dual-paper/CURRENT_SOURCE_REVIEW.json)。[冻结协议](../../../../docs/evaluation/PAPER-GRAPH-EVIDENCE-GATE.md)。

所有分数只覆盖冻结窗口/gold样本。原PDF、canonical图谱、gold、阈值、历史人工账本及旧评估报告保留；Gate A PASS不代表研究级全文能力或科学有效性。按用户要求，停在Gate B之前。
