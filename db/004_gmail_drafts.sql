-- Gmail OAuth tokens are never stored. Only the resulting draft identifier is retained.
alter table public.recruiter_drafts
 add column if not exists gmail_draft_id text,
 add column if not exists gmail_created_at timestamptz;

alter table public.recruiter_drafts drop constraint if exists recruiter_drafts_status_check;
alter table public.recruiter_drafts add constraint recruiter_drafts_status_check
 check(status in ('pending_review','approved','drafted','discarded'));
