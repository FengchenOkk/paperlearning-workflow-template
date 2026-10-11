# 论文 B：Methods 全节方法与步骤总结

论文：Li 等（2023），Approaching the quantum limit in two-dimensional semiconductor contacts。
范围：所提供 PDF 第 7 页，从 Methods 到 Data availability 之前；5 个方法小节、30 项方法与操作步骤。

状态：本清单为 MODEL_SOURCE_REVIEW 产生的候选总结，新增项尚未逐项人工验收；不是科学有效性评审。
来源：E:\PaperLearning\backend\data\documents\4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd.pdf
SHA-256：4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd。

## 连贯总结

论文先在蓝宝石上获得单层 MoS₂，并用 PMMA/热释放胶带转移；WSe₂ 则在 SiN_x/Si 上通过逆流、顺流切换的 CVD 生长。MoS₂ 器件在 HfO₂/高掺杂 Si 上采用光刻、O₂ 刻蚀、聚合物清除和 Sb/Au 蒸发剥离完成制备；WSe₂ 器件省去转移。电学测试分为参数分析仪测量和同步栅漏脉冲测量。
材料与界面通过 XRD、AFM、拉曼、光致发光、XPS、FIB 制样和 HAADF-STEM 表征。理论部分使用 VASP/PBE、PAW 势与 DFT-D3，构建半金属/TMD 接触模型，控制失配、真空层、结构收敛与 k 空间采样，并加入偶极修正；最后计算垂直静电势、实空间能带及 LDDOS。

## 方法与步骤清单

下表每一项均有机器清单中的原文引句、anchor、PDF 页码、bbox 与字符范围。所有来源均在 PDF 第 7 页。

### 生长与转移

| ID | 方法／步骤 | 原文支持的总结 | 当前图谱覆盖 |
| --- | --- | --- | --- |
| paper-b-methods-step-01 | MoS₂ 单晶单层 CVD 生长 | 在 C/A 蓝宝石 (0001) 衬底上生长单层 MoS₂；偏切角 0.2°–1°，衬底预退火 1,000 °C、4 h。详细生长工艺引用前作 31，本节未完整展开。 | 未单独识别 |
| paper-b-methods-step-02 | PMMA/TRT 辅助 MoS₂ 转移 | PMMA（Allresist A4, 950K）2,000 rpm 旋涂，150 °C 烘烤去溶剂；贴 TRT，在去离子水中剥离，转移后 120 °C 烘烤释放 TRT。 | 未单独识别 |

### WSe₂ 生长

| ID | 方法／步骤 | 原文支持的总结 | 当前图谱覆盖 |
| --- | --- | --- | --- |
| paper-b-methods-step-03 | 逆流/顺流 CVD 生长 WSe₂ | 在 100 nm SiN_x/Si 上用逆流管式炉生长；WSe₂ 粉末纯度 99.98%，1,180 °C、常压，逆流氩气 80 sccm；到温后改顺流，生长 4 min，再自然冷却。顺流流量的时间单位在原文中不完整。 | 未单独识别 |

### 器件制备与测量

| ID | 方法／步骤 | 原文支持的总结 | 当前图谱覆盖 |
| --- | --- | --- | --- |
| paper-b-methods-step-04 | MoS₂ 向器件衬底转移 | 采用 PMMA 辅助转移，将单层 MoS₂ 放到 HfO₂/高掺杂 Si 衬底。 | 未单独识别 |
| paper-b-methods-step-05 | 沟道隔离 | 用电子束光刻和 O₂ 干法刻蚀进行沟道隔离。 | 未单独识别 |
| paper-b-methods-step-06 | 去除 PMMA | 使用丙酮与 N-甲基-2-吡咯烷酮（NMP）去除 PMMA。 | 未单独识别 |
| paper-b-methods-step-07 | 源漏接触图形定义 | 用电子束光刻定义源极和漏极接触。 | 未单独识别 |
| paper-b-methods-step-08 | Sb/Au 电子束蒸发及剥离 | 电子束蒸发 20 nm Sb / 30 nm Au，随后 lift-off；作者明确说明 Sb (011̅2) 接触在器件制备后无需热退火。 | 未单独识别 |
| paper-b-methods-step-09 | 蒸发时衬底温度控制与测量 | 通过红外加热及调整冷却水流量控制温度，用表面温度指示条测温；本段未给出具体沉积温度值。 | 未单独识别 |
| paper-b-methods-step-10 | WSe₂ FET 制备分支 | WSe₂ FET 在原位 SiN_x/Si 衬底上采用同类制备方法，无需转移过程。 | 未单独识别 |
| paper-b-methods-step-11 | 电学参数测量 | 用 Keithley 4200 半导体参数分析仪，在闭循环低温探针台中测量；基础压力约 10⁻⁶ torr。 | 未单独识别 |
| paper-b-methods-step-12 | 同步栅漏脉冲测量 | 使用 Keithley 4200 脉冲测量单元和 4225-RPM 远程放大器；栅漏同步施加脉冲，最短脉宽可达 160 ns；占空比相关原话为“10 times”，含义需澄清。 | 未单独识别 |
| paper-b-methods-step-13 | 脉冲测量寄生效应控制 | 尽量缩短所有电缆，以减少脉冲测量中的寄生效应。 | 未单独识别 |

### 材料表征

| ID | 方法／步骤 | 原文支持的总结 | 当前图谱覆盖 |
| --- | --- | --- | --- |
| paper-b-methods-step-14 | XRD | 使用 Bruker D8 Discover 系统进行 X 射线衍射。 | 未单独识别 |
| paper-b-methods-step-15 | AFM | 使用 Asylum Cypher S 系统进行原子力显微镜表征。 | 未单独识别 |
| paper-b-methods-step-16 | 拉曼光谱 | 使用自建光谱系统、488 nm 激光及 Princeton Instruments SP-2500 光谱仪。 | 未单独识别 |
| paper-b-methods-step-17 | 光致发光光谱 | 与拉曼共用文中所述自建系统、488 nm 激发及 SP-2500 光谱仪。 | 未单独识别 |
| paper-b-methods-step-18 | XPS 及能量标定 | 使用 PHI 5000 VersaProbe、单色 Al Kα 激发；以外来碳的 C–C 化学态 284.8 eV 标定。 | 未单独识别 |
| paper-b-methods-step-19 | FIB 截面 TEM 样品制备 | FEI Helios 600i 双束 FIB；先原位沉积钨保护层，以 30 kV、21 nA 镓离子束刻蚀形成薄片，剥离后转移至 TEM 半网格。 | 未单独识别 |
| paper-b-methods-step-20 | HAADF-STEM | 使用 FEI Titan G2 60–300 像差校正 S/TEM，工作加速电压 300 kV。 | 未单独识别 |

### DFT 计算

| ID | 方法／步骤 | 原文支持的总结 | 当前图谱覆盖 |
| --- | --- | --- | --- |
| paper-b-methods-step-21 | VASP/PBE-GGA 第一性原理计算 | 使用 VASP 5.4；采用基于 Perdew–Burke–Ernzerhof 广义梯度近似的交换关联泛函。 | 已有候选 |
| paper-b-methods-step-22 | PAW 势 | 使用投影缀加波势描述价电子与离子芯相互作用。 | 未单独识别 |
| paper-b-methods-step-23 | DFT-D3 范德华修正 | 采用 Grimme 的 DFT-D3 方案计入范德华相互作用。 | 未单独识别 |
| paper-b-methods-step-24 | 接触 slab 模型 | 用单层 TMD 与三层半金属 Sb 或 Bi 堆叠；考察 (0001)/(011̅2) 晶面。 | 未单独识别 |
| paper-b-methods-step-25 | 超胞匹配与真空层 | 控制半金属/TMD 超胞晶格失配小于 3%；沿 c 方向设置大于 15 Å 的真空层。 | 未单独识别 |
| paper-b-methods-step-26 | 结构松弛与数值设置 | 所有结构充分松弛，最大力小于 0.02 eV·Å⁻¹，能量收敛标准 10⁻⁴ eV，截断能 400 eV；结构松弛 k-spacing 小于 0.04 Å⁻¹。原文还列出 Sb/Bi 两晶面及 MoS₂、MoSe₂、WS₂、WSe₂ 接触模型。 | 部分识别 |
| paper-b-methods-step-27 | 静态电子结构及布里渊区积分 | 静态计算采用小于 0.01 Å⁻¹ 的 k-spacing 进行布里渊区积分采样。 | 未单独识别 |
| paper-b-methods-step-28 | 偶极修正 | 所有 DFT 计算均考虑超胞 c 轴方向的偶极修正。 | 未单独识别 |
| paper-b-methods-step-29 | Poisson 方程求静电势分布 | 用 Poisson 方程计算 Sb (011̅2)–MoS₂ 与 Sb (0001)–MoS₂ 接触的垂直静电势剖面。 | 未单独识别 |
| paper-b-methods-step-30 | 实空间能带与 LDDOS 模拟 | 对单层 MoS₂、两端 Sb (011̅2) 电极器件，用 DFT 模拟未掺杂零偏压及电子掺杂（类似高栅偏压）条件下的实空间能带和 LDDOS。 | 未单独识别 |

## 当前识别缺口

当前应用在 Methods 页仅有 2 个 METHOD/SIMULATION 候选：VASP/PBE 概述，以及力阈值、能量收敛、截断能设置。前者对应上表 21；后者仅部分覆盖上表 26。其余 28 项虽有原文 source anchors，目前没有对应的独立方法候选。
因此，冻结抽样中方法条目通过，不等于 Methods 全节已经完整识别。后续通用识别需保留“小节—方法—步骤／参数”组织关系、跨栏续文、符号排版和原文条件；本清单没有把步骤先后或文本共现写成科学依赖。

## 必须保留的不确定性

- MoS₂ CVD 的详细生长配方本节引用前作 31；1,000 °C、4 h 是衬底预退火条件。
- WSe₂ 顺流氩气的“80 standard cubic centimetres”缺少明确时间单位，不能悄悄补成 sccm。
- “voltage duty cycle was 10 times”含义不清，不能擅自改成 10%。
- 截面制样从左栏末尾延续到右栏顶部；不得只保留半句。
- 晶面指数 (011̅2) 的第三位 1 有横线；所有下标、指数和严格不等号均以原 PDF 为准。
- 当前 Methods 全节总结之外，正文、扩展数据和独立补充材料的方法覆盖不能据此宣称完整。

## 原文定位

| 来源别名 | Anchor | 第 7 页位置 |
| --- | --- | --- |
| mos2 | 0f74e956-9c09-5dc2-b278-5dc94148bb30 | [39.69, 67.81, 296.28, 197.53] |
| wse2 | 012279a8-2df2-5ee2-b591-67a909dbc67f | [39.69, 207.56, 296.4, 348.03] |
| fabrication | ef7744e8-eade-5132-8c9b-19a63aff1217 | [39.69, 358.06, 296.41, 520.03] |
| electrical | a091d6cc-c138-5390-80c1-075ba22ca5c2 | [39.69, 520.6, 296.39, 638.28] |
| characterization | 98dd9a2e-3987-5508-ac41-da96d1b17535 | [39.69, 648.31, 296.27, 745.78] |
| fib | 44a3596c-0090-53ae-86dd-7560166b15c0 | [306.14, 47.6, 562.76, 133.03] |
| dft | eabf77bc-88cd-576b-bee5-1bf27aa1459f | [306.14, 143.06, 562.8, 444.78] |

逐项原文、精确字符范围和来源快照见同目录 PAPER-B-METHODS-INVENTORY.json。
