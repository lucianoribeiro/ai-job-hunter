# LinkedIn alerts ingestion (opt-in)

This feature **does not** connect to LinkedIn or Gmail directly. It imports a local
`.eml` export that you explicitly supply, extracts direct LinkedIn job links,
removes URL tracking query parameters, and discards sender/recipient details,
email headers and message contents.

## Use

1. In LinkedIn, create job alerts for remote QA Engineer, QA Lead, QA Manager,
   SDET and part-time freelance QA jobs.
2. Export one or more received alerts as `.eml` files to a local directory.
3. From your local clone of the repo, run:

```bash
python -m src.linkedin_alerts /path/to/alert1.eml /path/to/alert2.eml
python -m src.review
python -m src.dashboard
```

The importer produces `data/linkedin_jobs.json`. The review stage merges
its job links into the existing application queue, without treating them as
verified remote, USD, freelance, or Brazil-eligible opportunities.

**Do not commit .eml files or share private email alerts publicly.**
The JSON output contains only public LinkedIn job URLs and tentative job titles,
but those may still be inaccurate. Verify at the listing before applying.

LinkedIn alert links which only work via tracking redirects are deliberately
ignored: this avoids calling a tracking server or storing signed tokens.

Automated Gmail ingestion is a **separate future opt-in step**, not enabled here.
