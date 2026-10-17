-- Run in a Supabase Postgres project. Authentication is managed by Supabase Auth.
-- All tables contain user ownership and deny anonymous access by default.
create extension if not exists pgcrypto;

create table if not exists public.career_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  label text not null check (length(label) between 1 and 120),
  industry text not null default '',
  target_roles text[] not null default '{}',
  excluded_roles text[] not null default '{}',
  remote_first boolean not null default true,
  include_hybrid boolean not null default false,
  origin_city text not null default '',
  max_radius_km integer not null default 50 check (max_radius_km between 0 and 500),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(id, user_id)
);
create index if not exists career_profiles_user_id_idx on public.career_profiles(user_id);

create table if not exists public.opportunities (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  profile_id uuid not null,
  title text not null,
  company text not null default '',
  listing_url text not null,
  location_text text,
  work_mode text not null default 'unknown'
    check (work_mode in ('remote','hybrid','onsite','unknown')),
  source text not null default '',
  created_at timestamptz not null default now(),
  unique(user_id, listing_url),
  foreign key (profile_id, user_id) references public.career_profiles(id, user_id) on delete cascade
);
create index if not exists opportunities_user_id_idx on public.opportunities(user_id);

create table if not exists public.applications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  opportunity_id uuid not null,
  status text not null default 'pending_review'
    check (status in ('pending_review','approved','drafted','applied','interview','rejected','offer','dismissed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id, opportunity_id),
  foreign key (opportunity_id, user_id) references public.opportunities(id, user_id) on delete cascade
);
create index if not exists applications_user_id_idx on public.applications(user_id);

alter table public.career_profiles enable row level security;
alter table public.opportunities enable row level security;
alter table public.applications enable row level security;

-- Explicit user isolation for SELECT / INSERT / UPDATE / DELETE.
drop policy if exists career_profiles_own on public.career_profiles;
create policy career_profiles_own on public.career_profiles for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
drop policy if exists opportunities_own on public.opportunities;
create policy opportunities_own on public.opportunities for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
drop policy if exists applications_own on public.applications;
create policy applications_own on public.applications for all to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

revoke all on public.career_profiles, public.opportunities, public.applications from anon;
grant select, insert, update, delete on public.career_profiles, public.opportunities, public.applications to authenticated;
