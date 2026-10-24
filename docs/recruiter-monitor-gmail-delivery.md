# Recruiter Monitor — CV e envio Gmail

## Implementado
- Public posts: contact detection only when an email appears explicitly in the indexed post title. It is **not** proof that the address accepts applications. Do not infer missing recruiter details.
- The public GitHub Pages dashboard links to the authenticated Next.js application using `CAREER_APP_URL`. It cannot access private resumes, Gmail credentials or per-user delivery receipts.
- Authenticated flow: select an opportunity, choose an approved Resume Studio version or private PDF, edit a bilingual role-aware email template, save, approve, then explicitly choose **Confirmar e enviar e-mail com CV** or create a Gmail draft.
- A successful Gmail `users.messages.send` result with message id is stored in `recruiter_drafts.gmail_message_id` and `sent_at`. The authenticated application card displays a sent indicator only with those receipts.
- A database compare-and-swap changes `approved` to `sending` before the Gmail call to block concurrent duplicate sends. If Gmail succeeds but recording fails, `sending` remains: reconcile manually from Gmail Sent; do not blindly retry.
- RLS limits resumes and delivery states to their authenticated owners. No CV files or OAuth tokens are written to the public repository.

## Activation requirements
1. Apply `db/001_saas_foundation.sql`, `db/002_resume_studio.sql`, `db/003_recruiter_outreach.sql`, `db/004_gmail_drafts.sql`, `db/005_recruiter_send_receipts.sql` in order (and earlier migrations for private resume uploads as documented).
2. Deploy `app/` to an authenticated Next.js runtime with Supabase credentials and `NEXT_PUBLIC_SITE_URL`; GitHub Pages alone cannot run these server actions.
3. In Google Cloud/Supabase OAuth, approve `gmail.compose` and `gmail.send`; re-consent in the app. Sending must be expressly initiated by the logged-in user.
4. Set `CAREER_APP_URL` in the GitHub Actions repository variables so public recruiter cards can open the authenticated workflow.
5. Upload or approve the correct CV privately, inspect the recipient and job requirements, and use the explicit send action. Never use a generic address inferred from an unknown company.
6. Run `npm run typecheck` and `npm run build` inside `app/` plus Python regression suite before deploying.

## Not yet implemented
- Unattended automatic/batch sends and automatic role-to-CV selection.
- Reliable full-description personalization when the public index only contains a title/excerpt; the template reflects the title and user-entered verified details, not imagined qualifications.
- A live sent badge **on the public GitHub Pages card**. Per-user private state is shown in the authenticated application, not exposed to anonymous viewers.
- Gmail delivery to recipient inbox cannot be guaranteed: Gmail API confirms accepted send, not recipient receipt or recruiter review.
