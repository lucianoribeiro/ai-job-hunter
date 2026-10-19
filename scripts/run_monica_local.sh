#!/usr/bin/env bash
# Run on user's Ubuntu. CV stays local. No git push, no CV upload.
set -euo pipefail
cd "$(dirname "$0")/.."
CV="${1:-private/profiles/monica/profile.pdf}"
test -r "$CV" || { echo "CV not found: $CV" >&2; exit 1; }
python3 -m src.project_jobs_poc --config config/project_boards.example.json --output data/project_jobs_poc.json
python3 -m src.strategic_companies --config config/strategic_companies.json --output data/strategic_jobs.json
python3 -m src.monica_pipeline --cv "$CV" --projects data/project_jobs_poc.json --check-links --output site/monica-opportunities.json
python3 -m src.monica_page --input site/monica-opportunities.json --output site/monica.html
python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path
raw=json.loads(Path("data/project_jobs_poc.json").read_text())
reg=json.loads(Path("data/strategic_jobs.json").read_text())
out=json.loads(Path("site/monica-opportunities.json").read_text())
print("Project feed:",len(raw.get("jobs",[])),"Regional feed:",len(reg.get("jobs",[])))
print("Matched after screening:",len(out["jobs"]))
print("Geography:",dict(Counter(j.get("location_class") for j in out["jobs"])))
print("Status:",dict(Counter(j.get("application_status") for j in out["jobs"])))
PY
echo "Report ready: site/monica.html"
