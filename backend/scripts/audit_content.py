"""Inventory lexical audit hits without copying research text or credentials."""

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "docs/audit/content-occurrences.json"
PATHS = [
    "backend",
    "frontend",
    "packages",
    "docs",
    "evals",
    "infra",
    "prompt",
    "tools",
    "tests",
    "workflow",
    "config",
    "projects/_template",
    "vendor",
    ".github",
    "AGENTS.md",
    "README.md",
    "ROADMAP.md",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    ".env.example",
]
PATTERN = "mock|fake|demo|sample|placeholder|hardcoded|TODO|fixture"


def classification(path: str, term: str, line: str) -> str:
    if (
        path.startswith(("backend/tests/", "tests/", "evals/"))
        or ".test." in path
        or path == "backend/scripts/run_e2e.py"
    ):
        return "TEST_OR_GOLD_INPUT"
    if path.startswith(("vendor/", "workflow/vendor/")):
        return "THIRD_PARTY_REFERENCE_NOT_APP_RUNTIME"
    if path.startswith("prompt/"):
        return "PREEXISTING_REQUIREMENT_DOCUMENT_NOT_EXECUTABLE_AUTHORITY"
    if path.startswith(("workflow/", "projects/_template/", "config/")) or path == ".env.example":
        return "LEGACY_TEMPLATE_OR_WORKFLOW"
    if path.startswith("tools/"):
        return "LEGACY_CODE_ISOLATED_FROM_APP"
    if path.startswith("docs/") or path in {"README.md", "AGENTS.md", "ROADMAP.md"}:
        return "DOCUMENTATION_OR_EXPLICIT_GAP"
    if path == "frontend/src/GraphCanvas.tsx" and term.casefold() == "sample":
        return "LAYOUT_PARAMETER_NOT_SCIENTIFIC_DATA"
    if path.startswith("frontend/") and term.casefold() == "placeholder":
        return "INPUT_HINT_NOT_SCIENTIFIC_OUTPUT"
    if path == "backend/papergraph/extraction.py" and "demonstrat" in line.casefold():
        return "AUTHOR_WORDING_RULE_NOT_DEMO_DATA"
    if path.endswith(("package-lock.json", "contracts.ts", ".schema.json")):
        return "GENERATED_DEPENDENCY_OR_CONTRACT"
    if path.startswith("backend/scripts/"):
        return "AUDIT_OR_EVALUATION_UTILITY"
    return "SOURCE_COMMENT_CONFIGURATION_OR_BOUNDARY_REVIEW"


def main() -> None:
    command = [
        "rg",
        "--json",
        "--ignore-case",
        PATTERN,
        "-g",
        "!*.local.yaml",
        "-g",
        "!docs/audit/content-occurrences.json",
        *[path for path in PATHS if (ROOT / path).exists()],
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, encoding="utf-8", check=False)
    if result.returncode not in {0, 1}:
        raise RuntimeError("Content scan failed; no complete inventory produced")
    entries = []
    for raw in result.stdout.splitlines():
        record = json.loads(raw)
        if record["type"] != "match":
            continue
        data = record["data"]
        path = data["path"]["text"].replace("\\", "/")
        line = data["lines"]["text"]
        for match in data["submatches"]:
            term = match["match"]["text"]
            entries.append(
                {
                    "path": path,
                    "line": data["line_number"],
                    "byte_column": match["start"] + 1,
                    "term": term,
                    "classification": classification(path, term, line),
                    "line_sha256": hashlib.sha256(line.encode()).hexdigest(),
                }
            )
    entries.sort(
        key=lambda value: (str(value["path"]), int(value["line"]), int(value["byte_column"]))
    )
    inventory = {
        "date": "2026-10-05",
        "pattern": PATTERN,
        "paths": PATHS,
        "exclusions": [
            "ignored private originals, PDFs, credentials, research projects other than _template",
            "runtime data, dependencies, build/cache outputs; this inventory itself",
        ],
        "counts": dict(Counter(str(entry["classification"]) for entry in entries)),
        "occurrences": entries,
    }
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"occurrences": len(entries), "counts": inventory["counts"]}))
    runtime = [
        entry
        for entry in entries
        if str(entry["path"]).startswith(("backend/papergraph/", "frontend/src/"))
        and ".test." not in str(entry["path"])
        and not str(entry["path"]).endswith("contracts.ts")
    ]
    print(json.dumps(runtime, ensure_ascii=False))


if __name__ == "__main__":
    main()
