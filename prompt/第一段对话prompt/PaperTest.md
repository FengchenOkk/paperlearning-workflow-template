# NEXT MILESTONE

## Dual-Paper Scientific Quality Gate + First-Principles Pilot

The architecture audit/correction phase is complete.

Do NOT perform another broad architecture redesign.

Do NOT restart the project.

Do NOT add unrelated product features.

The current architecture is now the working foundation unless this milestone exposes a concrete blocking defect.

We are moving from:

> architecture correctness

to:

> scientific-system correctness.

---

# 0. The two real evaluation papers

Use these TWO real scientific papers as the primary evaluation corpus for this milestone.

## Paper A — Integrated photonics / 2D optoelectronics

**Hybrid tungsten oxyselenide/graphene electrodes for near-lossless 2D semiconductor phase modulators**

Shi Guo et al.

Light: Science & Applications, 2026.

This paper represents a scientific stack involving approximately:

```text
2D materials
graphene
TMDs
carrier doping
Fermi level
optical absorption
Pauli blocking
electro-optic response
waveguides
evanescent fields
effective refractive index
microring resonators
phase modulation
FDTD
integrated photonics
```

These are evaluation-domain expectations only.

Do NOT hard-code this list as graph output.

---

## Paper B — 2D semiconductor electronics / contacts

**Approaching the quantum limit in two-dimensional semiconductor contacts**

Weisheng Li et al.

Nature, 2023.

This paper represents a substantially different scientific stack involving approximately:

```text
2D semiconductors
MoS2
metal-semiconductor contacts
quantum contact resistance
carrier concentration
van der Waals gap
Schottky barriers
tunnelling
orbital hybridization
DFT
density of states
Bader charge transfer
TLM
ohmic contacts
short-channel FETs
```

Again:

these are evaluation-domain expectations only.

They must NOT be inserted into the graph simply because this prompt lists them.

---

# 1. Why two papers are required

The goal is NOT merely to successfully parse two PDFs.

The two papers intentionally belong to related but substantially different research directions.

Paper A:

```text
2D materials
+
photonics
+
electro-optic modulation
```

Paper B:

```text
2D materials
+
electronic transport
+
metal-semiconductor contacts
```

A valid scientific architecture must handle both using the SAME:

```text
document model

scientific ontology

canonical graph

provenance model

evaluation framework

first-principles engine architecture
```

Do not create paper-specific logic.

Do not create photonics-specific branches in the core parser.

Do not create semiconductor-contact-specific branches in the canonical ontology.

Domain-specific knowledge belongs in data and verified knowledge sources, not hardcoded application logic.

---

# 2. This milestone has TWO gates

Do them in order.

---

# GATE A

# REVIEWED PAPER → GRAPH → EVIDENCE

This gate must be completed before First-Principles expansion.

---

# GATE B

# FIRST PRINCIPLE → PAPER CONTRIBUTION PILOT

Only begin this after Gate A passes.

Do NOT claim a complete First-Principles engine after this milestone.

This phase is a scientifically reviewed pilot.

---

# ============================================================
# GATE A — REVIEWED PAPER → GRAPH → EVIDENCE
# ============================================================

# 3. Process both papers through exactly the same production pipeline

For BOTH papers use:

```text
REAL PDF
↓
DOCUMENT PARSER
↓
SOURCE MODEL
↓
SCIENTIFIC ENTITY EXTRACTION
↓
TYPED SCIENTIFIC OBJECTS
↓
CANONICAL GRAPH
↓
EVIDENCE
↓
SOURCE ANCHOR
↓
ORIGINAL PDF
```

Do not preload graph results.

Do not handcraft production graph nodes.

Do not write special extraction rules containing paper titles, author names or known conclusions.

Gold truth belongs only in:

```text
evals/
tests/
```

and must never be consumed as production analysis input.

---

# 4. Preserve both PDFs as local evaluation inputs

Do NOT commit user-provided PDFs to Git unless their redistribution rights are independently confirmed.

The repository may contain:

```text
manifest
SHA-256
metadata
expected source locations
gold annotations
```

but the original PDF files should remain ignored/local where appropriate.

Do not copy private or user-owned research files into test fixtures automatically.

---

# 5. Build an independent gold dataset

Create a small, high-quality human-reviewable gold dataset for BOTH papers.

Do not create hundreds of annotations.

Quality is more important than volume.

Create something equivalent to:

```text
evals/gold/
    paper-a/
    paper-b/
```

For each paper identify a carefully selected set of:

```text
research problem

central claims

important definitions

major methods

important experimental/simulation statements

important results

numbered equations where present

important figures and captions

important quantitative values

important assumptions/limitations where explicitly stated
```

Each gold item must contain:

```text
paper identifier

object type

exact source wording or normalized representation

page

source span/block

section where resolvable

figure/equation number when applicable

numbers

units

expected epistemic status
```

Gold annotations must come from the actual paper.

Do NOT use general scientific knowledge to fill missing paper statements.

---

# 6. Use scientifically meaningful gold examples

For Paper A, the gold set should cover multiple parts of the scientific argument, for example areas such as:

```text
research motivation

TOS-induced graphene doping

suppression of graphene optical absorption

device architecture

electro-optic modulation

effective-index/loss behavior

comparison of electrode configurations

modulation-efficiency result
```

These are annotation targets, not hardcoded graph outputs.

---

For Paper B, cover distinct areas such as:

```text
quantum contact limit

vdW contact limitation

Sb(0112)-MoS2 band hybridization

DFT evidence

charge transfer

contact-resistance measurement

TLM interpretation

evidence for ohmic behaviour

device-performance consequence
```

Again:

annotation targets only.

---

# 7. Equation evaluation

The papers have very different mathematical styles.

The system must tolerate this.

Paper B contains an explicit quantum-limit contact-resistance relation near the beginning of the paper.

Paper A may contain fewer important numbered analytical equations in the main article and may rely more strongly on device physics, extracted quantities, simulations and supplementary derivations.

Therefore:

DO NOT enforce an arbitrary identical equation quota.

Instead evaluate:

```text
equation detection when equations exist

equation number

source expression

symbol integrity

source location

paper-provided meaning
```

If no appropriate numbered equation exists in a selected section:

record that fact.

Do not invent one.

---

# 8. Figure evaluation

Select several scientifically important figures from EACH paper.

Verify separately:

```text
figure number

caption

source page

caption anchor

surrounding explanatory text
```

Keep these channels separate:

```text
CAPTION_EXPLICIT

PAPER_TEXT_EXPLICIT

VISUAL_OBSERVATION

AI_INTERPRETATION
```

The first two may be paper-grounded.

The latter two require their own provenance/status.

Never upgrade AI interpretation to paper fact.

---

# 9. Quantitative integrity

Scientific numbers must receive special validation.

Check selected values for:

```text
number

sign

decimal position

scientific notation

unit

prefix

context
```

Examples include quantities such as:

```text
contact resistance

carrier density

energy/Fermi-level shifts

optical wavelength

Vπ·L

extinction-ratio changes

barrier widths

temperature

device current
```

Do not trust parsed text merely because a numeric token exists.

Gold evaluation must compare the complete:

```text
value + unit + semantic meaning
```

---

# 10. Measure extraction quality

Do not report:

```text
"the pipeline appears good"
```

Create actual evaluation metrics for the gold set.

At minimum report:

```text
entity extraction precision

entity extraction recall

type classification accuracy

source-anchor correctness

page-location correctness

figure-caption association accuracy

equation localization accuracy where applicable

quantitative value integrity

provenance coverage
```

Also count:

```text
unsupported scientific edges

fabricated paper facts

paper statements without provenance

duplicate candidate entities

incorrectly merged entities
```

---

# 11. Define thresholds BEFORE tuning

Before changing extraction specifically to improve these two papers:

document the acceptance criteria.

Create:

```text
docs/evaluation/PAPER-GRAPH-EVIDENCE-GATE.md
```

Specify:

```text
metric

measurement procedure

pass condition

failure condition

known limitations
```

Do NOT silently change thresholds after seeing results.

If the gate fails:

report failure and improve the generic pipeline.

Do not weaken the metric merely to mark the milestone complete.

---

# 12. Zero-tolerance conditions

Regardless of statistical thresholds, the following conditions automatically FAIL Gate A:

```text
fabricated paper statement

fabricated equation

fabricated figure interpretation presented as source fact

fabricated numeric value

fabricated source location

accepted scientific edge based only on similarity/co-occurrence

verified object without valid provenance

gold data leaking into production analysis

paper-specific hardcoded extraction logic
```

---

# 13. Attribution is not validity

Continue enforcing:

```text
SOURCE_ATTRIBUTION
```

separately from:

```text
SCIENTIFIC_VALIDITY
```

A source anchor proves:

> the paper says this here.

It does NOT prove:

> this scientific conclusion is objectively true.

The evaluation report must keep these separate.

---

# 14. Cross-paper generalization test

The most important reason for using two papers is to detect accidental overfitting.

After both pipelines run:

compare:

```text
node types used

edge types used

parser failures

source-anchor failures

entity duplicates

unsupported relations

domain-specific assumptions
```

Answer:

> Did any component work only because Paper A resembles the previous photonics assumptions?

and:

> Did any component work only because Paper B resembles a conventional electronic-device paper?

Create:

```text
docs/evaluation/CROSS-DOMAIN-GENERALIZATION.md
```

---

# 15. Graph integrity after real papers

Run integrity validation for both real graphs.

Check:

```text
orphan nodes

invalid source anchors

invalid edge endpoints

missing provenance

duplicate canonical entities

unexpected prerequisite cycles

unsupported VERIFIED state

subtype inconsistencies

figure/caption mismatches

equation/source mismatches
```

All unresolved integrity errors must be documented.

---

# 16. Frontend validation

For BOTH papers manually or automatically verify:

```text
open paper

graph renders

select node

node inspector opens

scientific type is correct

epistemic status visible

evidence visible

select evidence

PDF goes to correct page

correct source block is highlighted

reverse source → graph relation works

refresh

state remains persistent
```

Do not validate only one paper.

---

# 17. Gate A deliverables

Create/update:

```text
docs/evaluation/PAPER-GRAPH-EVIDENCE-GATE.md

docs/evaluation/CROSS-DOMAIN-GENERALIZATION.md

docs/evaluation/PAPER-A-RESULTS.md

docs/evaluation/PAPER-B-RESULTS.md

evals/gold/...

docs/IMPLEMENTATION_STATUS.md
```

The report must clearly say either:

```text
GATE A: PASS
```

or:

```text
GATE A: FAIL
```

No ambiguous "mostly complete".

If it fails:

fix the generic source/graph/evidence pipeline and rerun.

---

# ============================================================
# GATE B — FIRST PRINCIPLE → PAPER CONTRIBUTION PILOT
# ============================================================

Only begin Gate B if Gate A passes.

---

# 18. Purpose of Gate B

Do NOT attempt to create the complete knowledge graph for both papers down to every first principle.

That would produce a large unverified AI graph.

Instead:

select ONE central scientific concept from EACH paper.

Build one deeply reviewed prerequisite/consequence path for each.

This tests whether the architecture can support a real First-Principles engine across different scientific domains.

---

# 19. Preferred pilot concepts

Unless analysis shows a better central concept, use:

## Paper A

A concept around:

```text
effective refractive index
```

or the immediately surrounding electro-optic phase-modulation mechanism.

Reason:

it connects:

```text
material optical response
→ guided optical mode
→ phase change
→ microring resonance
→ device modulation
```

Do NOT hard-code this path.

The system must reconstruct and verify it.

---

## Paper B

A concept around:

```text
quantum-limit contact resistance
```

or the central physical mechanism connecting band hybridization to low contact resistance.

Reason:

it connects:

```text
quantum transport
→ contact physics
→ interface electronic structure
→ charge injection
→ measured contact resistance
→ transistor performance
```

Again:

this is a target for analysis.

Not a preloaded answer.

---

# 20. Build candidate prerequisites recursively

For the selected concept:

perform:

```text
CORE PAPER CONCEPT
↓
identify immediate prerequisites
↓
generate candidate prerequisite relationships
↓
retrieve or identify scientific support
↓
review
↓
expand another level only when necessary
```

Do NOT generate the entire path in one LLM call.

Each edge must be individually representable as:

```text
source node

target node

relation

why needed

source/provenance

epistemic status

verification state
```

---

# 21. Distinguish three knowledge origins

Every prerequisite node must clearly be one of:

```text
PAPER_DERIVED

EXTERNAL_SCIENTIFIC_KNOWLEDGE

AI_DERIVATION
```

Never mix them.

For external scientific knowledge:

record source provenance.

For AI derivation:

explicitly label it.

For current paper content:

anchor it back to the PDF.

---

# 22. No fake First-Principles chain

This is forbidden:

```text
LLM generates 15 plausible prerequisite nodes
→ saves all as graph
→ calls it First Principles
```

The correct process is:

```text
candidate
→ evidence
→ review
→ accepted/rejected
→ expansion
```

Unverified prerequisites stay:

```text
CANDIDATE
```

---

# 23. Task-relative stopping rule

For BOTH pilot paths explicitly define:

```text
why decomposition stops here
```

A node may be a stopping point if:

```text
it is assumed knowledge for the chosen target reader

OR

it is an accepted foundational law/definition for this task

OR

further decomposition would not materially improve understanding of the paper
```

Do not recursively reduce everything to arithmetic/set theory.

Store the stopping reason.

---

# 24. Why-needed semantics

Every accepted prerequisite edge must support:

```text
Why does the learner need this concept to understand the next node?
```

This explanation must be relationship-specific.

Not generic textbook prose.

For example the UI should eventually support:

```text
Why do I need this?
```

and return an explanation grounded in the path.

---

# 25. Forward path must also work

First-Principles is not only backward decomposition.

Once a prerequisite path is accepted, the system must also traverse forward:

```text
foundation
↓
intermediate concept
↓
paper concept
↓
paper method
↓
paper result
↓
paper contribution
```

The system must be able to answer:

```text
Where is this foundational concept ultimately used in the paper?
```

---

# 26. Do not force identical scientific depth

The two papers require different foundations.

Paper A may descend toward concepts involving:

```text
electromagnetism
optical modes
complex refractive index
solid-state optical transitions
```

Paper B may descend toward concepts involving:

```text
quantum transport
electronic band structure
metal-semiconductor junctions
tunnelling
```

That difference is desired.

The ontology and engine should support both without special-case application code.

---

# 27. Evaluate First-Principles quality

For the two pilot chains measure/review:

```text
prerequisite correctness

edge semantics correctness

evidence availability

why-needed usefulness

stopping-rule quality

duplicate entity handling

path continuity

paper relevance

unsupported inference count
```

Do NOT use graph size as a quality metric.

More nodes are not better.

---

# 28. First-Principles UI pilot

Only after verified relationships exist:

allow the frontend to display the two pilot learning paths.

For each node allow:

```text
What is this?

Why do I need it?

Where does it come from?

What depends on it?

Where is it used in this paper?

Show evidence.
```

Unverified candidate nodes must look visibly different from reviewed nodes.

---

# 29. Required demonstration

Gate B is successful only if the repository can demonstrate BOTH:

```text
Paper A:
foundation
→ ...
→ selected photonics concept
→ paper mechanism
→ result/contribution
```

and:

```text
Paper B:
foundation
→ ...
→ selected contact-physics concept
→ paper mechanism
→ result/contribution
```

with scientific provenance and review state on every substantive relationship.

The exact paths must emerge from the analysis.

Do not preload paths from this prompt.

---

# 30. Do NOT claim complete First-Principles Engine yet

Even if both pilots succeed:

status should be something equivalent to:

```text
First-Principles Engine:
PARTIAL / PILOT VALIDATED
```

not:

```text
IMPLEMENTED
```

A complete claim requires broader scientific evaluation across additional domains and papers.

---

# ============================================================
# ENGINEERING RULES
# ============================================================

# 31. No broad feature expansion

During this milestone do NOT add:

```text
generic chat

Zotero

multi-paper research workspace

DeepSeek orchestration

paper reproduction

paper writing

recommendation engine

citation manager

collaboration

cloud deployment
```

unless strictly required to test the two gates.

---

# 32. No architecture churn without evidence

If a current architectural component works:

keep it.

If the real papers expose a concrete defect:

fix it.

Do not replace technology simply because another library appears more sophisticated.

Document any necessary architectural correction in an ADR.

---

# 33. Human review must remain explicit

Do not silently simulate human verification with an LLM.

A model can propose:

```text
candidate relationship
candidate interpretation
candidate prerequisite
```

but cannot mark itself independently human-verified.

Keep machine review and human review distinguishable.

---

# 34. External scientific sources

If external literature/background retrieval is required for Gate B:

use a provider abstraction.

Record:

```text
title
authors
year
identifier/DOI where available
source location
retrieval date
what statement it supports
```

Do not cite an external source merely because the title sounds relevant.

---

# 35. Scientific uncertainty

The correct answer may be:

```text
UNKNOWN

INSUFFICIENT_EVIDENCE

CONFLICTING

NOT_ASSESSED
```

These are valid scientific outcomes.

Do not force completeness.

---

# 36. Final tests

Before reporting completion run all applicable:

```text
backend tests

frontend tests

Ruff

mypy

frontend lint

frontend typecheck

production build

contract drift checks

database migration checks

graph integrity checks

browser E2E
```

Run real-paper tests for BOTH papers.

---

# 37. Final report

At completion provide:

## Gate A

```text
PASS / FAIL
```

with metrics.

## Paper A

```text
extraction quality
source quality
known errors
```

## Paper B

```text
extraction quality
source quality
known errors
```

## Cross-domain generalization

Explain whether one generic pipeline genuinely handled both.

## Gate B

```text
PASS / FAIL / PARTIAL
```

Show the two reviewed pilot knowledge paths.

## Remaining scientific risks

Explicitly list them.

## Next recommended milestone

Recommend only ONE bounded next milestone.

---

# 38. Update status truthfully

Update:

```text
docs/IMPLEMENTATION_STATUS.md
```

Do not mark:

```text
scientific reasoning

first-principles engine

argument graph

innovation graph
```

as complete unless their actual evaluation gates support that claim.

---

# 39. Core principle

The purpose of this milestone is NOT:

> make the graph bigger.

The purpose is:

> establish that the graph represents real scientific structure, across two different scientific subdomains, with traceable evidence and explicit uncertainty.

The quality hierarchy is:

```text
correct small graph
>
large plausible graph

verified relationship
>
high-confidence LLM guess

unknown
>
fabrication
```

Proceed with Gate A first.

Do not begin Gate B until Gate A has passed.