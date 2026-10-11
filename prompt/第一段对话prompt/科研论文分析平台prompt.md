# MASTER PROJECT PROMPT

## Research-Grade Paper Knowledge Graph & Scientific Paper Intelligence System

你正在接管一个已有但架构方向错误的 Git repository：

`paperlearning-workflow-template`

这是一个早期 V0 原型。

它此前主要围绕：

- Markdown / YAML
- CLI workflow
- literature reading workflow
- translation
- concept cards
- evidence tracking
- task orchestration
- JSON knowledge graph

进行设计。

这个方向现在不再作为产品架构约束。

---

# 0. 你的任务性质

这不是一次普通重构。

这不是给现有 CLI 增加一个网页。

这不是给 Markdown 文件加一个 graph viewer。

这不是“Chat with PDF”。

这不是“AI 论文总结器”。

这不是“论文翻译器”。

这也不是简单的 RAG 项目。

---

你要把这个 repository 重构成一个真正的：

# Scientific Paper Knowledge Intelligence Platform

核心产品目标：

> 给定一篇科研论文，系统从论文原文出发，对论文中的知识、理论、公式、方法、实验、数据、论证、创新和前置知识进行结构化建模，并从理解该论文所需的第一性原理开始构建一个具有严格来源追踪的交互式知识网络。

用户最终不是只看到：

> “这篇论文讲了什么？”

而是能够看到：

> “这篇论文为什么成立？”

> “理解它需要什么？”

> “这些知识从哪里来？”

> “哪些基础理论最终导致了作者的方法？”

> “作者到底在哪里做出了创新？”

> “作者的证据是否真正支持他的结论？”

> “某一个公式从什么理论推导出来？”

> “某一个结论在论文原文哪里？”

最终系统必须能够构建：

```text
First Principles
        ↓
Fundamental Mathematics / Science
        ↓
Domain Foundations
        ↓
Established Theories
        ↓
Methods / Materials / Algorithms / Devices
        ↓
Prior Research
        ↓
Research Gap
        ↓
Paper Problem
        ↓
Paper Method
        ↓
Experiment / Simulation
        ↓
Evidence
        ↓
Results
        ↓
Claims
        ↓
Contribution
        ↓
Limitations / Open Questions
```

但这不是一棵树。

它必须是：

# typed, directed, evidence-backed scientific knowledge graph.

---

# 1. 首要原则：不要维护错误架构的兼容性

首先检查 Git 状态。

保护：

- 用户未提交文件
- 用户私密配置
- API Key
- `.env`
- 本地论文
- 本地研究数据

不要破坏这些内容。

除此之外：

旧架构不具有兼容优先级。

Git history 本身已经是 V0 的历史记录。

如果旧代码阻碍新的 domain architecture：

删除、替换或者重构它。

不要为了兼容：

```text
projects/
workflow/
knowledge-map.md
knowledge-graph.json
old YAML contracts
legacy CLI
```

而损害新系统设计。

但是首先进行代码审计。

对于每个旧模块，只判断三件事：

```text
REUSE
REWRITE
REMOVE
```

只有真正符合新 architecture 的代码才能保留。

---

# 2. 产品重新定义

暂定产品代号：

# PaperGraph

名称不是架构的一部分，可后续修改。

PaperGraph 是：

> Evidence-grounded scientific knowledge reconstruction system.

核心对象不是：

```text
file
markdown
task
folder
```

核心对象是：

```text
Paper
ScientificEntity
KnowledgeNode
KnowledgeEdge
Claim
Evidence
SourceAnchor
ReasoningChain
LearningPath
```

文件只是输入。

数据库里的科学知识结构才是系统状态。

---

# 3. 系统的五个知识层

整个系统必须明确分离五个 layer。

## Layer 1 — Source Layer

忠实描述论文原文。

包括：

```text
Paper
Page
Section
Paragraph
Sentence / Span
Equation
Figure
Figure Caption
Table
Reference
Footnote
Supplement
```

这一层回答：

> 原论文究竟写了什么？

不得进行解释性改写。

---

## Layer 2 — Semantic Knowledge Layer

把论文中的科学实体结构化。

例如：

```text
Concept
Definition
Physical Quantity
Mathematical Object
Law
Principle
Theory
Model
Approximation
Assumption
Method
Algorithm
Material
Device
Architecture
Process
Experiment
Simulation
Dataset
Metric
Parameter
Phenomenon
```

这一层回答：

> 论文涉及哪些知识？

---

## Layer 3 — Reasoning / Argument Layer

重建作者的科学论证。

包括：

```text
Research Problem
Motivation
Research Gap
Hypothesis
Claim
Evidence
Observation
Reasoning
Assumption
Result
Conclusion
Limitation
Counterargument
Uncertainty
```

形成：

```text
Claim
  ↓ supported_by
Evidence
  ↓ interpreted_as
Observation
  ↓ explained_by
Mechanism
  ↓ supports
Conclusion
```

这一层回答：

> 作者为什么认为他的结论成立？

---

## Layer 4 — Learning / First-Principles Layer

从论文知识反向构建 prerequisite graph。

例如：

```text
Paper concept
    ↑
required by
Domain theory
    ↑
required by
Fundamental theory
    ↑
required by
Mathematics / physical laws
```

然后重新正向形成：

```text
First Principle
→ Fundamental Theory
→ Domain Concept
→ Paper Concept
→ Paper Method
→ Result
```

这一层回答：

> 如果我从基础开始，需要如何学到这篇论文？

---

## Layer 5 — Research Context Layer

论文不是孤立存在。

建立：

```text
Prior Work
Competing Method
Classical Work
Review
Author Previous Work
Research Lineage
Extended Work
Contradictory Work
```

最终形成：

```text
Existing theory
      ↓
Existing method
      ↓
Known limitation
      ↓
Research gap
      ↓
Paper innovation
```

这一层回答：

> 论文在整个研究领域中的位置是什么？

---

# 4. Scientific Ontology

禁止使用万能 `concept` 节点。

建立正式 Node Ontology。

至少包含：

```text
PAPER

SECTION
PARAGRAPH
SOURCE_SPAN

FIGURE
TABLE
EQUATION
REFERENCE

FIRST_PRINCIPLE

MATHEMATICAL_CONCEPT
MATHEMATICAL_THEOREM
MATHEMATICAL_METHOD

PHYSICAL_LAW
PHYSICAL_CONCEPT
PHYSICAL_QUANTITY
PHENOMENON

CHEMICAL_CONCEPT
MATERIAL

THEORY
MODEL

DEFINITION

ASSUMPTION
APPROXIMATION

METHOD
ALGORITHM
PROCESS

DEVICE
ARCHITECTURE

EXPERIMENT
SIMULATION
DATASET

PARAMETER
METRIC

RESEARCH_PROBLEM
MOTIVATION
RESEARCH_GAP

HYPOTHESIS
CLAIM
OBSERVATION
EVIDENCE

RESULT
CONCLUSION

CONTRIBUTION
INNOVATION

LIMITATION
OPEN_QUESTION

PRIOR_WORK
```

Ontology 必须允许扩展。

不能把学科写死在代码中。

---

# 5. Scientific Edge Ontology

禁止主要关系使用：

```text
related_to
```

Edge 必须有语义。

至少支持：

```text
CONTAINS

MENTIONS
DEFINES
DESCRIBES

DERIVES_FROM
MATHEMATICALLY_DERIVES_FROM

DEPENDS_ON
PREREQUISITE_OF

USES
APPLIES
IMPLEMENTS

ASSUMES
APPROXIMATES

EXPLAINS
CAUSES
AFFECTS

MEASURES
MEASURED_BY

SIMULATES
SIMULATED_BY

VALIDATES
VALIDATED_BY

SUPPORTS
SUPPORTED_BY

CONTRADICTS

COMPARES_WITH

EXTENDS
IMPROVES

MOTIVATES
ADDRESSES
SOLVES

PRODUCES
RESULTS_IN

CITES
CITED_BY

EVIDENCE_FOR

PART_OF
```

每条 edge 本身也是 scientific object。

必须包含：

```text
id
source_node_id
target_node_id
relation_type

confidence

verification_status

provenance[]

created_by

model

prompt_version

created_at
```

---

# 6. Knowledge Graph 必须是 Source of Truth

旧系统中的：

```text
knowledge-graph.json
knowledge-map.md
concept-guide.md
```

不再是主数据源。

它们最多只能作为：

```text
export / view
```

真正的 graph 必须存储在数据库 domain model 中。

UI、AI、Search、Learning Path、Argument Graph 全部从统一 graph model 获取数据。

严禁：

```text
UI 自己维护一个 graph
AI 又维护一个 graph
Markdown 再维护一个 graph
JSON 再维护一个 graph
```

只能有一个 canonical graph model。

---

# 7. Evidence / Provenance 是第一优先级

科研级系统最重要的不是 AI 多聪明。

而是：

# traceability.

所有 paper-derived scientific claims 都必须能够回到论文原始证据。

设计：

```ts
SourceAnchor {
    id

    paper_id

    page_number

    section_id?

    paragraph_id?

    source_span_id?

    start_char?
    end_char?

    bbox?

    equation_id?
    figure_id?
    table_id?

    text?

    source_hash
}
```

Evidence：

```ts
Evidence {
    id

    evidence_type

    source_anchor_id?

    external_source_id?

    supports_object_id

    support_type

    confidence

    verification_status

    note
}
```

---

# 8. 所有 AI 内容必须标明 epistemic status

至少支持：

```text
PAPER_EXPLICIT

PAPER_IMPLICIT

AUTHOR_CLAIM

OBSERVED_DATA

REFERENCE_DERIVED

BACKGROUND_KNOWLEDGE

AI_INTERPRETATION

AI_DERIVATION

AI_HYPOTHESIS

UNVERIFIED

CONFLICTING

UNKNOWN
```

UI 必须让用户看出来这些区别。

例如：

```text
Paper
External source
Established knowledge
AI derivation
AI interpretation
Unverified
```

不得混在一起。

---

# 9. 科研真实性规则

这是 hard requirement。

任何 LLM prompt 都必须继承以下规则：

```text
Never fabricate paper content.

Never fabricate equations.

Never fabricate equation numbers.

Never fabricate page locations.

Never fabricate experimental parameters.

Never fabricate measurement values.

Never fabricate citations.

Never fabricate references.

Never fabricate datasets.

Never fabricate author conclusions.

Never turn an inference into a paper statement.

Never turn a correlation into a causal relationship.

Never present external knowledge as if it came from the paper.
```

没有 evidence：

```text
UNVERIFIED
```

论文没有说明：

```text
NOT_SPECIFIED_IN_PAPER
```

AI 根据理论推导：

```text
AI_DERIVATION
```

AI 进行解释：

```text
AI_INTERPRETATION
```

不能通过“模型信心很高”替代证据。

---

# 10. 第一性原理不是关键词树

旧系统中简单声明：

```text
first_principle_ids
```

远远不够。

新的 first-principles engine 必须做真正的：

# Recursive prerequisite decomposition.

对于论文核心节点 N：

询问：

```text
What must a researcher already understand
to rigorously understand N?
```

得到：

```text
P1
P2
P3
```

继续对每一个 prerequisite 递归。

直到达到 stopping criteria。

---

# 11. First-Principles Stopping Criteria

禁止无限向下展开。

一个节点可以作为当前路径的基础节点，当：

```text
1. 它属于当前目标读者假定基础；
或
2. 继续拆解对理解论文已经没有明显帮助；
或
3. 它已经是该领域普遍接受的基础定义/规律；
或
4. 用户指定学习深度到此为止。
```

例如半导体光电论文不应该机械展开到：

```text
set theory
→ natural numbers
→ arithmetic
```

第一性原理必须是：

> task-relative first principles

而不是哲学意义上的无限还原。

---

# 12. Why-Needed Chain

每一个 learning node 必须回答：

```text
What is it?

Why does it matter?

Why is it needed for THIS paper?

What requires it?

What does it depend on?

Where is it eventually used?
```

必须能够产生：

```text
Maxwell Equations
↓
Wave Equation
↓
Guided Modes
↓
Effective Refractive Index
↓
Propagation Constant
↓
Phase Shift
↓
Interference
↓
Optical Modulation
↓
Paper Device
↓
Measured Result
```

用户必须能够点击：

```text
Why do I need this?
```

看到完整路径。

---

# 13. 四种主要 Graph View

一个 underlying graph。

多个 view。

不要创建四份数据。

---

## View A — Knowledge Graph

展示：

```text
first principles
theories
concepts
methods
devices
experiments
results
```

---

## View B — Argument Graph

展示：

```text
claim
↓
evidence
↓
reasoning
↓
conclusion
```

---

## View C — Innovation Graph

展示：

```text
prior work
↓
limitation
↓
research gap
↓
paper idea
↓
new method
↓
result
↓
advantage
```

---

## View D — Learning Graph

展示：

```text
prerequisites
↓
learning order
↓
paper understanding
```

Graph view 是 projection。

不是独立数据模型。

---

# 14. Paper Source Model

必须保留 PDF 中结构位置。

一篇论文解析为：

```text
Paper
├── Pages
├── Sections
│   ├── Paragraphs
│   ├── Equations
│   ├── Figures
│   └── Tables
└── References
```

重要要求：

文本解析后不能只剩 Markdown。

必须尽可能保留：

```text
page
block
bounding box
reading order
section
caption association
equation numbering
reference numbering
```

这样才能完成：

```text
Graph Node
↔
Original PDF
```

双向定位。

---

# 15. PDF Parsing Architecture

设计 parsing abstraction。

不要把系统绑定到一个库。

例如：

```python
class DocumentParser:
    parse_document()
    extract_text_blocks()
    extract_sections()
    extract_equations()
    extract_figures()
    extract_tables()
    extract_references()
```

实现 layered parser strategy。

可评估：

```text
PyMuPDF
GROBID
Docling
```

并允许 OCR fallback。

不要假定任何一个 parser 永远正确。

保存：

```text
parser
parser_version
parse_confidence
```

---

# 16. Equation Intelligence

Equation 必须成为 first-class entity。

结构：

```ts
Equation {
    id

    paper_id

    equation_number?

    latex

    source_anchor

    symbols[]

    assumptions[]

    meaning_math

    meaning_physical

    derivation

    derived_from[]

    used_by[]

    confidence

    verification_status
}
```

---

用户点击公式后至少看到：

```text
Original Equation

Symbol Definitions

Mathematical Meaning

Physical Meaning

Where It Comes From

Assumptions

Approximation

Derivation

Why The Paper Uses It

Related Figure

Related Result

Source Evidence
```

---

# 17. Equation Derivation Graph

公式推导不能只是长文本。

建立：

```text
Equation A
    ↓ operation
Equation B
    ↓ substitution
Equation C
    ↓ approximation
Paper Equation
```

每一步包含：

```text
operation
reason
assumption
source
```

如果推导不是论文提供：

必须显示：

```text
AI reconstructed derivation
```

不能冒充作者推导。

---

# 18. Figure Intelligence

Figure 也是 first-class entity。

系统需要分析：

```text
What is plotted?

What are the axes?

What are the units?

What do curves / colors / markers represent?

What experimental condition changes?

What trend is observed?

What mechanism explains the trend?

Which claim does the figure support?

Does the data fully support the claim?

What alternative explanations exist?
```

建立：

```text
Theory
↓
Prediction
↓
Measurement
↓
Figure
↓
Observation
↓
Claim
```

Figure analysis 必须引用：

```text
caption
surrounding paragraphs
figure location
```

不得只通过视觉猜测。

---

# 19. Table Intelligence

同样结构化：

```text
columns
units
conditions
metrics
baselines
values
comparisons
```

并连接：

```text
method
baseline
metric
claim
result
```

---

# 20. Translation Architecture

翻译不是 AI explanation。

两者必须严格分开。

数据库保存：

```text
source segment
translation segment
alignment
```

支持：

```text
Original
Chinese
Bilingual
```

翻译必须保持：

```text
equation IDs
figure IDs
table IDs
citation IDs
technical terminology
numbers
units
```

翻译不允许自行补充解释。

解释单独存储。

---

# 21. Deep Reading Architecture

不是生成一个：

```text
summary.md
```

而是结构化生成：

```text
PaperOverview

SectionAnalysis

MethodAnalysis

EquationAnalysis

FigureAnalysis

ArgumentAnalysis

ContributionAnalysis

LimitationAnalysis
```

然后 UI 组合展示。

---

# 22. Paper Overview Schema

至少：

```text
research_domain

research_object

core_problem

motivation

research_gap

research_question

hypothesis

main_method

main_contribution

key_results

limitations

open_questions
```

每一项必须有：

```text
evidence
confidence
epistemic_status
```

---

# 23. Section-Level Reading

每 section 至少具有三层：

```text
Level 1:
What is this section doing?

Level 2:
Detailed scientific explanation

Level 3:
Expert analysis
```

Expert analysis 包括：

```text
assumptions
method validity
mathematical implications
physical interpretation
relation to prior work
limitations
unresolved issues
```

---

# 24. Scientific Claim Model

Claim 必须独立建模。

```ts
Claim {
    id

    text

    claim_type

    paper_id

    source_anchor

    evidence_ids[]

    assumptions[]

    qualifiers[]

    confidence

    support_strength

    epistemic_status
}
```

Claim type 至少：

```text
BACKGROUND
METHOD
MECHANISTIC
EMPIRICAL
COMPARATIVE
CAUSAL
PERFORMANCE
GENERALIZATION
CONCLUSION
```

---

# 25. Argument Evaluation

系统不仅复述作者。

还需要区分：

```text
Author claims X
```

与：

```text
Evidence strongly supports X
```

系统应该能够输出：

```text
SUPPORTED
PARTIALLY_SUPPORTED
WEAKLY_SUPPORTED
NOT_DEMONSTRATED
CONFLICTING
INSUFFICIENT_INFORMATION
```

必须给理由和 evidence。

不能把 AI 的判断写成绝对真理。

---

# 26. Innovation Intelligence

建立独立 Innovation Path。

自动识别：

```text
Problem
↓
Existing Approach
↓
Existing Limitation
↓
Research Gap
↓
Paper Insight
↓
Novel Component
↓
Method
↓
Result
↓
Advantage
```

并回答：

```text
What exactly is new?

What is inherited?

What is merely implementation?

What is actually demonstrated?

What is claimed but not fully demonstrated?
```

---

# 27. External Scientific Knowledge

第一性原理图谱不能只依赖当前 PDF。

系统需要 External Scholarly Retrieval abstraction。

未来可接：

```text
Crossref
OpenAlex
Semantic Scholar
arXiv
PubMed
publisher metadata
Zotero
```

不要把 provider 写死。

设计：

```python
class ScholarlySourceProvider:
    search()
    get_metadata()
    get_references()
    get_citations()
    resolve_identifier()
```

外部内容必须保存 provenance。

---

# 28. Knowledge Verification

Background knowledge 也不能无限相信 LLM。

建立：

```text
candidate
↓
evidence lookup
↓
verification
↓
verified
```

状态：

```text
CANDIDATE

SUPPORTED

VERIFIED

DISPUTED

REJECTED

STALE
```

---

# 29. AI Architecture

不要创建一个 5000-token mega prompt 完成所有工作。

将 AI pipeline 分解。

建议逻辑角色：

```text
Paper Structural Analyzer

Concept Extractor

Scientific Entity Extractor

Equation Analyst

Figure Analyst

Argument Miner

Prerequisite Builder

First-Principles Expander

Research Context Retriever

Innovation Analyst

Scientific Verifier

Translator

Graph Synthesizer
```

角色是 pipeline responsibility。

不必强制每个角色使用独立模型。

---

# 30. LLM Provider Abstraction

不要把系统绑定某个模型。

```python
class LLMProvider:
    generate()
    generate_structured()
    embed()
```

不同任务使用 configuration routing。

例如：

```text
paper_analysis

translation

graph_reasoning

verification

vision

embedding
```

允许未来接：

```text
OpenAI
Anthropic
Gemini
DeepSeek
local models
```

API Key 只来自环境变量 / secret store。

---

# 31. Structured AI Output

业务代码禁止解析任意自然语言格式。

所有 pipeline 输出：

```text
Pydantic model
JSON schema
```

执行：

```text
generate
↓
schema validation
↓
semantic validation
↓
repair if safe
↓
persist
```

结构错误：

retry。

科学证据不足：

不要 retry 到模型“编出来”。

应标记：

```text
UNVERIFIED
```

---

# 32. Graph Construction Pipeline

理想流程：

```text
PDF
↓
Document Parsing
↓
Source Model
↓
Scientific Entity Extraction
↓
Claims / Equations / Figures / Methods
↓
Entity Resolution
↓
Paper-internal Graph
↓
Argument Graph
↓
Prerequisite Analysis
↓
External Knowledge Retrieval
↓
First-Principles Expansion
↓
Evidence Verification
↓
Innovation Graph
↓
Learning Paths
↓
Graph Persistence
↓
Interactive UI
```

---

# 33. Entity Resolution

必须考虑：

```text
同义词
缩写
中英文名称
notation aliases
plural
acronyms
field-specific naming
```

例如：

```text
Finite-Difference Time-Domain
FDTD
finite difference time domain method
```

应映射到同一个 canonical entity。

但是自动 merge 必须谨慎。

状态：

```text
candidate_same_entity
verified_same_entity
```

不允许模型随意合并两个科学概念。

---

# 34. Stable IDs

ID 不能依赖文件路径。

使用 UUID / ULID 或稳定 hash strategy。

Paper identity 优先：

```text
DOI
arXiv ID
PMID
canonical metadata hash
```

Graph node identity 独立于 UI 名称和文件位置。

---

# 35. Database Architecture

MVP 不要一开始引入不必要的分布式系统。

推荐核心：

```text
PostgreSQL
```

并使用：

```text
pgvector
```

用于 embedding retrieval。

Graph 可先使用：

```text
nodes table
edges table
```

关系模型表示。

不要因为项目叫 Knowledge Graph 就立即强制 Neo4j。

如果未来 graph query 明显需要 Neo4j：

通过 repository abstraction 添加。

---

# 36. Suggested Core Tables

至少设计：

```text
papers

paper_pages
paper_sections
source_spans

equations
figures
tables
references

knowledge_nodes
knowledge_edges

claims
evidence
source_anchors

translations

analyses

learning_paths

graph_views

ai_runs
verification_records
```

数据库必须通过 migration 管理。

---

# 37. Backend

推荐：

```text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
PostgreSQL
Redis
```

长时间分析任务使用 job queue。

选择成熟、可测试的 queue 实现。

不要在 HTTP request 内执行完整论文分析。

---

# 38. Job State Machine

```text
UPLOADED

PARSING

PARSED

STRUCTURAL_ANALYSIS

ENTITY_EXTRACTION

GRAPH_BUILDING

BACKGROUND_EXPANSION

VERIFYING

TRANSLATING

FINALIZING

READY

PARTIAL

FAILED
```

每一步保存：

```text
status
progress
error
run_id
input_hash
```

失败后可从中间恢复。

---

# 39. Frontend

推荐：

```text
Next.js
React
TypeScript
```

UI library：

选择稳定、轻量的 component architecture。

Graph：

优先评估：

```text
Cytoscape.js
```

因为核心需求是：

```text
large typed network
graph traversal
dynamic filtering
edge semantics
interactive layouts
```

PDF：

```text
PDF.js
```

Math：

```text
KaTeX
```

---

# 40. Frontend 信息架构

核心不是 dashboard。

核心页面：

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Paper Title | Search | View | Depth | Evidence | Settings           │
├─────────────────┬──────────────────────────────┬─────────────────────┤
│                 │                              │                     │
│ Paper Navigator │                              │ Node Inspector      │
│                 │                              │                     │
│ Abstract        │      KNOWLEDGE GRAPH         │ Definition          │
│ Introduction    │                              │ Explanation         │
│ Theory          │        ○────○────○            │ Why Needed          │
│ Method          │       / \  / \               │ Evidence            │
│ Results         │      ○──○────○──○             │ Equations           │
│ Conclusion      │       \   \ /                │ Paper Location      │
│                 │         ○──○                  │ Dependencies        │
│ Figures         │                              │ Dependents          │
│ Equations       │                              │                     │
├─────────────────┴──────────────────────────────┴─────────────────────┤
│ Original PDF / Bilingual Reading / Evidence Context                 │
└──────────────────────────────────────────────────────────────────────┘
```

Graph 是中心。

不是一个 tab 中的小工具。

---

# 41. Graph Interaction

必须支持：

```text
pan

zoom

fit

minimap

search

focus

expand

collapse

filter

path finding

depth selection

node pinning

graph history

back / forward
```

---

点击一个 node：

高亮：

```text
ancestors
current node
descendants
```

其他节点 fade。

---

# 42. Scientific Path Query

至少支持：

```text
Why is this needed?

Where does this come from?

Where is this used?

Show prerequisites.

Show path to paper contribution.

Show evidence chain.

Show derivation chain.

Show innovation lineage.
```

这几个操作是产品核心。

---

# 43. Progressive Disclosure

不要初次加载 300 个节点。

提供：

```text
Overview

Standard

Deep

First Principles
```

例如：

```text
Overview: 20–40 nodes

Standard: 50–120 nodes

Deep: 100–300 nodes

First Principles:
dynamic expansion
```

具体数量不是硬限制。

目标是保持可读性。

---

# 44. Learning Modes

支持用户理解程度：

```text
Beginner
Graduate
Expert
```

这不改变 underlying facts。

只改变：

```text
explanation depth
prerequisite stopping depth
terminology assumptions
```

---

# 45. Paper ↔ Graph 双向联动

这是核心体验。

用户点击论文文本：

```text
paragraph
```

系统显示：

```text
associated concepts
claims
equations
figures
```

用户点击 graph node：

PDF 自动跳转到：

```text
source page
source paragraph
highlight bbox/span
```

这一功能必须建立在真实 SourceAnchor 上。

禁止 fake highlight。

---

# 46. Search

统一搜索：

```text
paper text

concept

equation

figure

method

author

material

claim

metric
```

搜索结果定位：

```text
graph node
+
PDF location
```

---

# 47. AI Chat

Chat 是辅助功能。

不是系统核心。

回答必须基于：

```text
paper source
graph
evidence
external verified sources
```

每个 substantive answer 返回 citation objects。

用户可以问：

```text
为什么作者使用这个模型？

Eq. 7 从哪里来？

Figure 4 是否足以支持作者结论？

这个 approximation 的边界是什么？

如果去掉这个 assumption 会怎样？

帮我从 Maxwell equation 推到这里。

这个方法和 prior work 有什么区别？
```

---

# 48. AI Chat Hallucination Rule

回答必须区分：

```text
According to paper

According to external source

Established theory

Inference

Hypothesis
```

如果无法定位：

明确说明：

```text
I cannot verify this from the currently indexed evidence.
```

---

# 49. RAG Architecture

Chunking 不要简单：

```text
every 1000 tokens
```

优先按：

```text
section
paragraph
equation context
figure context
table context
reference context
```

建立 hierarchical retrieval。

Query 可以结合：

```text
semantic retrieval

source structure

knowledge graph neighborhood

claim evidence

keyword retrieval
```

---

# 50. Provenance-Aware Retrieval

任何 retrieval result 必须知道：

```text
source_id
paper_id
page
section
source_span
```

没有 provenance 的 embedding chunk 不允许成为正式 scientific evidence。

---

# 51. Caching

所有昂贵 AI 操作基于：

```text
input hash

prompt version

model

pipeline version
```

缓存。

论文重新打开时：

不能重新分析。

只有输入或分析版本变化才重新运行。

---

# 52. Reproducibility

每一次 AI 分析保存：

```text
run_id

model_provider

model_name

model parameters

prompt_version

pipeline_version

input_hash

started_at

completed_at

status

token_usage

cost if available
```

科研工具必须能回答：

> 这个分析是谁、什么时候、基于什么输入生成的？

---

# 53. Prompt Registry

所有系统 prompt 集中管理。

例如：

```text
backend/prompts/

paper_structure/
concept_extraction/
claim_extraction/
argument_analysis/
equation_analysis/
figure_analysis/
first_principles/
verification/
translation/
```

不要散落在 Python 文件中。

每一个 prompt 有版本号。

---

# 54. Evaluation System

这是科研级项目必须有的。

建立：

```text
evals/
```

至少评估：

```text
PDF structural accuracy

section detection

equation localization

figure association

concept extraction precision

edge correctness

claim extraction accuracy

claim-evidence alignment

provenance coverage

hallucination rate

translation fidelity

first-principles path quality

graph usefulness
```

---

# 55. Golden Test Paper

至少选择若干开放论文作为 golden fixtures。

每篇人工创建一小部分 truth：

```text
known sections
known equations
known claims
known concepts
known evidence
known relationships
```

然后测试 pipeline。

绝不能用：

```text
"LLM 返回了 JSON"
```

作为科学质量验收。

---

# 56. Provenance Coverage Metric

需要能够计算：

```text
number of scientific claims with valid evidence
/
total paper-derived scientific claims
```

目标：

paper-derived substantive claims 接近 100% 可追溯。

---

# 57. Graph Quality Checks

自动检测：

```text
orphan nodes

duplicate canonical entities

cycles in prerequisite graph

invalid source anchors

edges without provenance

paper claims without evidence

impossible graph references

stale verification

missing equation source

missing figure source
```

---

# 58. Tests

必须有：

```text
unit tests

schema tests

parser tests

graph tests

API integration tests

database tests

frontend component tests

E2E tests
```

核心 user journey 必须 E2E。

---

# 59. Core E2E Journey

至少：

```text
Upload PDF

→ parse successfully

→ paper appears

→ structural elements visible

→ knowledge graph generated

→ click concept

→ inspector opens

→ click source evidence

→ PDF jumps to correct page

→ select Why Needed

→ prerequisite chain visible

→ select contribution

→ innovation path visible

→ refresh browser

→ state persists
```

---

# 60. Error Handling

科研数据处理必须允许：

```text
PARTIAL SUCCESS
```

例如：

```text
text parsed
equations parsed
Figure 7 failed
```

不能整个 paper 变成：

```text
FAILED
```

必须记录 component-level errors。

---

# 61. Security

默认认为科研论文和研究资料可能未公开。

必须：

```text
never commit PDFs

never commit API keys

never log secrets

never log full private documents unnecessarily

configurable external model transmission

explicit storage locations
```

---

# 62. Privacy-Aware Processing

设计能力允许未来支持：

```text
local parser

local embedding

local model
```

即便 MVP 暂不全部实现。

Domain architecture 不得阻止 local-only mode。

---

# 63. Observability

需要 structured logging。

包括：

```text
request_id

paper_id

job_id

run_id

pipeline_step

duration

failure category
```

LLM 调用单独记录 tracing。

---

# 64. Repository Architecture

不要立即照抄此目录。

先审计后决定。

推荐目标形态大致：

```text
/
├── apps/
│   ├── web/
│   └── api/
│
├── packages/
│   ├── schemas/
│   ├── ontology/
│   └── shared/
│
├── services/
│   ├── document_processing/
│   ├── graph_engine/
│   ├── scientific_ai/
│   └── scholarly_retrieval/
│
├── prompts/
│
├── evals/
│
├── tests/
│
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── ontology/
│   └── research/
│
├── infra/
│
├── docker-compose.yml
│
└── README.md
```

如果实际工程上更适合其他布局：

可以调整。

但是 separation of concerns 必须保持。

---

# 65. Architecture Documents

在正式大规模编码前建立：

```text
docs/architecture/SYSTEM.md

docs/architecture/DATA-MODEL.md

docs/architecture/PIPELINE.md

docs/architecture/PROVENANCE.md

docs/ontology/SCIENTIFIC-ONTOLOGY.md

docs/architecture/AI-SYSTEM.md

docs/architecture/FRONTEND.md

docs/architecture/EVALUATION.md
```

---

# 66. ADR

重要技术决策使用：

```text
Architecture Decision Record
```

例如：

```text
ADR-001 database

ADR-002 graph storage

ADR-003 PDF parsing

ADR-004 knowledge graph frontend

ADR-005 LLM abstraction
```

---

# 67. 不要过度工程

“科研级”不等于：

```text
Kubernetes
20 microservices
Neo4j
Kafka
distributed event sourcing
```

一开始全部加入。

科研级代表：

```text
correctness

traceability

clear architecture

evaluation

reproducibility

scientific integrity

extensibility
```

优先 monolith/modular monolith。

当规模需要时再拆。

---

# 68. Phase 0 — Repository Audit

第一件事情：

完整检查当前 repository。

输出：

```text
current architecture

reusable components

obsolete components

architectural conflicts

security concerns

migration risk
```

创建：

```text
docs/legacy-audit.md
```

每个主要模块标记：

```text
KEEP
REFACTOR
REMOVE
```

---

# 69. Phase 1 — Foundation

建立：

```text
frontend

backend

database

migrations

core schemas

paper domain

source domain

graph domain

evidence domain
```

先不要做花哨 AI。

---

# 70. Phase 2 — Vertical Slice

这是第一个真正产品 milestone。

必须实现：

```text
Upload one PDF
       ↓
Parse paper
       ↓
Persist structure
       ↓
Extract basic scientific entities
       ↓
Build basic graph
       ↓
Render interactive graph
       ↓
Click node
       ↓
Show evidence
       ↓
Jump to PDF
```

只有这个完整跑通：

Phase 2 才算完成。

---

# 71. Phase 3 — Scientific Intelligence

加入：

```text
claims

argument graph

equations

figures

assumptions

methods

results

innovation path
```

---

# 72. Phase 4 — First-Principles Engine

加入：

```text
prerequisite decomposition

background retrieval

scientific verification

learning graph

why-needed chain

dynamic expansion
```

---

# 73. Phase 5 — Deep Reading

加入：

```text
translation

section explanations

expert analysis

paper-grounded chat

graph-aware retrieval
```

---

# 74. Phase 6 — Research Context

加入：

```text
reference retrieval

citation network

prior work

review papers

author research lineage

cross-paper knowledge graph
```

---

# 75. Phase 7 — Research Workspace

之后才考虑：

```text
Zotero integration

multiple papers

research project organization

reproduction

notes

personal research graph
```

不要现在重新把旧 workflow 复杂度带进核心应用。

---

# 76. 非目标

当前禁止把时间浪费在：

```text
paper reproduction automation

experiment execution

generic project management

agent society

complex subagent orchestration

publication workflow

paper writing

citation manager replacement
```

这些以后可以成为独立模块。

当前目标只有：

# Build the best possible scientific paper understanding system.

---

# 77. UI 原则

不要做成 AI startup landing page。

不要：

```text
huge gradient
giant cards
excessive rounded panels
random animations
marketing metrics
```

产品视觉参考应该接近：

```text
Obsidian graph
+
scientific PDF reader
+
IDE
+
knowledge explorer
```

特点：

```text
dense

calm

professional

research-oriented

high information efficiency
```

支持：

```text
dark mode
light mode
keyboard navigation
resizable panels
```

---

# 78. Graph Visual Grammar

颜色主要表达：

```text
node type
```

形状可表达：

```text
epistemic class
```

大小表达：

```text
paper relevance
```

边样式表达：

```text
relation type / verification state
```

不要让颜色承担五种语义。

建立正式 visual grammar 文档。

---

# 79. Scientific Inspector

Node Inspector 必须比 tooltip 强大。

包含：

```text
Name

Canonical definition

Explanation

Paper role

Why needed

Prerequisites

Dependents

Equations

Figures

Claims

Evidence

Source location

External references

Verification state

AI provenance
```

---

# 80. Dynamic Expansion

用户点击：

```text
Go deeper
```

不是生成一段更长解释。

应该：

```text
analyze node
↓
identify missing prerequisites
↓
retrieve background evidence
↓
create candidate nodes
↓
verify
↓
persist
↓
expand graph
```

这是核心区别。

---

# 81. Path Intelligence

Graph engine 必须支持：

```text
shortest semantic path

all prerequisites

path to contribution

path from first principle

claim → evidence path

innovation lineage

dependency impact
```

---

# 82. Scientific Consistency

如果系统发现两个节点/来源相互矛盾：

不要自动选择一个。

创建：

```text
CONTRADICTS
```

并标记：

```text
CONFLICTING
```

允许用户查看双方证据。

---

# 83. Uncertainty Is Data

不要把 uncertainty 看成失败。

它必须成为正式字段：

```text
confidence

uncertainty_reason

verification_status
```

这是科研系统的重要组成部分。

---

# 84. Graph Generation 不得基于简单关键词共现

旧版 Jaccard / co-occurrence 可以作为辅助 heuristic。

但不能成为核心科学关系来源。

一个 scientific edge 必须来自：

```text
explicit paper relation

validated semantic extraction

background scientific source

verified derivation

manual confirmation
```

Co-occurrence 只能产生：

```text
candidate association
```

不能产生 scientific dependency。

---

# 85. Human-in-the-Loop

用户可以：

```text
confirm edge

reject edge

edit node

merge nodes

split node

mark verified

mark incorrect

attach evidence
```

AI 不能覆盖人工 verification。

所有人工修改进入 audit log。

---

# 86. Versioning

Node / edge / analysis 修改必须有 version awareness。

至少追踪：

```text
created_at

updated_at

created_by

verification

analysis_version
```

Prompt 更新后重新分析：

不得静默覆盖人工修改。

---

# 87. Exports

未来允许导出：

```text
JSON

GraphML

Markdown study guide

BibTeX references

learning path
```

但 export 永远不是 source of truth。

---

# 88. Performance

Graph 初始渲染必须支持 progressive loading。

不要每次 node click 重新请求整张 graph。

支持：

```text
graph neighborhood query

depth-limited expansion

viewport-aware rendering
```

---

# 89. API Design

可以采用 REST。

例如：

```text
POST /papers

GET /papers/{paper_id}

GET /papers/{paper_id}/document

GET /papers/{paper_id}/graph

GET /papers/{paper_id}/graph/neighborhood

GET /nodes/{node_id}

GET /nodes/{node_id}/evidence

GET /nodes/{node_id}/paths

POST /nodes/{node_id}/expand

GET /claims/{claim_id}

GET /equations/{equation_id}

GET /figures/{figure_id}

POST /papers/{paper_id}/questions

GET /jobs/{job_id}
```

具体 endpoint 可以优化。

不要让 frontend 直接读取数据库。

---

# 90. API Contracts

Frontend 与 backend 共用稳定 schema。

OpenAPI 自动生成客户端或建立一致类型策略。

禁止：

```text
any
dict[str, Any]
```

成为核心 domain contract。

---

# 91. Code Quality

Python：

```text
type hints

Pydantic

lint

format

tests
```

TypeScript：

```text
strict mode

no careless any

typed API

component boundaries
```

避免：

```text
1000-line React component

giant service

god object

business logic in routes

business logic in UI

prompt strings in handlers
```

---

# 92. CI

建立 GitHub Actions。

至少：

```text
backend lint

backend typecheck

backend test

frontend lint

frontend typecheck

frontend test

build
```

不要 require secret 才能跑基本 CI。

AI tests 默认使用 fixtures / mocks。

---

# 93. Local Development

目标：

```text
git clone

configure .env

docker compose up

open browser
```

即可启动基础系统。

开发模式没有 AI Key 时：

系统仍可运行 UI、parser fixture、测试。

不能整个项目因为缺 Key 无法启动。

---

# 94. README

新的 README 必须首先解释：

```text
What PaperGraph is

What problem it solves

Architecture

Quick start

Development

Scientific integrity

Current limitations
```

不要再把 CLI commands 当作产品首页。

---

# 95. 最重要的 Acceptance Criteria

项目的成功不是：

```text
页面能打开
```

也不是：

```text
LLM 能回答问题
```

更不是：

```text
生成了很多节点
```

成功标准是：

给定一篇论文，用户能够：

```text
1. 看到论文科学结构。

2. 看到核心知识网络。

3. 从论文核心概念反向追到理解它所需的基础知识。

4. 从基础知识正向追到论文的方法和结果。

5. 点击任何 paper-derived claim 并定位原文证据。

6. 查看主要公式的意义和来源。

7. 查看 Figure 与 Claim 的对应关系。

8. 理解作者的 Argument Chain。

9. 明确知道论文创新发生在哪里。

10. 清楚地区分原文事实、外部知识和 AI 推理。

11. 对不确定内容看到明确 uncertainty 标记。

12. 在刷新和重新启动后仍保留所有分析状态。
```

只要这十二点还没有完整成立：

不要声称核心产品完成。

---

# 96. 科研质量高于 Demo 效果

出现以下选择：

```text
漂亮但不可靠

vs

简单但可验证
```

永远选择：

```text
简单但可验证
```

出现：

```text
多生成一个节点

vs

保证 provenance
```

优先：

```text
provenance
```

出现：

```text
让 AI 猜

vs

显示 unknown
```

选择：

```text
unknown
```

---

# 97. 不允许出现的项目行为

禁止：

```text
fake graph data

hard-coded demo scientific nodes

fake analysis progress

fake citations

fake page references

mock AI output presented as real paper analysis

placeholder marked complete

unused architecture scaffolding pretending implemented

README claiming unfinished features are supported
```

---

# 98. Codex 工作方式

不要一上来重写整个 repository。

首先：

```text
inspect
↓
reason
↓
document architecture
↓
establish domain model
↓
build vertical slice
↓
test
↓
iterate
```

如果某个旧组件可复用：

复用。

如果不合适：

删除。

不要因为它已经存在就保留。

---

# 99. 每一个 Phase 的完成要求

每完成一个 meaningful phase：

运行：

```text
tests

lint

typecheck

build
```

然后检查：

```text
git diff
```

确保：

```text
no secret

no accidental PDF

no generated junk

no unrelated changes
```

---

# 100. 工作记录

维护：

```text
docs/IMPLEMENTATION_STATUS.md
```

记录：

```text
Implemented

Partially Implemented

Not Implemented

Known Issues

Architecture Decisions

Next Milestone
```

只能记录真实状态。

---

# 101. 第一次执行本 Prompt 时你必须做什么

现在开始。

第一轮先执行完整 repository audit。

不要向用户询问旧 architecture 是否需要保留。

默认：

> 新科研产品质量优先于 V0 compatibility。

除非存在未提交用户数据，否则允许重构。

第一阶段输出并保存：

```text
docs/legacy-audit.md

docs/architecture/SYSTEM.md

docs/architecture/DATA-MODEL.md

docs/architecture/PROVENANCE.md

docs/ontology/SCIENTIFIC-ONTOLOGY.md

docs/architecture/PIPELINE.md

docs/architecture/FRONTEND.md

docs/architecture/EVALUATION.md

docs/IMPLEMENTATION_STATUS.md
```

之后开始建立新的 repository architecture。

---

# 102. 第一个必须真正完成的产品 milestone

不要首先实现 Chat。

不要首先实现 Zotero。

不要首先实现 agent orchestration。

不要首先实现 multi-paper research。

不要首先实现 reproduction。

第一个 milestone 必须是：

# PAPER → GRAPH → EVIDENCE

即：

```text
real PDF
↓
real parsing
↓
real persisted source model
↓
real scientific entities
↓
real graph
↓
real interactive frontend
↓
real evidence anchor
↓
real jump back to PDF
```

只有当这个链完整工作后：

继续开发：

```text
FIRST PRINCIPLES
ARGUMENT GRAPH
INNOVATION GRAPH
EQUATION INTELLIGENCE
FIGURE INTELLIGENCE
```

---

# 103. 第二个核心 milestone

# FIRST PRINCIPLE → PAPER CONTRIBUTION

选择一个真实核心概念。

系统必须能够显示：

```text
first principle
↓
fundamental concept
↓
domain theory
↓
paper prerequisite
↓
paper method
↓
experiment
↓
result
↓
contribution
```

并且每一条关键关系有：

```text
source
confidence
verification status
```

这个链跑通后，产品才真正具有差异化。

---

# 104. 最终产品哲学

系统不是：

# AI tells me what the paper says.

系统应该成为：

# A navigable scientific model of why the paper makes sense.

知识图谱不是 decoration。

它是：

# the primary representation of scientific understanding.

PDF 不是唯一界面。

AI Chat 不是唯一界面。

Markdown 不是数据库。

Summary 不是知识。

Similarity 不是 scientific relation。

LLM confidence 不是 evidence。

真正的核心是：

```text
Knowledge
+
Relations
+
Evidence
+
Reasoning
+
Provenance
+
Uncertainty
```

---

# 105. 开始执行

现在：

1. 检查整个 repository。
2. 检查 git status。
3. 找出旧系统中真正值得保留的部分。
4. 识别错误架构。
5. 写 legacy audit。
6. 写新的 architecture documents。
7. 建立新的 domain models。
8. 建立 database schema。
9. 建立 backend skeleton。
10. 建立 frontend skeleton。
11. 建立第一个 `PAPER → GRAPH → EVIDENCE` vertical slice。
12. 使用真实 PDF fixture 验证。
13. 运行所有测试。
14. 修复失败。
15. 更新 IMPLEMENTATION_STATUS。

除非：

- 可能覆盖未提交用户数据；
- 缺少必须由用户提供的凭据；
- 操作不可逆且 Git 无法恢复；

否则不要在每一步停下来问用户“是否继续”。

进行合理的高级工程判断并继续执行。

不要追求快速生成大量代码。

优先保证：

```text
architecture correctness
scientific integrity
traceability
testability
maintainability
```

最终目标不是把旧模板“升级一下”。

而是把它变成一个：

# research-grade scientific paper knowledge intelligence platform.