# AI Job Hunter — Next.js hosting + Google/Gmail OAuth

The GitHub Pages dashboard is static. Gmail OAuth and private CV attachments require the Next.js app under `app/` deployed separately.

## Deploy via Vercel
1. Import GitHub repository `lucianoribeiro/ai-job-hunter`.
2. Set **Root Directory = app** and **Framework Preset = Next.js**. File `app/vercel.json` is provided.
3. Configure **Production** environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL=https://qcbzbojlrafyrjkzmjhg.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY=<Supabase publishable / legacy anon key>` (public key only; NEVER the service-role key)
   - `NEXT_PUBLIC_SITE_URL=https://<your-vercel-domain>` (exact URL, no slash suffix)
4. Deploy and verify that `/applications/outreach` redirects anonymous visitors to sign-in and that the homepage loads.
5. In GitHub repository **Settings → Secrets and variables → Actions → Variables**, set `CAREER_APP_URL=https://<your-vercel-domain>`. This connects the public Recruiter Monitor to the authenticated app.

## Google OAuth via Supabase
1. Open Supabase project `qcbzbojlrafyrjkzmjhg` → Authentication → Providers → Google.
2. In Google Cloud Console (Google Auth Platform), configure brand/consent screen, publish/test-user rules, and OAuth web client. Enable **Gmail API**.
3. Add Google OAuth **Authorized redirect URI**: `https://qcbzbojlrafyrjkzmjhg.supabase.co/auth/v1/callback`. This is Supabase's callback, NOT the Next.js `/auth/callback`.
4. Save OAuth Client ID and Secret **only** in Supabase Auth Google provider settings, never in GitHub or browser code.
5. Supabase Authentication → URL Configuration: Site URL = deployed Next.js domain. Add redirect allowlist `https://<your-vercel-domain>/auth/callback` (plus a localhost address for development if needed).
6. Sign into the Next.js application. On an approved recruiter email draft's compose page choose **Conectar Gmail e autorizar envio**. Google should request `gmail.compose` and `gmail.send`.
7. The app validates scopes on server and displays the authenticated Gmail state. If consent is refused, sending stays disabled. Gmail restricted scopes can require Google verification depending on app publishing/test mode.

## Important safety and rollout
- Confirm latest `SaaS web checks` GitHub Action passes before using a deployment.
- Run an explicit dry-run review using a test recipient you control and a non-sensitive test PDF. Do not bulk-send recruiting messages.
- Apply `db/005_recruiter_send_receipts.sql` only if the Supabase migration history does not already show `recruiter_send_receipts`; it was applied on 2026-10-24.
- Gmail API acceptance confirms sending, not inbox delivery. Status `sending` requires manual reconciliation before any retry.
- No credential, private CV, OAuth token or recipient address belongs in the public repository.
- This document prepares the deployment; it **does not imply** a Vercel project was created or the Google console approved consent.
