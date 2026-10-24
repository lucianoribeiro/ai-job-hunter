-- Opt-in Gmail send receipts. No messages are sent by database triggers.
alter table public.recruiter_drafts add column if not exists gmail_message_id text;
alter table public.recruiter_drafts add column if not exists sent_at timestamptz;
alter table public.recruiter_drafts drop constraint if exists recruiter_drafts_status_check;
alter table public.recruiter_drafts add constraint recruiter_drafts_status_check
 check(status in ('pending_review','approved','drafted','sending','sent','discarded'));
create index if not exists recruiter_drafts_user_sent_idx
 on public.recruiter_drafts(user_id,opportunity_id,sent_at) where status='sent';
create unique index if not exists recruiter_drafts_gmail_message_unique
 on public.recruiter_drafts(user_id,gmail_message_id) where gmail_message_id is not null;
