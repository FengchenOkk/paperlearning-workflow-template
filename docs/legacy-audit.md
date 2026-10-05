# V0 audit and transition to PaperGraph

Audit date: 2026-10-05. Baseline: `118a9d2`.

The repository currently implements a Python/PyYAML filesystem workflow, not an application. `wf.py` dispatches literature, task, registry, graph and Zotero modules. Scientific state lives in YAML/Markdown; JSON graphs are derived views. There is no database, HTTP server, PDF parser or frontend. Tests use isolated temporary projects and simulated providers. Vendor ARS is third-party code, not part of the new application.

| Module | Decision | Reason and destination |
| --- | --- | --- |
| tools/storage.py | REUSE | Atomic writes are useful; new document storage has a separately typed boundary. |
| tools/adapters.py | REWRITE | Environment-only credentials and explicit execution remain good patterns; free-text output cannot be a scientific domain contract. Future structured providers must validate schema and evidence. |
| tools/tasks.py | REWRITE | Draft/review and stale-input safeguards inform scientific verification; filesystem task orchestration stays outside the application. |
| tools/registry.py | REWRITE | Stable identity and hash checks are retained as principles; DB IDs replace paths in the new application. |
| tools/knowledge.py | REMOVE from application | Jaccard/co-occurrence cannot establish scientific dependency. No runtime imports into PaperGraph. |
| tools/literature.py, study.py, wf.py | REMOVE from application | File templates and CLI progress are unrelated to the new core domain. Existing code remains isolated for user data access. |
| tools/zotero.py | REWRITE later | Read-only policy is useful; research workspace integrations follow the first product milestones. |
| workflow/, config/ | REMOVE from application | Existing local profiles and contracts are protected. No ingestion of local configuration or credentials. |
| projects/, prompt/ | PRESERVE | Untracked user research and prompts must not be overwritten or automatically migrated. |
| workflow/vendor/ | REMOVE from application | No third-party execution or dependency on ARS. Preserve original files. |
| tests/ | REUSE as regression suite | Run the original suite; new app tests live under backend/tests. |

REMOVE means excluded from the new runtime, not deletion of user-accessible historical tooling. Compatibility does not constrain the new DB graph. Historical YAML and the application DB represent separate workspaces; no implicit synchronization or competing copies of application graph state.

Risks: local `.env` and private model profiles exist; do not read secret values. Untracked `projects/2d-semiconductor-contacts/` and `prompt/` existed before work. No research migration, model invocation, scientific review record or paper-progress update is authorized by merely importing a PDF. Public golden PDF downloads are ignored, with URL/hash metadata tracked instead. PyMuPDF's AGPL/commercial licensing requires a deployment licensing decision before distributing a proprietary service.
