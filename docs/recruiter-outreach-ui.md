# Recruiter outreach UI — safe review stage
- Signed-in job owners can prepare email recipient, subject, body and an optional approved resume version.
- Only explicitly published professional application addresses should be entered. User must verify the ad and recipient.
- Stored as private per-user database draft and manually approved before any future integration.
- No Gmail API invocation, Gmail draft creation, CV attachment or email send occurs in this phase.
- A future Gmail action must require per-user OAuth, attachment creation, explicit approval and error handling; never use a shared mailbox across users.
- Apply database migrations in order, including db/003_recruiter_outreach.sql.
