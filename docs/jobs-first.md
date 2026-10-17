# Jobs-first workflow (commercial MVP)

## Built
- Signed-in `/jobs` retrieves current job listings from public Remotive and Arbeitnow feeds, with server-side fetch, request timeout and 15-minute cache.
- Listings display source, original application link, employer, location and published date **only when provided**. They are not claimed to be verified, and remote eligibility for candidates in Brazil must be checked on the listing.
- Each user filters jobs with their saved professional profile and can save jobs to their private Opportunities table.
- `/applications` displays private saved opportunities, shows application status and allows preparing a review-only application record.
- Users follow the original employer job URL to apply; no browser automation, email sending or attachments are executed automatically.

## Outstanding
- Rich recruiter email drafts with private CV attachment, confirmed recruiter address, approved message and authenticated Gmail connection.
- External application automation only via supported authorized integrations and explicit per-application approval, respecting external websites and anti-bot rules.
- Accurate commute distances and verified remote hiring geography.
- Pagination and broader search sources; this initial server fetch processes limited public feed batches.
- End-to-end two-account privacy, OAuth/hosting configuration, deployment and actual job-feed live verification.
