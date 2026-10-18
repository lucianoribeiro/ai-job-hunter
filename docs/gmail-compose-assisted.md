# Gmail assisted compose — OAuth draft with PDF attachment

This step supports a user-approved recruiter message with a verified recipient supplied by the applicant.

Flow: identify an explicitly published recruiter email → prepare and approve the message → select an approved CV → authorize the restricted Gmail scope → create a Gmail draft with the professional PDF attached → user reviews and manually sends.

- The requested Google scope is `https://www.googleapis.com/auth/gmail.compose`. The application creates drafts; it has no automatic-send feature.
- OAuth provider tokens stay in the authenticated server session and are never written to application tables or the repository.
- Only an approved, user-owned resume version can be attached. The same professional ATS PDF is available for download.
- Every draft lookup is constrained by the authenticated user and protected by Supabase RLS.
- Apply `db/004_gmail_drafts.sql` after the prior migrations.
- In Google Cloud/Supabase, enable Gmail API, configure the OAuth consent screen and add the Supabase callback URI. Re-consent is required for users who logged in before the Gmail scope was added.
- Set the GitHub Actions variable `CAREER_APP_URL` to the deployed authenticated Next.js application URL so Recruiter Monitor cards can open this flow.
