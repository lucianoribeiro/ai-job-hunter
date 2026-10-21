-- Private original PDF resumes; apply in the connected Supabase SQL Editor before using UI.
insert into storage.buckets (id,name,public,file_size_limit,allowed_mime_types)
values ('private-resumes','private-resumes',false,5242880,array['application/pdf'])
on conflict (id) do update set public=false,file_size_limit=5242880,allowed_mime_types=array['application/pdf'];

create table if not exists public.resume_files (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 language text not null check (language in ('pt-BR','en-US')),
 label text not null check (char_length(label) between 1 and 120),
 object_path text not null unique,
 original_name text not null,
 bytes integer not null check (bytes > 0 and bytes <= 5242880),
 created_at timestamptz not null default now(),
 unique (user_id,language)
);
alter table public.resume_files enable row level security;
drop policy if exists resume_files_own_select on public.resume_files;
create policy resume_files_own_select on public.resume_files for select to authenticated using (auth.uid() = user_id);
drop policy if exists resume_files_own_insert on public.resume_files;
create policy resume_files_own_insert on public.resume_files for insert to authenticated with check (auth.uid() = user_id and object_path like auth.uid()::text || '/%');
drop policy if exists resume_files_own_update on public.resume_files;
create policy resume_files_own_update on public.resume_files for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id and object_path like auth.uid()::text || '/%');
drop policy if exists resume_files_own_delete on public.resume_files;
create policy resume_files_own_delete on public.resume_files for delete to authenticated using (auth.uid() = user_id);

drop policy if exists private_resumes_owner_read on storage.objects;
create policy private_resumes_owner_read on storage.objects for select to authenticated
 using (bucket_id='private-resumes' and (storage.foldername(name))[1]=auth.uid()::text);
drop policy if exists private_resumes_owner_insert on storage.objects;
create policy private_resumes_owner_insert on storage.objects for insert to authenticated
 with check (bucket_id='private-resumes' and (storage.foldername(name))[1]=auth.uid()::text);
drop policy if exists private_resumes_owner_delete on storage.objects;
create policy private_resumes_owner_delete on storage.objects for delete to authenticated
 using (bucket_id='private-resumes' and (storage.foldername(name))[1]=auth.uid()::text);

-- The application status is already tracked by the existing applications table.
-- Sending remains deliberately disabled; statuses must never be marked sent on draft creation.
