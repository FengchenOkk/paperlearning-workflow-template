# Gate A precision 下降诊断 — 2026-10-11

诊断范围：冻结模型比较 `current-a.json/current-b.json` 对照当前 `reconciliation-20261011-r4` 的 v5 普通生产输出。没有修改生产代码、PDF、冻结 gold、预测评审、阈值或历史人工决定；没有创建当前人工 ACCEPT。

## 1. 分数下降如何组成

| 论文 | 原冻结模型比较 | 当前冻结模型比较 | 当前人工 precision |
| --- | --- | --- | --- |
| A | 19/19 = 100% | 16/21 = 76.19% | 未计算，待 E0 及局部真实决定 |
| B | 18/18 = 100% | 17/18 = 94.44% | 未计算，待 E0 及局部真实决定 |

这里的旧 100% 是 MODEL_SOURCE_REVIEW 的预测表比较，绝不是历史 HUMAN_SOURCE_REVIEW 全部 ACCEPT。历史人工评审已指出 A 背景独立对象应 REJECT、关系句 METHOD 类型不适合，且 B 上划线/下标应 REVISE。旧 reviewed Gate A 已是 FAIL，不能把旧模型 100% 当成人工认可的起点。

模型评估器用 `SHA256(type + "\n" + 原文)` 查冻结 prediction-review；没有该键就写 UNREVIEWED/correct=false。它没有消费当前人工映射或新决定，所以未计正确并不等于科学上错误。对象 UUID 或纯 bbox/heading/notation 元数据变化本身不改变这个键；此次两处 literal heading 从 node.text 分离才改变文本键，关系句的 type 变化改变类型键。

- A 分母：旧 19 − 已人工 REJECT 的背景 1 + 新 PROCESS/两条 METHOD 3 = 当前 21。
- A 原比较分子：旧 19 − 被移除的背景 1 − Abstract 前缀键失配 1 − METHOD→RELATIONSHIP_ANALYSIS 键失配 1 = 当前 16；三个新增对象无冻结键，也未获计分。
- B：18 个陈述均保留；去掉 DFT calculations 标题导致一个文本键失配，故 18 − 1 = 17，分母仍为 18。
- 两篇当前没有新键的预测共六个；另列 A 已移除的旧背景，解释旧分子的第三个减少及 recall 16/17。

## 2. 逐项原对象、现对象及证据

ID 必须分清：原冻结生产报告来自一次独立运行；历史人工审核针对 canonical DB 对象；当前 v5 是另一独立运行。三者 UUID 不同不是科学内容差异。原冻结运行的 current-a-runtime/current-b-runtime 数据库已不在对应报告目录，报告本身不存 anchor ID；不得把 canonical 的 anchor 冒充该原运行 anchor。下面明确标注可核验的历史人工 source anchor，以及冻结生产报告实际保留的 page/bbox。当前 anchor 来自当前真实 isolated DB。

### A-失分1：摘要问题句，评估键失配

当前 key：`c4b31b5148c91bdb953c4624338c8880a170e712437938e020adc70aec944398`。
当前生产对象：`fcf48675-a871-555a-93d5-d64fc593ba81`，类型 `RESEARCH_PROBLEM`，版本 1，当前 evidence fingerprint `06e53eea2ba9573b60d8fa424474ea93a93304923a97d5b74d43ad504702a097`。
原 PDF：[第 1 页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)；source SHA-256 `30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`。
原冻结生产对象：`188fa286-c451-5072-9b9b-1fb10f0060f1`，类型 `RESEARCH_PROBLEM`，key `3777317fe9c4627ac181ca9f922c60e36ced693803d404a521128ce6d9fff7ce`；源 page 1，bbox `[63.15587615966797, 271.1330261230469, 532.1282958984375, 463.1760559082031]`。
历史人工对象：`0f0c6539-8405-56a5-9982-06affec07eaf`，版本 1；历史决定 `human-source-A-a-problem-1` / **ACCEPT**；用户原话：accpet，摘要第一句没问题。
历史人工 source anchor：`74a81bb7-141a-5b4d-a9bc-854fa0b1eb06`；span `2cd0d0b4-b4c3-5fcb-9a3c-352ce4ea331d`；page 1；字符区间 [0, 1621)；bbox `[63.15587615966797, 271.1330261230469, 532.1282958984375, 463.1760559082031]`。

原科学陈述（包含旧标题时原样列出）：

```text
Abstract
Optical phase modulators are critical components in integrated photonics, but conventional designs suffer from a
trade-off between modulation efﬁciency and optical loss.
```

当前科学陈述：

```text
Optical phase modulators are critical components in integrated photonics, but conventional designs suffer from a
trade-off between modulation efﬁciency and optical loss.
```

当前 source anchors：

- `2a961331-6b49-5d9e-ae14-16166653b4b8`；span `d7995251-fd43-5210-a611-799eb3b27f04`；page 1；字符区间 [0, 1621)；bbox `[63.15587615966797, 271.1330261230469, 532.1282958984375, 463.1760559082031]`。

为什么不计正确：Literal source heading removal changed the SHA-256 prediction key; same scientific statement/type.
技术分类：`NONMATERIAL_METADATA_CHANGE`。
证明：原源 hash/page/offset/bbox/整块文字相同=True；去掉实际源中标题后的科学原文相同=True；type 相同=True；layer/epistemic 相同=True。
结论：评估文本键失配兼 metadata-only change；不是已证实的新 false positive、错误科学类型或科学内容损失。工程上不应把标题塞回科学陈述去追旧键；评估层需要 E0 的可审计有限绑定。无需重新审核同一问题句/DFT 科学内容，历史 ACCEPT 的范围不扩展。
完整 source text/metadata、类型/layer/epistemic、指纹与新旧映射见当前 paper-a.json 的 graph_node_mapping；本报告中的候选正文逐字取自记录，没有补科学文字。

### A-失分2 / A1：关系句改类型，修正旧类型后尚未重新判定

当前 key：`da79f21d9e04cfa03706851697cc5d382ea5927f353bd74daf24b61e8a146248`。
当前生产对象：`1f8ffa09-f97d-531f-af7c-174c229cc6c2`，类型 `RELATIONSHIP_ANALYSIS`，版本 1，当前 evidence fingerprint `0f232489156f560555b4487df78216b5b89fca14ff8877d24390fd424cbb2067`。
原 PDF：[第 7 页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)；source SHA-256 `30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`。
原冻结生产对象：`79fd3de3-5357-5e8f-9d7a-2cec72739741`，类型 `METHOD`，key `c935580f9be3e0df4cc1187c71ad463cc5dc39af96ea51a8ba94c8e21f751699`；源 page 7，bbox `[56.69093322753906, 375.8001403808594, 290.5704040527344, 578.4327392578125]`。
历史人工对象：`bed7a52b-9932-559a-b389-e7cacc8c6ff2`，版本 1；历史决定 `human-source-A-a-prediction-c935580f9be3-1` / **REVISE**；用户原话：revise，感觉method有点不适合，这有点像探索一个相关关系
历史人工 source anchor：`d08a4ec1-ec7b-52ab-89c5-481992b2f205`；span `1c08b433-4220-5f1f-bea1-27fcadc5a279`；page 7；字符区间 [0, 885)；bbox `[56.69093322753906, 375.8001403808594, 290.5704040527344, 578.4327392578125]`。

原科学陈述（包含旧标题时原样列出）：

```text
We further extracted the intrinsic complex refractive
index changes—Δn and Δk—of the monolayer WS2 as a
function of electrostatically induced carrier density for the
device with TOS/graphene electrodes (Fig. 4c and Sup-
plementary Information IV).
```

当前科学陈述：

```text
We further extracted the intrinsic complex refractive
index changes—Δn and Δk—of the monolayer WS2 as a
function of electrostatically induced carrier density for the
device with TOS/graphene electrodes (Fig. 4c and Sup-
plementary Information IV).
```

当前 source anchors：

- `ec63f9f7-ed0a-5468-af2a-64c93b62dbd7`；span `8f6570bf-b6d8-5397-a371-ef8e7d3c2166`；page 7；字符区间 [0, 885)；bbox `[56.69093322753906, 375.8001403808594, 290.5704040527344, 578.4327392578125]`。

为什么不计正确：Scientific type changed, so the frozen type+text prediction key no longer matches.
技术分类：`MATERIAL_CONTENT_OR_TYPE_CHANGE`。
证明：原源 hash/page/offset/bbox/整块文字相同=True；去掉实际源中标题后的科学原文相同=True；type 相同=False；layer/epistemic 相同=True。
结论：旧 METHOD 类型曾被用户明确质疑；当前类型按“关系分析”要求修正，科学原文未变。这个 enum 是实质类型变化，不能纳入 E0 或继承原 REVISE 为 ACCEPT。当前未计分属于新 type+text 键尚未判定；不能把旧错误类型的模型 credit 视为应该恢复的真值。现无另一个确定的生产错误，等待 A1 对当前类型归属的真实决定；若 REVISE，按具体意见通用修正后重新检查。
完整 source text/metadata、类型/layer/epistemic、指纹与新旧映射见当前 paper-a.json 的 graph_node_mapping；本报告中的候选正文逐字取自记录，没有补科学文字。

### A-失分3 / A2a：新的工艺片段汇总

当前 key：`6c6cce386755367dcc7aecf9a7fc3a4d9b6070b495ab70f2f9af21565e0130d4`。
当前生产对象：`796f256a-90e7-5843-b1ef-f78416790de6`，类型 `PROCESS`，版本 1，当前 evidence fingerprint `d98c272eab324e059b660897b6cdd6891fffb02101fcde78d52cc145de4a7dec`。
原 PDF：[第 8 页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)；source SHA-256 `30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`。
原冻结生产对象/类型/key/anchor：无同范围对象。历史独立生产评审决定：无。

当前科学陈述：

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

当前 source anchors：

- `ce800448-3107-5a24-94ac-94187a44d833`；span `8afbd8f8-ffda-520e-bdca-fe357ac604c0`；page 8；字符区间 [0, 272)；bbox `[56.692108154296875, 674.1483154296875, 290.5409851074219, 732.2403564453125]`。
- `fe880ee9-81b8-51e4-8030-87dcfd598462`；span `eb04dcff-2dc1-5c33-bd30-ba60cd0ee94c`；page 8；字符区间 [0, 1146)；bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。
- `36f5fa38-19d3-5f4c-a51c-09a43e63d6a0`；span `8002fd82-1f6f-5caa-b8b1-cad43f93dfc0`；page 8；字符区间 [0, 586)；bbox `[304.7234802246094, 351.87469482421875, 538.5851440429688, 481.2027282714844]`。

为什么不计正确：New source-anchored candidate has no entry in immutable prediction adjudication.
技术分类：`NEW_CANDIDATE`。
结论：相对原冻结生产是新对象，没有冻结独立判定；不能因此认定科学 false positive。它是 SEMANTIC/AI_INTERPRETATION 的摘录分组，不是已证实工艺顺序或完整器件方法。
先前 v4 修正中的 PROCESS：`49a9fa05-72a8-54df-b034-b813b6674c5c`，key `1057397f6ea54889262a2087f7f2fca7d2df001ad8c966b344f6bf7ec422c0a4`；当时没有人工决定。其实际科学内容如下，能直接看出混入表征信息：

```text
A SiN layer of 350 nm was deposited on a SiO2 substrate
by low-pressure chemical vapor deposition. The SiN
waveguide and ring resonator were patterned on AR-P
6200 e-beam resist by electron beam lithography (Raith
EPBG 100KV). After developing the resist, the inductively
coupled plasma reactive ion etching (ICP-RIE) was used
to etch the waveguide and resonator, using CHF4 as
etching gas and additional Ar to lower the etch rate and
maintain the chamber pressure. A plasma asher was used
to strip of the remaining resist. The passive sample with
SiN waveguide arrays was then cladded with the 1 µm
PECVD SiO2 and followed by chemical mechanical pol-
ishing (CMP). After the CMP process, a 50 nm to 100 nm
SiO2 cladding with a top surface roughness of <1 nm
remained to minimize potentially induced strain effect
(Supplementary Information IX). Next, the device was
again patterned with positive resist (AZ52143E) and pat-
terned using a direct laser writer (DMO ML 3 Pro) to
deﬁne the metal electrodes. Ti/Au (10 nm/ 40 nm) was
then deposited, followed by liftoff in acetone. Finally, to
remove any remaining residue and increase adhesion to
our 2D HS, the sample was cleaned using oxygen plasma
(FEMTO SCIENCE).
TMDs, graphene, and hBN ﬂakes were mechanically
exfoliated onto SiO2/Si substrates. The thickness of
individual ﬂakes was carefully veriﬁed via optical contrast
using an optical microscope. The HS stack comprising
these exfoliated ﬂakes was fabricated using a dry-transfer
technique facilitated by a polycarbonate (PC) stamp.
Speciﬁcally, ﬂakes were ﬁrst picked up at 120 °C using the
PC polymer and subsequently transferred onto the target
substrate at 200 °C. After transfer, the residual PC poly-
mer was completely removed by immersing the samples
in chloroform for 12 h. For controlled oxidation of as-
exfoliated WSe2 ﬂakes, UV-ozone treatment was per-
formed at 50 °C for 30 min in the UV ozone cleaner
(Samco UV-1), maintaining an oxygen ﬂow rate of
1 L/min, ensuring effective conversion of WSe2 into TOS.
PL and Raman spectra were acquired at room tem-
perature using a commercial Raman spectroscopy system
(Nanobase XperRam-S567). A 532 nm continuous-wave
laser was employed as the excitation source, focused onto
the sample through a 100× objective lens. The resulting
signals were collected by the same objective lens and
analyzed using the built-in spectrometer. The laser power
was carefully controlled to avoid sample damage or
heating effects during measurements. Spatially resolved
PL mapping was performed to characterize the optical
quality and homogeneity of the samples before and after
oxidation.
The sheet resistance of pristine graphene and TOS-
doped graphene samples was characterized using a
source-measure unit (SMU, Keithley 2634B). Electrical
contacts were fabricated onto the samples using standard
lithographic and metal deposition techniques, enabling
precise voltage biasing and current measurement. The
sheet resistance and corresponding charge neutral point
shifts were determined by systematically sweeping the
applied gate voltage while measuring the current-voltage
characteristics, conﬁrming the doping level and electrical
quality of the graphene-based electrodes.
```
旧汇总 anchors：`79244c7a-5df0-5836-8aa7-3377f94e3a48` (p8), `0fe84a3a-fa38-5fc9-ad42-7ee6b85aad36` (p8), `20dd2805-fa74-5f56-9e33-411517eb2fb2` (p8), `8d8e2faa-b83f-51de-b9d5-675e0d2aeafa` (p8)

该 v4 分组确有工程缺陷，已在 v5 通用修复：仅编译明确制备/处理句，保留 PC stamp 跨块续句，排除 PL/Raman、激光功率及片电阻结果的整段正文。当前仍含电接触制备原句，是表征样品制备还是器件主流程的分组边界仍需 A2a 审核，不能预判所有摘录构成一条执行链。
human-source-A-a-fabrication-2 曾 ACCEPT 的是 REVISED_METHOD_VIEW（六源结构/制备综合视图），不是该 PROCESS 或其新独立子步骤的对象评审，不能拿来自动计 credit。当前需要 A2a 的分组/类型/源范围判定；若发现依旧过度分组，应修复生产而不是删除所有有效工艺事实。
完整 source text/metadata、类型/layer/epistemic、指纹与新旧映射见当前 paper-a.json 的 graph_node_mapping；本报告中的候选正文逐字取自记录，没有补科学文字。

### A-失分4 / A3：拾取、转移新候选

当前 key：`8d2324c7008bc8bc0c0742d2e9d60f14096a0a50b7321bbf10f67eaf138f2276`。
当前生产对象：`4431a4f7-9c76-5c5d-a689-0ecd0447246c`，类型 `METHOD`，版本 1，当前 evidence fingerprint `7151983b5835cbb72d275e5401840aec7bec7f94cd0edafbb8953310b79288d9`。
原 PDF：[第 8 页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)；source SHA-256 `30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`。
原冻结生产对象/类型/key/anchor：无同范围对象。历史独立生产评审决定：无。

当前科学陈述：

```text
Speciﬁcally, ﬂakes were ﬁrst picked up at 120 °C using the
PC polymer and subsequently transferred onto the target
substrate at 200 °C.
```

当前 source anchors：

- `fe880ee9-81b8-51e4-8030-87dcfd598462`；span `eb04dcff-2dc1-5c33-bd30-ba60cd0ee94c`；page 8；字符区间 [0, 1146)；bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。

为什么不计正确：New source-anchored candidate has no entry in immutable prediction adjudication.
技术分类：`NEW_CANDIDATE`。
结论：有实际原文和参数的新 METHOD 候选，没有冻结预测键；没有证据证明它是 scientific false positive。旧已接受综合视图包含这些事实，但没有对该独立对象的当前类型/定位作决定。保留有效步骤，等待对应 A3/A4 真实决定；当前未发现必须先做的额外生产修正。
完整 source text/metadata、类型/layer/epistemic、指纹与新旧映射见当前 paper-a.json 的 graph_node_mapping；本报告中的候选正文逐字取自记录，没有补科学文字。

### A-失分5 / A4：聚合物去除新候选

当前 key：`ef6e9b024ba55f3fd3fd815f230bf3b4167a830f39fdb6ada6c9397fab826190`。
当前生产对象：`45fa7f8a-268c-5371-af4d-3184f7ff31d4`，类型 `METHOD`，版本 1，当前 evidence fingerprint `f6896cf62390b1d39b6bdce3acd5c694fa218337cb4275a05dc824a95fa1dd62`。
原 PDF：[第 8 页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)；source SHA-256 `30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`。
原冻结生产对象/类型/key/anchor：无同范围对象。历史独立生产评审决定：无。

当前科学陈述：

```text
After transfer, the residual PC poly-
mer was completely removed by immersing the samples
in chloroform for 12 h.
```

当前 source anchors：

- `fe880ee9-81b8-51e4-8030-87dcfd598462`；span `eb04dcff-2dc1-5c33-bd30-ba60cd0ee94c`；page 8；字符区间 [0, 1146)；bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。

为什么不计正确：New source-anchored candidate has no entry in immutable prediction adjudication.
技术分类：`NEW_CANDIDATE`。
结论：有实际原文和参数的新 METHOD 候选，没有冻结预测键；没有证据证明它是 scientific false positive。旧已接受综合视图包含这些事实，但没有对该独立对象的当前类型/定位作决定。保留有效步骤，等待对应 A3/A4 真实决定；当前未发现必须先做的额外生产修正。
完整 source text/metadata、类型/layer/epistemic、指纹与新旧映射见当前 paper-a.json 的 graph_node_mapping；本报告中的候选正文逐字取自记录，没有补科学文字。

### B-失分1：DFT 方法句，评估键失配

当前 key：`3eed8cbe5e1e2f83287ea33107b6547e145a931bed9a3fa7c28bce3e9bd7a570`。
当前生产对象：`656715f2-1b94-5c6b-abf2-f0dbb5d7c5e3`，类型 `SIMULATION`，版本 1，当前 evidence fingerprint `852ab5c0654d1c209868bf77d2155c47bffdb2f7c4306ae2a84a4fda8c806d01`。
原 PDF：[第 7 页](E:/PaperLearning/backend/data/documents/4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd.pdf)；source SHA-256 `4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd`。
原冻结生产对象：`545d67a7-8abc-5b1e-a1ba-336245e58688`，类型 `SIMULATION`，key `48b848f51191d1e796ddf88bb9d0bdb7d482639b9ef68e5f4b6d79d6d523ca0a`；源 page 7，bbox `[306.1416931152344, 143.06312561035156, 562.7979125976562, 444.776123046875]`。
历史人工对象：`14a5cee5-6df1-547c-893d-e14ad2ca16cd`，版本 1；历史决定 `human-source-B-b-dft-method-1` / **ACCEPT**；用户原话：accept,这里是DFT的使用方法，但这一大节都是方法，所有用到的方法都需要识别出来，并做好总结
历史人工 source anchor：`eabf77bc-88cd-576b-bee5-1bf27aa1459f`；span `51994cf6-7d86-5615-814a-1f8f4660742e`；page 7；字符区间 [0, 1927)；bbox `[306.1416931152344, 143.06312561035156, 562.7979125976562, 444.776123046875]`。

原科学陈述（包含旧标题时原样列出）：

```text
DFT calculations
First-principles DFT calculations were performed by using the Vienna 
Ab initio Simulation Package (VASP 5.4)⁴⁹ with the exchange-correlation 
functional based on Perdew–Burke–Ernzerhof ⁵⁰ generalized gradient 
approximation.
```

当前科学陈述：

```text
First-principles DFT calculations were performed by using the Vienna 
Ab initio Simulation Package (VASP 5.4)⁴⁹ with the exchange-correlation 
functional based on Perdew–Burke–Ernzerhof ⁵⁰ generalized gradient 
approximation.
```

当前 source anchors：

- `736e109e-128f-5e26-85e7-e9ad261d9b6b`；span `29cc6dd3-34f8-5f5c-99ca-095692f2f046`；page 7；字符区间 [0, 1927)；bbox `[306.1416931152344, 143.06312561035156, 562.7979125976562, 444.776123046875]`。

为什么不计正确：Literal source heading removal changed the SHA-256 prediction key; same scientific statement/type.
技术分类：`NONMATERIAL_METADATA_CHANGE`。
证明：原源 hash/page/offset/bbox/整块文字相同=True；去掉实际源中标题后的科学原文相同=True；type 相同=True；layer/epistemic 相同=True。
结论：评估文本键失配兼 metadata-only change；不是已证实的新 false positive、错误科学类型或科学内容损失。工程上不应把标题塞回科学陈述去追旧键；评估层需要 E0 的可审计有限绑定。无需重新审核同一问题句/DFT 科学内容，历史 ACCEPT 的范围不扩展。
完整 source text/metadata、类型/layer/epistemic、指纹与新旧映射见当前 paper-b.json 的 graph_node_mapping；本报告中的候选正文逐字取自记录，没有补科学文字。

### A 已移除旧 credit：背景 LIMITATION / a-limitation

原冻结对象 `e184052a-9495-5042-9677-d7ba6eeace2c` / `LIMITATION`；历史人工对象 `b586000f-5407-5601-bbd0-d98b711da1c2`，历史决定 `human-source-A-a-limitation-2` / **REJECT**。
原冻结 source page 2，bbox `[56.691619873046875, 88.87735748291016, 290.5670471191406, 469.241943359375]`；历史人工 anchor `312679c2-a720-5da3-a5b1-5311e5cc392d`，span `c2d3924b-09dc-58c8-ba2b-d24a80225207`，page 2，offset [0, 1740)，bbox `[56.691619873046875, 88.87735748291016, 290.5670471191406, 469.241943359375]`。

```text
Although
ionic liquid gating is capable of injecting signiﬁcantly high
charge densities without introducing absorption losses, it
suffers from nonlocal charge dispersion, limited chemical
stability, and incompatibility with scalable CMOS fabri-
cation processes²⁸–³⁰.
```
当前独立科学对象：无（REMOVED_CANDIDATE）；原文完整 source span 仍保留。此项是用户已决定“不要作为本论文独立研究对象”的背景。旧 MODEL_SOURCE_REVIEW 给它 credit 不能覆盖历史人类 REJECT。移除该错误独立对象不是移除有效事实，背景资料未删除。冻结 gold a-limitation 仍在，recall 仍 16/17=94.12%，高于80%阈值。无需再问用户，也不改 gold。

当前保留的 source span `3c67003d-98df-58ed-a97a-fb3d692a78c2`；page 2；bbox `[56.691619873046875, 88.87735748291016, 290.5670471191406, 469.241943359375]`；其原文字节与上述历史 source anchor 的 text 完全相同。

## 3. 与 precision 键失分不同的待审核项

A2b（旧氧化 METHOD）、B1（第三位1上划线）、B2（on/th 下标）仍拥有冻结模型表中的旧 key，所以模型比较给它们 credit；但旧人类决定为 REVISE，当前结果尚未 ACCEPT。这证明高模型 precision 本身不足以通过人工源验收。A 的两条 explanation-only REVISE 保留原决定与真实澄清，不制造 ACCEPT、不误计为科学提取错误。

Equation 1 原始块/页码/范围/bbox 不变；当前 display metadata 有两条“Unresolved short mathematical rule”提示，没有宣称自动根号/分式重构。冻结 gold 同时保留原始三个 text fragments 和一个 MODEL_SOURCE_REVIEW 的视觉转写；历史 human-source-B-b-equation-1-1 是 SOURCE_ATTRIBUTION / ACCEPT。两种范围不可混同：局部化及可视原图归属的旧 ACCEPT 可以在 E0 中有限映射，不能自动认证当前新符号显示或自动 algebra/LaTeX。

协议既要求 equation localization 100%，也禁止未解决的 gold 数值/字形歧义。当前 localization=1/1 是工程测量，不能凭此声称精确数学转写已核验。最终评估必须检查当前原图证据与此前接受的 Equation 1 是同一份源，保留重构 unknown；若未知影响选定 gold 的符号/数值/意义，则仍 FAIL，必须解决该具体源忠实度问题，不能让 E0/其他 ACCEPT 抵消。不能仅因为整块新 metadata 报告了一条未归属解释警告，就凭空撤销旧的定位接受或制造新的公式含义。

## 4. 人工评审完成后是否能够 PASS

结论：完成真实的 E0 和局部评审，配合当前评估层绑定/判定计算，有可能让 reviewed Gate A PASS；它不会改变冻结模型比较 16/21、17/18。仅给报告换 PASS 标签或继续用旧 key 表计分都不够。当前六个无旧键候选中，未发现仍需先修复的确定性源文字缺陷；v4 PROCESS 的通用工程分组缺陷已经修正。后续是否还有生产修改，取决于 A1/A2a 等对当前类型/分组的具体审核，以及选定源字形检查。

| 条件 | A | B |
| --- | --- | --- |
| 固定当前 precision 分母 | 21 | 18 |
| ≥90% 所需正确对象数 | 至少19/21=90.48% | 至少17/18=94.44% |
| E0 限定映射后可承接的旧 ACCEPT | 14 | 16 |
| A 两项 explanation-only resolution | 原真实澄清支持正确原文/类型判定，保留REVISE标签；不是补造ACCEPT | 不适用 |
| 局部待决定 | A1、A2a、A2b、A3、A4 共5个窗口对象 | B1、B2共2个窗口对象 |
| 若所有局部判定正确且绑定/其他条件都有效 | 条件性21/21（非已获得分数） | 条件性18/18（非已获得分数） |

A 在上述两项解释性澄清原范围仍有效的条件下有16个可判定正确对象，其余5个至少3个正确才满足 precision；该算术不是劝用户 ACCEPT。若错误类型/重复分组/源忠实度问题被确认，按真实决定计算并修复；每次改输出后重新核验源/版本/指纹。B 即便只一项新增确认便在算术上达到17/18，也不能忽略另一项符号源忠实度修订；anchor/page/caption/quantity 要求100%，零容忍及所有独立条件仍需满足。

评估层仍需具体工作：E0批准后写独立等价记录（旧/新ID、版本、源hash、证据指纹、原决定引用、范围及批准原话），保留历史账本；逐项收集真实A1…B2决定后创建当前SOURCE_ATTRIBUTION审计，计算当前人类判定的precision及源检查。旧frozen model-key表/阈值/gold不改，新的真实判定不冒充MODEL_SOURCE_REVIEW。最后按不变定义复算并核查生产稳定性、provenance、selected quantities、graph integrity与相应浏览器结果。任何尚未解除的源字形歧义、错误类型或不足19/21、17/18，都给出精确FAIL原因。

所以这不是“只需要全部点 ACCEPT”，也不是“现有低模型分数证明必须继续重写生产”。必需的是有限审计绑定、真实局部决定及受原协议约束的最终计算/源核查；没有证据时不再做广泛架构修改。Gate B持续NOT_STARTED。

## 5. E0 如何证明35项是元数据变化

| 论文 | 等价窗口项 | 其中原ACCEPT | 其中原REVISE |
| --- | --- | --- | --- |
| A | 17 | 14 | 3（两项说明性澄清已解决，一项A2b仍待当前决定） |
| B | 18 | 16 | 2（B1、B2仍待当前修订决定） |
| 合计 | 35 | 30 | 5 |

1. 对照原始PDF SHA-256，重查不可变human ledger与decision history，以及77条实际历史node/anchor快照。
2. 每项按同源、同页、唯一的原文身份找映射；不做语义相似/fuzzy合并。原整块source.text、offset、bbox逐项相同，完整新旧源在paper-a/b.json。
3. 比较同type、layer、epistemic status；科学文字只允许折叠空白，并去掉当前源metadata中实际存在的literal leading heading。A Abstract、B DFT calculations两例逐字移除，其他符号不改。
4. 全部科学字符相同，故数值、单位、符号及条件限定没有被归一化删除；source notation是独立显示元数据。新显示的科学含义修订、未解决REVISE及公式重构不在此等价批准范围。
5. 记录旧canonical ID/版本/实际指纹，当前 ID/版本/实际应用evidence fingerprint及完整metadata差异。新UUID、source anchor IDs、创建器版本等不视为科学新事实。
6. 不符合以上条件的A1类型变化、三个新A对象均排除E0；可能多匹配时拒绝猜测。21条数量与9个解析异常实例的旁证映射保留历史范围，并不制造其新ACCEPT。

E0技术建议：接受上述有限的可审计映射方式，承接原决定及范围、保留5个REVISE和其真实澄清，单独等待实质项。E0不是35个新的ACCEPT，更不是SCIENTIFIC_VALIDITY或VERIFIED；没有审批时仍只是提案。

本轮只呈现E0，等待用户明确ACCEPT / REVISE / REJECT；收到后再呈现A1，后续依次A2a、A2b、A3、A4、B1、B2，不同时请求全部决定。

## 6. 证据入口及完整性

- [冻结协议](PAPER-GRAPH-EVIDENCE-GATE.md)
- [当前候选完整映射A](../../evals/reports/dual-paper/reconciliation-20261011-r4/paper-a.json)
- [当前候选完整映射B](../../evals/reports/dual-paper/reconciliation-20261011-r4/paper-b.json)
- [35项有限等价清单](../../evals/reports/dual-paper/reconciliation-20261011-r4/EQUIVALENCE-PROPOSAL.md)
- [当前局部评审范围](../../evals/reports/dual-paper/reconciliation-20261011-r4/TARGETED-REVIEW.md)
- [不可变历史人类账本](../../evals/reviews/dual-paper/HUMAN_SOURCE_REVIEW.json)
- [当前artifact/implementation hash清单](../../evals/reports/dual-paper/reconciliation-20261011-r4/manifest.json)

当前manifest SHA-256：`67cbb9b9672921b8483bf6244600944dbf46982afcacab73fdabc2e439deadc1`。历史ledger SHA-256：`4c9220d03943ddc25583270fd2c08a1f20aa0853c518860db7cef9c31f7e9d99`。历史decision-history digest：`daeff02aa4d6b27445e57b87f7963f1d075884e7e86b5b2f4d0426bd860df99e`。

当前已记录39后端/7对账/8前端测试及真实public PDF、两篇原PDF浏览器旅程PASS；本次仅生成诊断文档和读核输入，未重新运行应用、不冒充新测试或新评审记录。未commit/push。
