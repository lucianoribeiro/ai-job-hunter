# Project-management job-board integration POC

This is an **isolated** read-only proof of concept, independent of the existing QA discovery workflow.

## How to run
```bash
python -m unittest discover -s tests -v
python -m src.project_jobs_poc --config config/project_boards.example.json --output data/project_jobs_poc.json
```

Edit a **local copy** of the example config to add actual employer board slugs after finding each employer's public Greenhouse or Lever career-board URL. The example company token is illustrative; the Lever token is a publicly documented example. Do not consider sample tokens evidence of useful opportunities.

Greenhouse GET: `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true`
Lever GET: `https://api.lever.co/v0/postings/{slug}?mode=json&skip=0&limit=100`

The POC does not submit applications or scrape LinkedIn. It does not verify whether the job is still open beyond its appearance in the board feed. Remote description mentions are classified separately from an explicitly remote location. Published date is **not** inferred from Greenhouse updated_at or Lever payloads. Brazil eligibility is never inferred. Project manager titles may include technical positions, so results require manual review.

## Commercial viability gates
- Record boards configured, boards returning valid responses, fetched listings, title matches, and unique job URLs.
- Manually label at least 30 returned results for relevance, Brazil eligibility, freshness, and presence of an actionable application page.
- Evaluate precision = relevant/inspected and coverage = relevant employers with accessible feeds / candidate employers surveyed.
- Do not claim country eligibility, salary, recruiter contact, or publication date without evidence.
- Check provider terms, attribution, rate limits, and any redistribution restrictions before publicly commercializing job data.

LinkedIn recruiter post support can be added separately as **user-provided URL/text import**, without automated LinkedIn browsing or bypassing access restrictions.
