# Hidden Opportunities Lab — isolated prototype

This is a separate experimental module, not a replacement for the existing AI Job Hunter.

## Safe boundary

- No changes to `src/hunter.py`, `src/unified_jobs_dashboard.py`, GitHub Pages, database or existing scheduled collectors.
- No merge or deployment is needed to test this module.
- It accepts structured PUBLIC source records and does not use LinkedIn authentication.
- A qualifying signal is **not** a confirmed or unadvertised job opening.

## Run

```bash
python -m unittest tests.test_hidden_opportunities_lab -v
python -m src.hidden_opportunities_lab --input public_evidence.json --output-dir artifacts/hidden-opportunities-lab
```

Input JSON is a list of objects, for example:
```json
[{"url":"https://www.linkedin.com/posts/company-example","company":"Example","excerpt":"We're hiring a quality engineering lead.","published_at":"2026-10-27"}]
```

Results are saved as `report.json` and `report.html` in the selected output directory, not in the existing published job feed.

## Follow-up milestones

1. Add isolated public Agent Reach adapter that emits a structured evidence JSON list.
2. Verify each evidence link and publication date using public sources, then compare against all public job feeds.
3. Add persistent evidence history and separately tracked outreach status.
4. Only after evidence quality is proven, design a separately gated, opt-in UI. No changes to existing general-job cards.
