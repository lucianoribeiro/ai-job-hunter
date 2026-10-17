-- Per-user recruiter outreach, always review-only; no email is sent from database actions.
create table if not exists public.recruiter_drafts (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 opportunity_id uuid not null,
 resume_version_id uuid,
 recipient_email text not null check(length(recipient_email) between 5 and 254),
 subject text not null check(length(subject) between 1 and 250),
 body text not null check(length(body) between 1 and 12000),
 status text not null default 'pending_review' check(status in ('pending_review','approved','discarded')),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 foreign key(opportunity_id,user_id) references public.opportunities(id,user_id) on delete cascade,
 foreign key(resume_version_id,user_id) references public.resume_versions(id,user_id) on delete restrict
);
create index if not exists recruiter_drafts_user_idx on public.recruiter_drafts(user_id);
alter table public.recruiter_drafts enable row level security;
drop policy if exists recruiter_drafts_owner on public.recruiter_drafts;
create policy recruiter_drafts_owner on public.recruiter_drafts for all to authenticated
 using((select auth.uid())=user_id) with check((select auth.uid())=user_id);
revoke all on public.recruiter_drafts from anon;
grant select,insert,update,delete on public.recruiter_drafts to authenticated;
