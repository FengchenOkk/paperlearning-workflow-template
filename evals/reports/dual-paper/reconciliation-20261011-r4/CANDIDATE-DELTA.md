# 候选级失败原因

冻结 precision 定义：没有独立判定的预测不计正确。旧预测表只按 type + 原文生成的哈希键匹配。键失配不能证明科学错误。以下保留实际键、对象 ID、原文及定位。

| 项目 | 当前原始模型比较 | 当前人工 precision |
| --- | --- | --- |
| A | 16/21 = 76.19% | 未计算；需要等价绑定与局部决定 |
| B | 17/18 = 94.44% | 未计算；需要等价绑定与局部决定 |

不会通过修改冻结 prediction-review / gold 或删掉有效候选改变这些历史比较。新的人类源归属评估须单独记录当前键的判定，采用相同窗口与阈值。

## A / RESEARCH_PROBLEM / fcf48675-a871-555a-93d5-d64fc593ba81

预测键：`c4b31b5148c91bdb953c4624338c8880a170e712437938e020adc70aec944398`；PDF 第 1 页；bbox `[63.15587615966797, 271.1330261230469, 532.1282958984375, 463.1760559082031]`。
分类：NONMATERIAL_METADATA_CHANGE；旧决定：human-source-A-a-problem-1。
Literal source heading removal changed the SHA-256 prediction key; same scientific statement/type.

```text
Optical phase modulators are critical components in integrated photonics, but conventional designs suffer from a
trade-off between modulation efﬁciency and optical loss.
```

## A / RELATIONSHIP_ANALYSIS / 1f8ffa09-f97d-531f-af7c-174c229cc6c2

预测键：`da79f21d9e04cfa03706851697cc5d382ea5927f353bd74daf24b61e8a146248`；PDF 第 7 页；bbox `[56.69093322753906, 375.8001403808594, 290.5704040527344, 578.4327392578125]`。
分类：MATERIAL_CONTENT_OR_TYPE_CHANGE；旧决定：human-source-A-a-prediction-c935580f9be3-1。
Scientific type changed, so the frozen type+text prediction key no longer matches.

```text
We further extracted the intrinsic complex refractive
index changes—Δn and Δk—of the monolayer WS2 as a
function of electrostatically induced carrier density for the
device with TOS/graphene electrodes (Fig. 4c and Sup-
plementary Information IV).
```

## A / PROCESS / 796f256a-90e7-5843-b1ef-f78416790de6

预测键：`6c6cce386755367dcc7aecf9a7fc3a4d9b6070b495ab70f2f9af21565e0130d4`；PDF 第 8 页；bbox `[56.692108154296875, 674.1483154296875, 290.5409851074219, 732.2403564453125]`。
分类：NEW_CANDIDATE；旧决定：无当前对象决定。
New source-anchored candidate has no entry in immutable prediction adjudication.

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

## A / METHOD / 4431a4f7-9c76-5c5d-a689-0ecd0447246c

预测键：`8d2324c7008bc8bc0c0742d2e9d60f14096a0a50b7321bbf10f67eaf138f2276`；PDF 第 8 页；bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。
分类：NEW_CANDIDATE；旧决定：无当前对象决定。
New source-anchored candidate has no entry in immutable prediction adjudication.

```text
Speciﬁcally, ﬂakes were ﬁrst picked up at 120 °C using the
PC polymer and subsequently transferred onto the target
substrate at 200 °C.
```

## A / METHOD / 45fa7f8a-268c-5371-af4d-3184f7ff31d4

预测键：`ef6e9b024ba55f3fd3fd815f230bf3b4167a830f39fdb6ada6c9397fab826190`；PDF 第 8 页；bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。
分类：NEW_CANDIDATE；旧决定：无当前对象决定。
New source-anchored candidate has no entry in immutable prediction adjudication.

```text
After transfer, the residual PC poly-
mer was completely removed by immersing the samples
in chloroform for 12 h.
```

## B / SIMULATION / 656715f2-1b94-5c6b-abf2-f0dbb5d7c5e3

预测键：`3eed8cbe5e1e2f83287ea33107b6547e145a931bed9a3fa7c28bce3e9bd7a570`；PDF 第 7 页；bbox `[306.1416931152344, 143.06312561035156, 562.7979125976562, 444.776123046875]`。
分类：NONMATERIAL_METADATA_CHANGE；旧决定：human-source-B-b-dft-method-1。
Literal source heading removal changed the SHA-256 prediction key; same scientific statement/type.

```text
First-principles DFT calculations were performed by using the Vienna 
Ab initio Simulation Package (VASP 5.4)⁴⁹ with the exchange-correlation 
functional based on Perdew–Burke–Ernzerhof ⁵⁰ generalized gradient 
approximation.
```

A 未召回 a-limitation：历史决定 human-source-A-a-limitation-2 明确 REJECT 为独立对象。原文仍完整保留为背景；冻结 gold 不删，16/17 召回率保持。此项无需重新问用户。
A 旧 PROCESS 汇总确有分组缺陷：包含 PL/Raman 光谱、激光功率与电阻表征整段。通用 v5 改为明确制备/处理原句的编译，遇到可能的小节标签分组，跨块断句保留原文延续。旧汇总保留在 production-corrections-20261011-r2；当前分组是 AI_INTERPRETATION，不暗示完整工艺顺序。
A 新增 METHOD 的 120/200 °C 转移与 12 h 聚合物去除均有原文证据；不能因没有冻结键而删去。关系句由 METHOD 改为 RELATIONSHIP_ANALYSIS，与既有人工要求一致，但当前新类型仍需显式确认。
B SIMULATION 不是全新科学陈述：旧 human-source-B-b-dft-method-1 已 ACCEPT 相同 DFT/VASP/PBE 原文和 SIMULATION 类型，唯一文字变化是前置 DFT calculations 标题分离。无需重复 DFT 内容评审，纳入 E0 等价映射。
B 原图再检查：Sb(0 1 -1 2) 的上划线位于第三个数字 1；Ion/Vth 的 on/th 为下标。浏览器已检查实际独立排版视图；V_th 仍注明此前为模型补充检查。
Equation 1 原始块、页码、定位不变。新 metadata 报告短线/根号/分式解释不确定；没有新增归一化公式、LaTeX 或 VERIFIED。历史 ACCEPT 只在原评审范围内保存，不用它消除该不确定性。冻结 gold/阈值不变；当前人工评估尚不能宣布 PASS。
