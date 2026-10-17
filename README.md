# AI Job Hunter

Automated, **review-first** job discovery for international QA opportunities.

## What it does
- Fetches public jobs from Remotive and Arbeitnow APIs.
- Scores QA Engineer, QA Lead, QA Manager and test automation opportunities.
- Separates full-time jobs from remote, flexible freelance/contract roles (~2 hours/day).
- Prioritizes USD compensation where explicitly provided, without inventing salary or working hours.
- Deduplicates job postings, produces CSV and Markdown reports.
- Runs daily with GitHub Actions, or manually from the Actions tab.

**It does not submit applications, log into LinkedIn, or send CVs automatically.** Apply only after manual review. Public job board data may be stale; verify details at the source.

## Run locally

```bash
python -m src.hunter
python -m unittest discover -s tests -v
```

Output: `data/jobs.csv` and `data/report.md`.

## Automated runs

Go to **Actions → Discover QA jobs → Run workflow**, or wait for the scheduled daily run. Results are uploaded as workflow artifacts and committed to `data/` on `main`.

## Configuration
Modify `config.json` to change keywords and preferences. Ranking is heuristic, not an AI model, and does not use paid APIs.

## Privacy and safety
Never put your CV, credentials, API keys or private contact details in this public repo. The pipeline only fetches public job ads and creates reports.
