# Resume Studio — initial implementation

This first iteration provides a **private, manually editable** resume record and human-approved resume versions in the authenticated SaaS.

## Setup
- Apply `db/001_saas_foundation.sql` followed by `db/002_resume_studio.sql`.
- Configure Supabase Auth as described in `docs/saas-setup.md`.
- Open `/resumes` after Google login.

## Implemented
- Auth-required page, create resume and resume versions, server-side input length validation.
- Ownership required at both database (RLS, foreign keys) and action level.
- Resume versions start as drafts; approval is explicit and never sends an application.
- Plain-text resume content is stored in private Postgres rows, not the repository.

## Not yet implemented
- Automated LinkedIn import (depends on authorized data export or explicitly provided data).
- PDF/DOCX upload, document parsing, formatting, download and AI suggestions.
- Edit/delete UI, audit log, encryption design review, full account deletion and LGPD workflow.
- Mapping versions to job applications and end-to-end email approval.
- Runtime Supabase configuration and two-account RLS verification.

Never store resumes, OAuth keys, Gmail messages or CV files in a public git repository.
