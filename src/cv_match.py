"""Private local CV keyword comparison. Never uploads or persists CV contents."""
import argparse
import json
from pathlib import Path
from src.opportunity_assessment import assess_opportunity
from src.hunter import DATA

def compare(cv_text, jobs):
    return [{"title": j.get("title"), "company": j.get("company"), "url": j.get("url"),
             "assessment": assess_opportunity(j, cv_text)}
            for j in jobs if isinstance(j, dict)]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cv", type=Path, required=True, help="Local UTF-8 CV text file (never committed)")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    cv = args.cv.read_text(encoding="utf-8")
    source = DATA / "applications.json"
    queue = json.loads(source.read_text(encoding="utf-8")) if source.exists() else {}
    result = compare(cv, list(queue.values()))
    document = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(document + "\n", encoding="utf-8")
    else:
        print(document)

if __name__ == "__main__":
    main()
