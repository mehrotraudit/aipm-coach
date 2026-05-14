-- Run in Supabase → SQL Editor. Fixes PostgREST APIError on insert/select when RLS blocks anon.

create table if not exists public.sessions (
  id bigint generated always as identity primary key,
  category text not null,
  score smallint not null,
  created_at timestamptz not null default now()
);

alter table public.sessions enable row level security;

drop policy if exists "sessions_anon_insert" on public.sessions;
drop policy if exists "sessions_anon_select" on public.sessions;

create policy "sessions_anon_insert" on public.sessions
  for insert to anon with check (true);

create policy "sessions_anon_select" on public.sessions
  for select to anon using (true);
