-- Resume Studio: per-user private structured resume content and versions.
-- No files are stored in the public repository.
create table if not exists public.resumes (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 title text not null check (length(title) between 1 and 120),
 language text not null default 'pt-BR' check (language in ('pt-BR','en-US')),
 summary text not null default '' check (length(summary) <= 12000),
 experience text not null default '' check (length(experience) <= 60000),
 skills text not null default '' check (length(skills) <= 12000),
 education text not null default '' check (length(education) <= 12000),
 source text not null default 'manual' check (source in ('manual','linkedin_export','existing_cv')),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 unique (id,user_id)
);
create table if not exists public.resume_versions (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 resume_id uuid not null,
 label text not null check (length(label) between 1 and 120),
 target_role text not null default '',
 content text not null check (length(content) between 1 and 80000),
 status text not null default 'draft' check (status in ('draft','approved')),
 created_at timestamptz not null default now(),
 foreign key (resume_id,user_id) references public.resumes(id,user_id) on delete cascade
);
create index if not exists resumes_owner_idx on public.resumes(user_id);
create index if not exists resume_versions_owner_idx on public.resume_versions(user_id);
alter table public.resumes enable row level security;
alter table public.resume_versions enable row level security;
drop policy if exists resumes_owner on public.resumes;
create policy resumes_owner on public.resumes for all to authenticated
 using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
drop policy if exists versions_owner on public.resume_versions;
create policy versions_owner on public.resume_versions for all to authenticated
 using ((select auth.uid())=user_id) with check ((select auth.uid())=user_id);
revoke all on public.resumes, public.resume_versions from anon;
grant select,insert,update,delete on public.resumes, public.resume_versions to authenticated;
