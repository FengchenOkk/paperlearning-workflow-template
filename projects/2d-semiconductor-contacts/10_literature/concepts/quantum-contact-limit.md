---
concept_id: quantum-contact-limit
aliases: []
type: foundational
status: learning
is_first_principle: false
canonical_statement: 在原文的理想弹道通道计数约定下，有限横向模式数给出宽度归一化接触电阻的非零下限。
extends: []
replaces: []
first_defined_in: TODO(user)
first_seen_year: TODO(user)
prerequisites: []
related: []
contrasts: []
papers:
- liApproachingQuantumLimit2023
generated_by: current-codex-session/manual-handoff
model_role: literature-reader
prompt_version: sb-concepts-v1
source_refs:
- 10_literature/papers/liApproachingQuantumLimit2023/01_source/evidence-mechanism.md
created_at: '2026-10-01T14:38:26.170304+00:00'
id: concept:quantum-contact-limit
object_type: concept
links:
- rel: co-occurs
  target: concept:transfer-length-method
  evidence:
  - file: 10_literature/papers/liApproachingQuantumLimit2023/04_analysis/analysis.yaml
    field: concepts[0]
    source_refs:
    - 10_literature/papers/liApproachingQuantumLimit2023/01_source/evidence-mechanism.md
  - file: 10_literature/papers/liApproachingQuantumLimit2023/04_analysis/analysis.yaml
    field: concepts[2]
    source_refs:
    - 10_literature/papers/liApproachingQuantumLimit2023/01_source/evidence-results.md
  confidence: medium
  weight: 1.0
  status: candidate
  generated_by: wf-knowledge
  input_hash: 86eec3bdf57e762a05532ebcb40ea27485016f79e24641eb1819ef8a15e17167
- rel: derived-from
  target: paper:liApproachingQuantumLimit2023
  evidence:
  - file: 10_literature/concepts/quantum-contact-limit.md
    field: papers/paper_ids
    source_refs: []
  confidence: medium
  status: candidate
  generated_by: wf-registry
paper_ids:
- paper:liApproachingQuantumLimit2023
requested_role: knowledge-builder
---

# 概念：二维接触量子下限

## 1. 一句话定义

在原文的理想弹道通道计数约定下，有限横向模式数给出宽度归一化接触电阻的非零下限。

## 2. 为什么需要这个概念

即使消除额外界面散射，有限传导模式也限制电导。

## 3. 直观理解

像有限数量的并行通道：通道更多，整体电阻更小。

## 4. 形式化定义

$R_{c,\min}=h/(2q^2)\sqrt{\pi/(2n_{2D})}$；原文式(1)，p.274。

## 5. 公式与符号

h单位J·s，q单位C，n₂D单位m⁻²，结果为Ω·m；换成Ω·μm需乘10⁶。

## 6. 前因后果

n₂D=3×10¹³ cm⁻²时下限29.53 Ω·μm，42 Ω·μm约为1.42倍。

## 7. 与相近概念的区别

不等于肖特基势垒为零；后者并不保证所有模式都无背散射地注入。

## 8. 常见误区

勿把Ω·μm当Ω·μm²；勿把高浓度下限当材料常数。

## 9. 代表文献迷你综述

原文引Landauer工作；本轮仅核对本文式(1)，未独立读取该经典原文。

## 10. 开放问题

TODO(user)：不同谷/自旋简并、非理想透射及有限温度的模式计数。

新概念说明替代或修正了什么；旧概念说明为何仍重要。概念定义在本卡唯一维护，正文链接关联概念卡及论文。
