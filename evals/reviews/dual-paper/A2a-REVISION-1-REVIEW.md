# A2a 修订1：制作与表征分组（待审核）

用户原话：`revise，进行分组边界，表征和制作进行分组`。旧对象 v1 的 REVISE 已保存。本次修订仍是草稿，三个组都未被 ACCEPT。

所有对象均为 PROCESS / SEMANTIC / AI_INTERPRETATION / CANDIDATE；均来自原始 PDF 第8页。单句 METHOD 候选及原始源块未改写。以下分组不推导统一顺序，也不声称完整执行配方。

## 制作与材料处理

ID `796f256a-90e7-5843-b1ef-f78416790de6`，version 2，fingerprint `e6551866a0b4a4b8def2ac816fae6fa7e9f1a9c9556b887e28513773ed693e25`。

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
```

Source anchor `ce800448-3107-5a24-94ac-94187a44d833`，page 8，字符 [0, 272)，bbox `[56.692108154296875, 674.1483154296875, 290.5409851074219, 732.2403564453125]`。源块证据精度仍为 TEXT_BLOCK。

Source anchor `fe880ee9-81b8-51e4-8030-87dcfd598462`，page 8，字符 [0, 1146)，bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。源块证据精度仍为 TEXT_BLOCK。

## 光学表征

ID `ab543609-3081-585f-80ce-82b0b5ab9398`，version 1，fingerprint `e25cb361da8b26a32aa9d1a79992928986f93ef9b274089125f4735a582a9a25`。

```text
The thickness of
individual ﬂakes was carefully veriﬁed via optical contrast
using an optical microscope.
PL and Raman spectra were acquired at room tem-
perature using a commercial Raman spectroscopy system
(Nanobase XperRam-S567).
A 532 nm continuous-wave
laser was employed as the excitation source, focused onto
the sample through a 100× objective lens.
The resulting
signals were collected by the same objective lens and
analyzed using the built-in spectrometer.
The laser power
was carefully controlled to avoid sample damage or
heating effects during measurements.
Spatially resolved
PL mapping was performed to characterize the optical
quality and homogeneity of the samples before and after
oxidation.
```

Source anchor `ce800448-3107-5a24-94ac-94187a44d833`，page 8，字符 [0, 272)，bbox `[56.692108154296875, 674.1483154296875, 290.5409851074219, 732.2403564453125]`。源块证据精度仍为 TEXT_BLOCK。

Source anchor `fe880ee9-81b8-51e4-8030-87dcfd598462`，page 8，字符 [0, 1146)，bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。源块证据精度仍为 TEXT_BLOCK。

## 电学表征及其测试样品制备

ID `6d241e34-de8f-5105-803a-b19e1ac284aa`，version 1，fingerprint `1b134ec8d1219e32bc9a2529cce04a96016ee53b8590204cb40c269516d3865b`。

```text
The sheet resistance of pristine graphene and TOS-
doped graphene samples was characterized using a
source-measure unit (SMU, Keithley 2634B).
Electrical
contacts were fabricated onto the samples using standard
lithographic and metal deposition techniques, enabling
precise voltage biasing and current measurement.
The
sheet resistance and corresponding charge neutral point
shifts were determined by systematically sweeping the
applied gate voltage while measuring the current-voltage
characteristics, conﬁrming the doping level and electrical
quality of the graphene-based electrodes.
```

Source anchor `36f5fa38-19d3-5f4c-a51c-09a43e63d6a0`，page 8，字符 [0, 586)，bbox `[304.7234802246094, 351.87469482421875, 538.5851440429688, 481.2027282714844]`。源块证据精度仍为 TEXT_BLOCK。

[原始PDF 第8页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)

![机械剥离和干法转移](E:/PaperLearning/.runtime/gate-a-reconciliation-20261011/review-a2a/exfoliation-context.png)

![转移、去残留、氧化与光学表征](E:/PaperLearning/.runtime/gate-a-reconciliation-20261011/review-a2a/transfer-oxidation-context.png)

![片电阻表征和电接触制备](E:/PaperLearning/.runtime/gate-a-reconciliation-20261011/review-a2a/electrical-contact-context.png)

修订差异：制作组保留剥离、PC转移、氯仿去残留和氧化；移出的电接触原句保留在明确用于片电阻表征的组中；厚度光学核对、PL/Raman及PL mapping单列光学表征组。制作组旧ID保留并升至v2，另两个组是新候选；新对象没有旧 ACCEPT。

技术建议：ACCEPT 本次三个组的来源归属与分组边界。需要用户判断制作/表征是否已分清、测量样品限定是否准确、原始条件/数值/单位是否忠实。本建议不是人工决定。请回复 A2a ACCEPT / REVISE / REJECT；不包含其他制作/表征候选或科学有效性。

40项后端测试、8项前端测试、Ruff/mypy及公开PDF/两篇原始PDF浏览器旅程通过（包括PROCESS每个证据锚点跳转、反向选择和刷新）。原冻结模型比较报告保留；本次新模型键比较A16/22、B17/18，当前人工指标未计算，Gate A仍FAIL、Gate B未开始。
