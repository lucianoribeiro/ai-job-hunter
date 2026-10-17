# AI Job Hunter

A zero-paid-API, **review-first** QA job discovery agent.

## Capabilities
- Finds publicly posted remote QA jobs from Remotive and Arbeitnow.
- Scores roles including QA Engineer, QA Lead, QA Manager and QA automation.
- Flags potential freelance opportunities; USD salary is only indicated if explicitly present.
- Creates a rolling job history with first/last seen dates and stable URL-based identities.
- Creates a review queue, preserving human decisions on subsequent runs.
- Produces `data/jobs.csv`, `data/report.md`, `data/history.json`, `data/applications.json` and `data/applications.md`.
- Runs daily through GitHub Actions.

## Quick start

```bash
python -m unittest discover -s tests -v
python -m src.hunter
python -m src.review
```

Or go to [GitHub Actions](https://github.com/lucianoribeiro/ai-job-hunter/actions), select **Discover QA jobs**, and choose **Run workflow**.

## Review process

The `data/applications.md` report is a view of roles awaiting review. The canonical queue is `data/applications.json`. Each item begins at `pending_review`. After you personally verify a posting, change its `status` to `approved`, `dismissed`, `applied`, `interview`, `rejected` or `offer`. These values and existing notes are preserved on refresh.

**No CVs are sent and no job applications are submitted automatically.** Approval in the file is a tracking state, not authorization to submit.

## Reliability limitations

The ranking is heuristic, not an LLM. Employer reputation is initially `unverified`: the system does not claim company trustworthiness without evidence. Remote listings can be restricted to specific countries; Brazil eligibility must be checked. Flexible/contract is **not** proof of two hours per day, and a USD preference is not a guarantee of USD compensation. The source APIs can be down or return incomplete data.

## Privacy

This repository is public. **Never commit personal CVs, email addresses, private application notes, credentials, interview correspondence or other confidential data.** Review status and job metadata are visible publicly. Use a private repository before tracking personal details.
