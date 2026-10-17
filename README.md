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

## Opportunity advisor (top of dashboard)

The advisor is generated before the offline HTML dashboard. By default it uses explainable evidence-based rules, marks employer reputation and Brazil eligibility as unverified, and avoids guessing USD compensation or two-hour availability. An optional hosted AI narrative requires a GitHub Actions secret named `OPENAI_API_KEY`, under repository Settings > Secrets and variables > Actions. The API has separate usage charges. If the secret is missing or the API is unavailable, rules-based advice still works. Never add tokens to committed files.

For local CV matching, save your CV as a UTF-8 text file **outside this repository** and run `python -m src.cv_match --cv /path/to/private-cv.txt`. This feature evaluates skill keywords locally, does not upload the CV, and is not yet a browser upload workflow. Employer vetting still requires independent evidence and review. The offline dashboard does not execute an AI API call in the browser.

## Empresas estratégicas — Honda Brasil

The daily job discovery workflow checks the official public Honda careers landing page (`https://honda.gupy.io/`) for directly exposed job links. Results are exported to `data/strategic_jobs.json` and displayed in the dashboard, separately from remote/USD opportunities. The region includes Sumaré, Campinas, Paulínia, Nova Odessa, Americana and Hortolândia. Gupy's documented integration API requires authorization; this watcher never uses employer credentials or claims official API access. If the career page loads links dynamically, the dashboard reports `needs_connector` instead of falsely showing zero openings. Employer, location, and role suitability must be verified on the official job posting. The implementation does not submit applications.

## APinfo — consulta externa (sem API oficial confirmada)

O dashboard apresenta um link para o portal [APinfo](https://www.apinfo.com/apinfo/), identificado como fonte de consulta **manual**. A APinfo não integra a coleta automática, não gera vagas fictícias nem aumenta os contadores de oportunidades. Antes de automatizar a ingestão, é necessário confirmar uma API/feed oficialmente permitido ou obter autorização explícita da plataforma. A presença do link não indica parceria ou integração de dados.
