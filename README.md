# AI Job Hunter

A zero-paid-API, **review-first** QA job discovery agent.

## Capabilities
- Finds publicly posted remote QA jobs from Remotive and Arbeitnow.
- Scores roles including QA Engineer, QA Lead, QA Manager and QA automation.
- Flags potential freelance opportunities; USD salary is only indicated if explicitly present.
- Creates a rolling job history with first/last seen dates and stable URL-based identities.
- Creates a review queue, preserving human decisions on subsequent runs.
- Produces `data/jobs.csv`, `data/report.md`, `data/history.json`, `data/applications.json` and `data/applications.md`.
- Generates an offline HTML dashboard (`data/dashboard.html`) showing job counts, freelance listings and application statuses; it can be downloaded from GitHub Actions artifacts and opened locally.
- Runs daily through GitHub Actions.

## Quick start

```bash
python -m unittest discover -s tests -v
python -m src.hunter
python -m src.review
python -m src.dashboard
```

Or go to [GitHub Actions](https://github.com/lucianoribeiro/ai-job-hunter/actions), select **Discover QA jobs**, and choose **Run workflow**.

## Review process

The `data/applications.md` report is a view of roles awaiting review. The canonical queue is `data/applications.json`. Each item begins at `pending_review`. After you personally verify a posting, change its `status` to `approved`, `dismissed`, `applied`, `interview`, `rejected` or `offer`. These values and existing notes are preserved on refresh.

**No CVs are sent and no job applications are submitted automatically.** Approval in the file is a tracking state, not authorization to submit.

## Reliability limitations

The ranking is heuristic, not an LLM. Employer reputation is initially `unverified`: the system does not claim company trustworthiness without evidence. Remote listings can be restricted to specific countries; Brazil eligibility must be checked. Flexible/contract is **not** proof of two hours per day, and a USD preference is not a guarantee of USD compensation. The source APIs can be down or return incomplete data.

## Privacy

This repository is public. **Never commit personal CVs, email addresses, private application notes, credentials, interview correspondence or other confidential data.** Review status and job metadata are visible publicly. Use a private repository before tracking personal details.

## LinkedIn alerts (opt-in)

An offline importer is available for LinkedIn alert emails exported as .eml files. It extracts only direct public job links and tentative titles; no login or mailbox access is required. Run `python -m src.linkedin_alerts /path/to/alert.eml` and then `python -m src.review` and `python -m src.dashboard`. See [instructions](docs/linkedin-alerts.md). Do not commit email exports.

## Public company-board sources (opt-in)

The `company_boards` configuration supports Greenhouse, Lever, Ashby, Personio and Workable.
Only add a verified **public employer board slug**; no recruiter tokens or private APIs are needed.
Example (replace with a real board identifier after checking its public careers page):

```json
"company_boards": {
  "greenhouse": [{"company": "Employer Name", "board": "verified-board-slug"}],
  "lever": [],
  "ashby": [],
  "personio": [],
  "workable": []
}
```

Empty arrays are intentional: **a connector does not automatically discover employers**. Until
verified boards are configured, the five adapters return zero jobs. Company feeds may omit
publication dates or remote eligibility; these values must not be inferred. Workable's public
endpoint requires employer-by-employer verification. Failures appear under source errors in
`data/report.md`. Existing Remotive and Arbeitnow jobs continue to be collected.


## Regional expansion: Campinas and Paulínia

The SmartRecruiters adapter is configured for BoschGroup (Bosch) and SyngentaGroup
(Syngenta). It reads the documented public company postings API with bounded
pagination, including city and published date when supplied. The Recruitee careers
site adapter is implemented but has no employer boards configured.

**Important:** A configured board is not proof that it returned jobs. Run the
workflow and inspect the source errors and real job output. Do not claim that
every employer board or region has vacancies. Workable remains disabled pending
endpoint verification. Recruitee has announced a Careers Site API token
requirement effective February 2027; do not bypass authentication or use
private credentials. Prefer the officially public XML feed if the API becomes
restricted.

The two profiles are QA (remote-first) and project management (remote, hybrid,
or onsite). Regional cities are preserved in the location field. An explicit
regional city filter and a broader discovery mechanism are still needed to
guarantee useful coverage for Paulínia, Campinas, Sumaré and nearby cities.
