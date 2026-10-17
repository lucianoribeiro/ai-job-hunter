# LinkedIn integration — authorized MVP scope

This module **does not access LinkedIn**. Users can supply links of jobs or posts they are permitted to share, one URL per line in a local `.txt` file.

```bash
python -m src.linkedin_shared_links my-links.txt --output data/linkedin_shared_jobs.json
python -m unittest discover -s tests -v
```

The export is intentionally **separate** from confirmed employer listings: a shared link is not evidence that a role exists, is open, is remote or is eligible in Brazil. Users should independently open and verify each posting. Do not redistribute third-party post contents without permission. Do not commit personal alert emails, saved posts, CVs or recruiter contact information into this public repository.

LinkedIn alert importer (`src/linkedin_alerts.py`) remains available for explicit .eml exports. No OAuth, automatic account browsing, LinkedIn search API, scraping, Easy Apply bot, or Gmail synchronization is implemented.

See LinkedIn [User Agreement](https://www.linkedin.com/legal/user-agreement) and [Crawling Terms](https://www.linkedin.com/legal/crawling-terms). Commercial reuse of LinkedIn data needs its own rights assessment.
