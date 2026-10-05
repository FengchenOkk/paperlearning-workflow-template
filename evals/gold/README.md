# Dual-paper source sample

The source PDFs were supplied locally by the user. No PDFs are stored in this gold set. Production extraction receives document bytes only, never these annotations. Gold and prediction review are evaluation inputs used after canonical graph creation.

| Corpus | Source | Gold | Frozen gold SHA-256 |
| --- | --- | --- | --- |
| A | Guo et al., *Hybrid tungsten oxyselenide/graphene electrodes for near-lossless 2D semiconductor phase modulators*, 2026; supplied 10-page article | 17 items; 10 quantity occurrences; figures 1, 3, 4; no main-article numbered equation found | `b2cf5c09d52627a92ebdd17209ca9e51f3af85599896731336a4a00427ec0109` |
| B | Li et al., *Approaching the quantum limit in two-dimensional semiconductor contacts*, 2023; supplied 19-page article with extended data | 16 items; 11 quantity occurrences; figures 1–3; equation 1 | `f1647451ea439c4b4b29b31f41bc1ca7a368ada89d40d74fceebf019c96cba63` |

Annotations were frozen before baseline scoring and changes. Current-model source review is **MODEL_SOURCE_REVIEW**, with all human decisions **PENDING**. This model is also implementing the pipeline; these scores are not an independent human or held-out scientific evaluation. No paper-derived object was marked VERIFIED.

Human review bundles: [A](paper-a/REVIEW.md), [B](paper-b/REVIEW.md). Protocol: [fixed gate](../../docs/evaluation/PAPER-GRAPH-EVIDENCE-GATE.md). Reports: [A](../reports/dual-paper/current-a.json), [B](../reports/dual-paper/current-b.json). Original PDF hashes are in gold and reports; mismatching editions fail evaluation.

From `backend/`, with explicit local source paths:

```powershell
..\.venv\Scripts\python.exe -m scripts.evaluate_source_gate --pdf $paperPathA --gold ../evals/gold/paper-a/gold.json --adjudication ../evals/gold/paper-a/prediction-review.json --output ../.runtime/my-source-gate/a.json
..\.venv\Scripts\python.exe -m scripts.evaluate_source_gate --pdf $paperPathB --gold ../evals/gold/paper-b/gold.json --adjudication ../evals/gold/paper-b/prediction-review.json --output ../.runtime/my-source-gate/b.json
..\.venv\Scripts\python.exe -m scripts.run_source_gate_e2e --pdf-a $paperPathA --pdf-b $paperPathB
```

Use a fresh output stem for each run. The runner creates isolated migrated application storage, the same normal upload/worker path, then scores its graph. It does not copy originals into evaluation fixtures. Runtime storage and screenshots are ignored. The initial Desktop PDF paths disappeared during this session; subsequent validation used the previously ingested local application documents with identical pinned hashes. Reproduction requires the same local bytes, not an assumed Desktop path or a public download.
