# Research coordination

These rules describe Codex's orchestration. If DSH reads this file, it is the task worker: follow the assigned task, do not launch another DSH or Codex agent, and do not write the final project synthesis.

Codex/GPT is the lead agent for this project. It defines the research question, chooses methods, integrates evidence, checks sources, implements and verifies code, and writes the final answer.

DeepSeek Harness (DSH) is an external task worker invoked with `node features/F-001-deepseek-worker/scripts/dsh-task.mjs --task-file <path>`. It is not a Codex-native subagent thread. Use it only for a bounded, independent task whose output Codex can inspect: candidate literature leads, structured extraction from supplied material, alternative hypotheses, or a second-pass critique. When the user asks to use DSH, delegate a suitable bounded task. Do not delegate for routine edits or when no independent work is useful.

Before invoking DSH, prepare a task file that states the question, input locations, allowed actions, expected output, and source requirements. By default, instruct DSH to read and analyze only. Do not include API keys, private credentials, or unpublished sensitive material unless the user authorized sending it to DeepSeek. DSH is an external process with its own tools, and prompt instructions alone are not a permission boundary.

After DSH finishes, inspect `answer.md` and, when needed, `events.jsonl` under the reported run directory in `features/F-001-deepseek-worker/.runtime/runs/`. Verify every paper, DOI, quotation, numerical result, and claim against its primary source before using it. Treat model output as leads, not evidence. Codex owns the final synthesis and marks uncertainty explicitly. If DSH fails or is unavailable, continue with Codex and report the limitation.

Research rules for both agents: distinguish observed evidence from inference; record provenance for each material claim; never invent citations or results; keep reproducible code, data transformations, and assumptions reviewable.

This repository is a public workflow template with a local private instance. Never remove ignore rules or stage `PROJECT.md`, planning state files, `workstreams/WS-*/`, real research/output material, Zotero local configuration/indexes/reading packets, DSH tasks/runs, PDFs, data, credentials, or machine paths merely to make them visible in the public repository. Add reusable behavior through public scripts, templates, tests, `*.example.*` files, and sanitized documentation. If local instance files are missing, run `node planning/scripts/setup-local.mjs`; it must not overwrite existing private files.

For substantial new work, read `PROJECT.md` and `planning/WORKFLOW.md` first. Put each reusable capability in its own `features/F-###-slug/` directory and each research topic or outcome-focused initiative in its own `workstreams/WS-###-slug/` directory. Keep status and next action current. Update `planning/BACKLOG.md` when tasks are added or completed. Record only cross-cutting or difficult-to-reverse decisions in `planning/DECISIONS.md`. Do not create parallel task lists that compete with the backlog.
