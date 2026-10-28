"""Standalone Agent Reach public-search adapter for the isolated Lab.

Produces structured evidence JSON without changing the production job feed.
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from src.agent_reach_hidden import QUERIES, structured_results


def discover(executable: str = "agent-reach") -> dict:
    if not shutil.which(executable):
        return {"status": "unavailable", "records": [], "errors": ["Agent Reach CLI not installed"]}
    records, errors = [], []
    for query in QUERIES:
        try:
            result = subprocess.run(
                [executable, "web", "search", query],
                capture_output=True, text=True, timeout=40, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append({"query": query, "error": str(exc)[:200]})
            continue
        if result.returncode:
            errors.append({"query": query, "error": (result.stderr or "search failed")[:200]})
            continue
        parsed = structured_results(result.stdout[:120000])
        if not parsed:
            errors.append({"query": query, "error": "No structured results"})
        records.extend({**item, "search_query": query} for item in parsed)
    return {"status": "complete" if not errors else "partial",
            "records": records, "errors": errors, "queries": list(QUERIES)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/hidden-opportunities-lab/source_records.json"))
    parser.add_argument("--diagnostics", type=Path, default=Path("artifacts/hidden-opportunities-lab/source_diagnostics.json"))
    args = parser.parse_args()
    result = discover()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.diagnostics.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result["records"], ensure_ascii=False, indent=2), encoding="utf-8")
    args.diagnostics.write_text(json.dumps({k: v for k, v in result.items() if k != "records"}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "source_records": len(result["records"]), "errors": len(result["errors"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
