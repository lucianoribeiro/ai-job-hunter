# SaaS foundation — setup and security boundaries

This PR adds an **initial authenticated web application**, separate from the static prototype in `web/`.

## Requirements
- A Supabase project (Postgres + Auth) with Google OAuth provider configured.
- A trusted web deployment origin (or localhost for development).
- Node.js 20+ and access to `npm install`.

## Steps
1. Create a Supabase project and apply `db/001_saas_foundation.sql` in SQL editor.
2. Enable Google as an OAuth provider in Supabase Auth; add the correct redirect URL for your deployment.
3. In `app/`, copy `.env.example` to `.env.local` and set:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` (public key, not service role)
   - `NEXT_PUBLIC_SITE_URL` (exact origin, e.g. `http://localhost:3000`)
4. Run `npm install`, `npm run typecheck`, `npm run build`, then `npm run dev`.
5. Open the homepage, sign in with Google and create a career profile.

## Commercial readiness boundaries
- User data lives in Supabase with row-level security: policies require `auth.uid() = user_id`.
- Cross-user references are enforced with composite foreign keys.
- Multi-user and cross-account authorization must be tested with two actual test users **before production**.
- OAuth setup, hosting, environment variables and real login have **not** been configured by this PR.
- This is an initial authenticated profile-management application, **not** a complete commercial product.
- No Gmail tokens, candidate CVs, or email addresses should be committed to the public repository.
- Billing, permissions for team accounts, profile edits/deletions UI, user consent, LGPD flows and rate limiting remain future work.
- LinkedIn alerts and recruiter draft PRs are separate and must be integrated deliberately.
