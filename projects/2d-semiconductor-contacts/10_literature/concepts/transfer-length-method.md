---
concept_id: transfer-length-method
aliases: []
type: foundational
status: learning
is_first_principle: false
canonical_statement: 用多个沟道长度器件的总电阻线性拟合，分离沟道片电阻与两端接触电阻。
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
- 10_literature/papers/liApproachingQuantumLimit2023/01_source/evidence-results.md
created_at: '2026-10-01T14:38:35.850181+00:00'
id: concept:transfer-length-method
object_type: concept
links:
- rel: derived-from
  target: paper:liApproachingQuantumLimit2023
  evidence:
  - file: 10_literature/concepts/transfer-length-method.md
    field: papers/paper_ids
    source_refs: []
  confidence: medium
  status: candidate
  generated_by: wf-registry
paper_ids:
- paper:liApproachingQuantumLimit2023
requested_role: knowledge-builder
---

# 概念：传输长度法（TLM）

## 1. 一句话定义

用多个沟道长度器件的总电阻线性拟合，分离沟道片电阻与两端接触电阻。

## 2. 为什么需要这个概念

单个器件的电阻通常混合沟道和接触贡献。

## 3. 直观理解

比较不同长度；长度增加的部分归入沟道，外推到零长度的截距归入接触。

## 4. 形式化定义

$R_{tot}W=R_{sh}L+2R_c$；这是方法解释式，不是本文编号公式。

## 5. 公式与符号

Rtot单位Ω，W/L单位长度，Rsh单位Ω/□，Rc单位Ω·长度；原文Lc表示沟道长度。

## 6. 前因后果

Fig.3b纵截距为2Rc；使用相同载流子浓度、线性工作区及近似对称接触。

## 7. 与相近概念的区别

LT不是几何间隙：本文LT=5.1 nm为提取值，几何间隙约0.285 nm。

## 8. 常见误区

接触内外片电阻相同的假设可能因电荷转移失效；很小截距需检查置信区间。

## 9. 代表文献迷你综述

本文Fig.3图注与Extended Data Fig.5图注；未独立复算Source data。

## 10. 开放问题

TODO(user)：取得源数据重拟合，评估短沟道与接触区片电阻差异。

新概念说明替代或修正了什么；旧概念说明为何仍重要。概念定义在本卡唯一维护，正文链接关联概念卡及论文。
