# B2：稳定性结果原句及 I_on / V_th 下标（待用户决定）

用户回复 `B1 accept`，已记录B1的来源归属、METHOD分类及横线显示。本卡只呈现B2，实际decision=null。

| 字段 | 当前对象 |
| --- | --- |
| ID / version | 8c008d5d-6389-503d-8c92-ea46a92fdae2 / 1 |
| type / layer | RESULT / ARGUMENT |
| epistemic / application state | AUTHOR_CLAIM / CANDIDATE |
| 原人工记录 | human-source-B-b-stability-1：REVISE，保持不变 |
| 原对象 ID / version | 5b7945d5-d837-50a3-aef4-52e64e07adc7 / 1 |
| pipeline / 对象创建器 | source-graph-v6 / local-rule-extractor-v4（此对象未被分组修订重写） |

原用户返修原话：`revise ，一些公式标识需要注意下标，如Ion其中on是下标。`。`I_on`是用户明确提供的例子；`V_th`是模型补充核对原PDF的伴随修正，原记录的MODEL_SOURCE_REVIEW与explicit_user_example=false保持不变。本次展示两者以等待新的实际决定，不追溯补造原用户指示。E0绑定只维持旧REVISE，不自动接受。

当前修正：原PDF字符提取原样保留 `Ion`、`Vth`；独立符号视图根据PDF字形基线与字号（PDF_BASELINE_AND_SIZE）显示 `I_on`、`V_th`，下标分别是on、th。原始文字、24h数值及作者“不明显退化”的限定保留。

原始PDF：[第5页](E:/PaperLearning/backend/data/documents/4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd.pdf)。source anchor `c17caaf5-78ce-5864-9b13-c28318acf332`，span `61293a29-9427-5c14-99d0-e97649c830ce`，字符 [0, 824)，bbox `[39.68510055541992, 552.8456420898438, 296.334228515625, 681.276123046875]`；精度TEXT_BLOCK，包含完整稳定性条件及对比上下文。当前RESULT原句：

```text
No obvious degradation of Ion, threshold voltage 
(Vth) and subthreshold swing (SS) was observed during 24 h for the Sb 
contact.
```

当前符号视图（来自实际数据库notation记录）：

```text
No obvious degradation of I_on, threshold voltage 
(V_th) and subthreshold swing (SS) was observed during 24 h for the Sb 
contact.
```

中文释义：作者报告，Sb接触在24h观察期间，I_on、阈值电压V_th及亚阈值摆幅SS未出现明显退化。同一源块的前文限定测试为125°C、氮气环境；本项保留该证据上下文，不扩大成任意温度、气氛或长期稳定性结论。下一句Bi接触下降41%属于上下文，不是此RESULT原句。

![原始PDF稳定性条件及下标](E:/PaperLearning/.runtime/gate-a-a2a-revision-20261011/review-b2/original-stability-subscripts-context.png)

B2从“No obvious degradation”开始，到“contact.”结束。上方125°C、氮气环境是条件；下方“In contrast”开始Bi对比。完整源块：

![完整稳定性源块](E:/PaperLearning/.runtime/gate-a-corrections-20261011/paper-b-block-5.png)

技术建议：ACCEPT 当前来源、RESULT归属、I_on/V_th下标及24h限定。这是模型建议，不是人类决定。本项不证明实验可靠性、器件稳定性或科学有效性。

source SHA256 `4e09fdba4af8799d7868b2cdeee8ecea5224f452a3a1702dc00cabcd86183ddd`；current evidence fingerprint `23b6c679139ef48e4db933538c2dcd046091ef96362426de936ae06ab3214518`；prediction key `c122b3c98f960ccc6cc6c4907dba1211ad96196e7fcb12b69074cc2b868fb7aa`；parser `1.28.2+layout-v3-notation`。对象来自当前隔离评估DB，应用状态保持CANDIDATE；无SCIENTIFIC_VALIDITY VERIFIED。

这是既定顺序的最后一项。等待 B2 ACCEPT / REVISE / REJECT；审核结束后另算当前人工指标，对照冻结协议并保留原模型分数；Gate B不开始。
