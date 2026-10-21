# Private CV storage — setup

1. In the existing Supabase project, run `supabase/migrations/20261021_private_resume_files.sql` using the Supabase SQL Editor (or your controlled migration workflow).
2. Confirm Google login works and that `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are configured on the Next.js app.
3. Sign in, open **Meus currículos** (`/resumes`), upload a PDF for each language. The PDF is placed in a **private** Supabase bucket, under `<auth-user-id>/<random-id>.pdf`.
4. Confirm that user B cannot list, download or remove user A's files and that anonymous users cannot access the download route.
5. Confirm invalid non-PDF and >5MB files are rejected and replacing the EN PDF does not change the PT file.
6. Verify the deployment build before merging.

The GitHub repository is public. Do not commit any CV PDFs, storage access credentials, private filenames with sensitive data, or service-role keys. Do not turn this bucket public. No email dispatch or background auto-apply is enabled by this change. A CV remains unavailable to automated outreach until a separately reviewed integration is implemented. The historical `resumes` and `resume_versions` text tables are unchanged.

### Known rollout limitation
This PR creates application code and SQL migration only; it **cannot apply the migration to your Supabase project** through GitHub. Before deploying, run the migration with sufficient database permissions. In the event of a database deletion failure after storage deletion, the metadata may point to a missing file; retry via admin reconciliation. The app intentionally does not expose direct public or signed URLs.
