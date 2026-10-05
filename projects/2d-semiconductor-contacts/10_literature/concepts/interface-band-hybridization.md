---
concept_id: interface-band-hybridization
aliases: []
type: foundational
status: learning
is_first_principle: false
canonical_statement: 不同材料的轨道耦合使电子态包含双方轨道成分；本文强调费米能级附近跨Sb/MoS₂界面的混合态。
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
created_at: '2026-10-01T14:38:30.671759+00:00'
id: concept:interface-band-hybridization
object_type: concept
links:
- rel: co-occurs
  target: concept:quantum-contact-limit
  evidence:
  - file: 10_literature/papers/liApproachingQuantumLimit2023/04_analysis/analysis.yaml
    field: concepts[0]
    source_refs:
    - 10_literature/papers/liApproachingQuantumLimit2023/01_source/evidence-mechanism.md
  - &id001
    file: 10_literature/papers/liApproachingQuantumLimit2023/04_analysis/analysis.yaml
    field: concepts[1]
    source_refs:
    - 10_literature/papers/liApproachingQuantumLimit2023/01_source/evidence-mechanism.md
  confidence: medium
  weight: 1.0
  status: candidate
  generated_by: wf-knowledge
  input_hash: 86eec3bdf57e762a05532ebcb40ea27485016f79e24641eb1819ef8a15e17167
- rel: co-occurs
  target: concept:transfer-length-method
  evidence:
  - *id001
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
  - file: 10_literature/concepts/interface-band-hybridization.md
    field: papers/paper_ids
    source_refs: []
  confidence: medium
  status: candidate
  generated_by: wf-registry
paper_ids:
- paper:liApproachingQuantumLimit2023
requested_role: knowledge-builder
---

# 概念：界面能带杂化

## 1. 一句话定义

不同材料的轨道耦合使电子态包含双方轨道成分；本文强调费米能级附近跨Sb/MoS₂界面的混合态。

## 2. 为什么需要这个概念

能带对齐不足以描述跨范德华间隙的注入效率，还需检查耦合。

## 3. 直观理解

电子态在两种材料中都有空间分布，界面不再仅是两个彼此独立的能带。

## 4. 形式化定义

用轨道投影能带、局部态密度、空间电荷分布判断；本文Fig.1是DFT结果。

## 5. 公式与符号

Sb pz与Mo d轨道沿垂直方向的重叠增大，杂化态跨EF。

## 6. 前因后果

电荷转移与能带杂化共同支持接触区简并掺杂；两者概念不同。

## 7. 与相近概念的区别

杂化不等于必须形成共价键；本文XPS未发现Sb–S键形成证据。

## 8. 常见误区

勿把计算杂化态称为实验直接观测；勿仅凭Rc降低定量分配机制贡献。

## 9. 代表文献迷你综述

本文Fig.1/p.276；其他文献全文未读取，TODO(user)。

## 10. 开放问题

TODO(user)：沉积温度、洁净度、取向分布及模型厚度对杂化的定量影响。

新概念说明替代或修正了什么；旧概念说明为何仍重要。概念定义在本卡唯一维护，正文链接关联概念卡及论文。
