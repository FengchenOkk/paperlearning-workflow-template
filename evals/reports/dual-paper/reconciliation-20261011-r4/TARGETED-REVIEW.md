# 仅待确认的局部项目

先确认 E0 等价性绑定提案，不重新评审 35 项等价候选或 21 项数量。E0 不是新的科学 ACCEPT：原历史决定、范围和未解决 REVISE 原样保留。
以下六张卡涉及七个当前对象；A2 把同一源中的工艺汇总和旧氧化子步骤合并呈现，两者决定分别记录。可回复 E0 同意/不同意；A1、A2a、A2b、A3、A4、B1、B2 各 ACCEPT / REVISE / REJECT，并说明需要改动的内容。
所有决定目前为 null；本文件没有替用户作决定。

## A1：关系分析类型

原文不变；METHOD → RELATIONSHIP_ANALYSIS。旧 REVISE 要求‘关系分析’，未对新的 enum 对象作 ACCEPT。请决定该句作为 SEMANTIC/AUTHOR_CLAIM 的关系探索归属是否合适；它不陈述具体关系结果。

旧对象：bed7a52b-9932-559a-b389-e7cacc8c6ff2；旧决定：human-source-A-a-prediction-c935580f9be3-1 / REVISE。
当前对象：`1f8ffa09-f97d-531f-af7c-174c229cc6c2`；类型 `RELATIONSHIP_ANALYSIS`；版本 1；pipeline `source-graph-v5`。
源 SHA-256：`30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`；当前 evidence fingerprint：`0f232489156f560555b4487df78216b5b89fca14ff8877d24390fd424cbb2067`。
原始 PDF：[第 7 页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)；bbox `[56.69093322753906, 375.8001403808594, 290.5704040527344, 578.4327392578125]`。

当前原文：

```text
We further extracted the intrinsic complex refractive
index changes—Δn and Δk—of the monolayer WS2 as a
function of electrostatically induced carrier density for the
device with TOS/graphene electrodes (Fig. 4c and Sup-
plementary Information IV).
```

历史原文：

```text
We further extracted the intrinsic complex refractive
index changes—Δn and Δk—of the monolayer WS2 as a
function of electrostatically induced carrier density for the
device with TOS/graphene electrodes (Fig. 4c and Sup-
plementary Information IV).
```

源 anchors：ec63f9f7-ed0a-5468-af2a-64c93b62dbd7

## A2a：二维材料工艺片段汇总

这是新的 AI_INTERPRETATION PROCESS：只汇集原文中的剥离、干法转移、拾取/转移、残留聚合物去除、氧化和电接触制备；排除了光谱等表征正文，补回跨块的 PC stamp 句尾。它不是推导工艺、完整执行配方或器件结构综合稿。请对该分组和证据范围作决定。历史 human-source-A-a-fabrication-2 的 ACCEPT 对象是六源的 REVISED_METHOD_VIEW，不能扩展成对这个生产对象的 ACCEPT。

旧对象：无同范围的已接受生产对象；旧决定：无 / 无。
当前对象：`796f256a-90e7-5843-b1ef-f78416790de6`；类型 `PROCESS`；版本 1；pipeline `source-graph-v5`。
源 SHA-256：`30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`；当前 evidence fingerprint：`d98c272eab324e059b660897b6cdd6891fffb02101fcde78d52cc145de4a7dec`。
原始 PDF：[第 8 页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)；bbox `[56.692108154296875, 674.1483154296875, 290.5409851074219, 732.2403564453125]`。

当前原文：

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

源 anchors：ce800448-3107-5a24-94ac-94187a44d833, fe880ee9-81b8-51e4-8030-87dcfd598462, 36f5fa38-19d3-5f4c-a51c-09a43e63d6a0

### A2b：同卡的旧氧化子步骤

原氧化 METHOD 原文没变，旧生产决定仍为 REVISE（当时要求完整器件结构/制备覆盖）。当前引用它作为一个材料处理子步骤，完整结构综合稿仍是历史已接受视图。请明确对子步骤归属作决定；不要把 A2a 的 PROCESS 当成覆盖全部结构的那个综合稿。SiN 工艺编译和 DEVICE/图1结构候选可在 paper-a.json 的 graph_node_mapping 找到，属于同一源但不扩展冻结窗口。

旧对象：5089ade4-6914-566d-b785-ffb8ff1fa255；旧决定：human-source-A-a-fabrication-1 / REVISE。
当前对象：`ca8eacbf-78a0-52be-bdeb-1da5b078a992`；类型 `METHOD`；版本 1；pipeline `source-graph-v5`。
源 SHA-256：`30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`；当前 evidence fingerprint：`5bccb35ed640dec575650e40bf1fffd3c63f7561d3a9285da24f98afff670437`。
原始 PDF：[第 8 页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)；bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。

当前原文：

```text
For controlled oxidation of as-
exfoliated WSe2 ﬂakes, UV-ozone treatment was per-
formed at 50 °C for 30 min in the UV ozone cleaner
(Samco UV-1), maintaining an oxygen ﬂow rate of
1 L/min, ensuring effective conversion of WSe2 into TOS.
```

历史原文：

```text
For controlled oxidation of as-
exfoliated WSe2 ﬂakes, UV-ozone treatment was per-
formed at 50 °C for 30 min in the UV ozone cleaner
(Samco UV-1), maintaining an oxygen ﬂow rate of
1 L/min, ensuring effective conversion of WSe2 into TOS.
```

源 anchors：fe880ee9-81b8-51e4-8030-87dcfd598462

## A3：拾取与转移 METHOD

新生产对象；原文明确 120 °C 拾取、200 °C 转移。已接受扩展视图包含这些事实，但不是对这个独立 METHOD 的类型/当前定位判定，故不自动继承。请决定该原文步骤作为 METHOD 是否合适。

旧对象：无同范围的已接受生产对象；旧决定：无 / 无。
当前对象：`4431a4f7-9c76-5c5d-a689-0ecd0447246c`；类型 `METHOD`；版本 1；pipeline `source-graph-v5`。
源 SHA-256：`30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`；当前 evidence fingerprint：`7151983b5835cbb72d275e5401840aec7bec7f94cd0edafbb8953310b79288d9`。
原始 PDF：[第 8 页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)；bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。

当前原文：

```text
Speciﬁcally, ﬂakes were ﬁrst picked up at 120 °C using the
PC polymer and subsequently transferred onto the target
substrate at 200 °C.
```

源 anchors：fe880ee9-81b8-51e4-8030-87dcfd598462

## A4：聚合物去除 METHOD

新生产对象；原文明确氯仿浸泡 12 h 去除残余 PC。保留 poly- / mer 跨行原文，没有补实验条件。旧扩展视图的 ACCEPT 不自动作用于此独立对象。请决定该原文步骤作为 METHOD 是否合适。

旧对象：无同范围的已接受生产对象；旧决定：无 / 无。
当前对象：`45fa7f8a-268c-5371-af4d-3184f7ff31d4`；类型 `METHOD`；版本 1；pipeline `source-graph-v5`。
源 SHA-256：`30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e`；当前 evidence fingerprint：`f6896cf62390b1d39b6bdce3acd5c694fa218337cb4275a05dc824a95fa1dd62`。
原始 PDF：[第 8 页](E:/PaperLearning/backend/data/documents/30afba934882b658b4ca20f1fecd116bc40f9c5f4c083c837c4d188ff4805a9e.pdf)；bbox `[304.7235107421875, 88.87528228759766, 538.593017578125, 349.67596435546875]`。

当前原文：

```text
After transfer, the residual PC poly-
mer was completely removed by immersing the samples
in chloroform for 12 h.
```

源 anchors：fe880ee9-81b8-51e4-8030-87dcfd598462

## B1：第三位 1 的上划线修订

原 raw text (0112) 保留；独立 PDF notation 视图显示 (01 1̅ 2)，ASCII Sb(0 1 -1 2)。原图及浏览器确认上划线在第三个数字 1，末位 2 没有上划线。旧决定是 REVISE 而非修订结果的 ACCEPT。请仅确认这项显示/源忠实度修订。

旧对象：9b030c80-1944-527e-bada-05c7f41bb8ea；旧决定：human-source-B-b-contact-method-1 / REVISE。
当前对象：`5ca9a9b2-fc14-5c6e-997d-80a0bdef2605`；类型 `METHOD`；版本 1；pipeline `source-graph-v5`。
源 SHA-256：`4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd`；当前 evidence fingerprint：`6bede47676de4e95302dcb5d577f4b13e372b5af21d553122e09a54fa617725a`。
原始 PDF：[第 1 页](E:/PaperLearning/backend/data/documents/4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd.pdf)；bbox `[217.32009887695312, 218.87550354003906, 560.9495239257812, 502.9736328125]`。

当前原文：

```text
Here we push the electrical contact of monolayer molybdenum 
disulfide close to the quantum limit by hybridization of energy bands with semi- 
metallic antimony (0112) through strong van der Waals interactions.
```

历史原文：

```text
Here we push the electrical contact of monolayer molybdenum 
disulfide close to the quantum limit by hybridization of energy bands with semi- 
metallic antimony (0112) through strong van der Waals interactions.
```

源 anchors：c929285d-5f90-5779-9c0f-03a90e777cbf

## B2：on/th 下标修订

原 raw text Ion/Vth 保留；独立视图显示 I_on、V_th，24 h、SS 与无明显衰退的限定不变。I_on 是用户明确要求，V_th 曾为模型检查；两者本次再次核对原图。旧 REVISE 没有接受当前显示修订，请仅确认该修订。

旧对象：5b7945d5-d837-50a3-aef4-52e64e07adc7；旧决定：human-source-B-b-stability-1 / REVISE。
当前对象：`8c008d5d-6389-503d-8c92-ea46a92fdae2`；类型 `RESULT`；版本 1；pipeline `source-graph-v5`。
源 SHA-256：`4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd`；当前 evidence fingerprint：`23b6c679139ef48e4db933538c2dcd046091ef96362426de936ae06ab3214518`。
原始 PDF：[第 5 页](E:/PaperLearning/backend/data/documents/4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd.pdf)；bbox `[39.68510055541992, 552.8456420898438, 296.334228515625, 681.276123046875]`。

当前原文：

```text
No obvious degradation of Ion, threshold voltage 
(Vth) and subthreshold swing (SS) was observed during 24 h for the Sb 
contact.
```

历史原文：

```text
No obvious degradation of Ion, threshold voltage 
(Vth) and subthreshold swing (SS) was observed during 24 h for the Sb 
contact.
```

源 anchors：c17caaf5-78ce-5864-9b13-c28318acf332

原图参考：

![B 原文上划线](E:/PaperLearning/.runtime/gate-a-corrections-20261011/paper-b-block-1.png)

![B 原文下标](E:/PaperLearning/.runtime/gate-a-corrections-20261011/paper-b-block-5.png)

这些是原 PDF 的本地渲染，非生成科学图片。Equation 1 没有新的公式决定请求：原定位映射归 E0，未支持的数学重构继续 unknown。
