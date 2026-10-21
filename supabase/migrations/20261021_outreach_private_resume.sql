-- Bind approved outreach to private PDF files without enabling sending.
alter table public.recruiter_drafts add column if not exists resume_file_id uuid references public.resume_files(id) on delete set null;
create index if not exists recruiter_drafts_resume_file_id_idx on public.recruiter_drafts(resume_file_id);
-- Draft ownership and PDF ownership are both checked by the authenticated server action.
