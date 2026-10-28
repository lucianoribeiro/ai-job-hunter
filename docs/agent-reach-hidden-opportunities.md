# Hidden Opportunities — Agent Reach (experimental)

This is an optional, read-only adapter and **not** an AI-based confirmation that a hidden job exists.

## Prerequisites

Install and verify the actual Agent Reach project using its official [install instructions](https://github.com/Panniantong/Agent-Reach/blob/main/docs/install.md). Do not install the unrelated PyPI package with the same name. Run `agent-reach channels` to inspect supported channels. Do not configure LinkedIn login or copy account cookies to GitHub Actions. Public web search may work without authentication, subject to provider changes.

## Run

```bash
python -m src.agent_reach_hidden
```

The adapter invokes read-only `agent-reach web search` for QA-specific intent phrases, then outputs:

- `data/hidden_opportunities.json`: raw evidence excerpts, links, statistics, and errors
- `data/hidden_opportunities.html`: local review report

If Agent Reach is unavailable or a query fails, the report records failure instead of silently claiming zero opportunities. If a CLI version changes its output format, update the adapter before relying on its counts.

Alternatively, use a sanitized JSON export of public results for reproducible testing:

```bash
python -m src.agent_reach_hidden --input /path/to/public-sources.json
```

Each array item requires an HTTPS `url` and public `excerpt` string. **Never provide login cookies, access tokens, private messages, or personal contact data.**

## Classification policy

1. A source must contain both a QA/quality-engineering term and a hiring-intent phrase.
2. Each unique public URL becomes at most one potential signal.
3. Existing `data/jobs.csv` URLs are compared using a canonical URL; "not in baseline" does not prove the opportunity is truly new across all collectors.
4. All items remain **potential/unconfirmed** until there is separate evidence from the company or recruiter. Brazil eligibility and USD compensation remain unknown.
5. No automated outreach or applications are sent.

LinkedIn public job reading is not equivalent to authenticated LinkedIn post searching. Agent Reach currently documents that in-platform LinkedIn search requires login; this adapter intentionally only uses the public web channel.

## CI

Run `python -m unittest discover -s tests -v`. The optional collector is not enabled in GitHub Pages CI until a verified public-source environment and a safe dependency-pinning approach are tested. The report is not included in production cards yet.
