# B1：Sb 指数横线及接触方法原句（待用户决定）

用户回复 `A4 accept`，已记录A4的来源归属与独立METHOD分类。本卡只呈现B1，实际decision=null。

| 字段 | 当前对象 |
| --- | --- |
| ID / version | 5ca9a9b2-fc14-5c6e-997d-80a0bdef2605 / 1 |
| type / layer | METHOD / SEMANTIC |
| epistemic / application state | AUTHOR_CLAIM / CANDIDATE |
| 原人工记录 | human-source-B-b-contact-method-1：REVISE，保持不变 |
| 原对象 ID / version | 9b030c80-1944-527e-bada-05c7f41bb8ea / 1 |
| pipeline / 对象创建器 | source-graph-v6 / local-rule-extractor-v4（此对象未被分组修订重写） |

原用户返修原话：`revise ,米勒指数应该是011(上有一横线)2，表示的方向`。原纠正记录明确横线位于第三位数字（第二个1），记作 `(01\bar{1}2)`。其中“表示的方向”保持ATTRIBUTED_USER_NOTE，不把它当作已核验的晶体学解释。E0绑定只维持原REVISE，不自动产生ACCEPT。

当前修正：原PDF字符提取原样保留 `(0112)`；独立符号视图利用PDF短横线绘制与字形位置（PDF_DRAWING_AND_GLYPH）呈现 `(011̅2)`，第三位1有横线，末位2没有横线。这不是重写原文或补造科学解释。

原始PDF：[第1页](E:/PaperLearning/backend/data/documents/4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd.pdf)。source anchor `c929285d-5f90-5779-9c0f-03a90e777cbf`，span `c72e10ec-d636-52a0-bb9d-97aedc6d0243`，字符 [0, 1695)，bbox `[217.32009887695312, 218.87550354003906, 560.9495239257812, 502.9736328125]`；精度TEXT_BLOCK，包含摘要上下文。当前独立METHOD对应原句：

```text
Here we push the electrical contact of monolayer molybdenum 
disulfide close to the quantum limit by hybridization of energy bands with semi- 
metallic antimony (0112) through strong van der Waals interactions.
```

当前符号视图（来自实际数据库notation记录）：

```text
Here we push the electrical contact of monolayer molybdenum 
disulfide close to the quantum limit by hybridization of energy bands with semi- 
metallic antimony (011̅2) through strong van der Waals interactions.
```

中文释义：作者称，通过与半金属Sb的能带杂化及强范德华相互作用，使单层MoS₂电接触接近量子极限。本项审核原句的来源、METHOD归属及横线显示；“接近量子极限”保持AUTHOR_CLAIM，不接受其科学有效性。

![原始PDF接触方法及指数](E:/PaperLearning/.runtime/gate-a-a2a-revision-20261011/review-b1/original-contact-method-context.png)

图中前面的“stability issues”属于上一句上下文；B1从“Here we push”开始，到“interactions.”结束。“The contacts”属于下一句。完整原始源块：

![完整摘要源块](E:/PaperLearning/.runtime/gate-a-corrections-20261011/paper-b-block-1.png)

技术建议：ACCEPT 当前原句来源、METHOD分类和第三位1横线显示。这是模型建议，不是人类决定。请判断横线位置、原句边界及来源是否忠实；不评估晶体学含义或接触性能。

source SHA256 `4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd`；current evidence fingerprint `6bede47676de4e95302dcb5d577f4b13e372b5af21d553122e09a54fa617725a`；prediction key `736ff73f7f51505e00e0b893722f5266f0c4a54987c8847271117727291195b5`；parser `1.28.2+layout-v3-notation`。对象来自当前隔离评估DB，应用状态保持CANDIDATE；无SCIENTIFIC_VALIDITY VERIFIED。

等待 B1 ACCEPT / REVISE / REJECT 后才呈现B2。原REVISE、冻结gold及模型分数保留；当前人工指标在全部审核完成后计算；Gate B不开始。
