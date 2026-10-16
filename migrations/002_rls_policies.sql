-- ─────────────────────────────────────────────────────────────────────────────
--  Migration 002 — Row Level Security policies
--  Run AFTER 001_initial_schema.sql
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable RLS on all user-specific tables
alter table public.profiles           enable row level security;
alter table public.user_interests     enable row level security;
alter table public.user_preferences   enable row level security;
alter table public.bookmarks          enable row level security;
alter table public.user_interactions  enable row level security;
alter table public.user_feedback      enable row level security;

-- categories is public-read, admin-write
alter table public.categories enable row level security;

-- ── profiles ────────────────────────────────────────────────────────────────
create policy "profiles: users read own" on public.profiles
  for select using (auth.uid() = id);

create policy "profiles: users update own" on public.profiles
  for update using (auth.uid() = id);

create policy "profiles: users insert own" on public.profiles
  for insert with check (auth.uid() = id);

-- ── user_interests ───────────────────────────────────────────────────────────
create policy "interests: users read own" on public.user_interests
  for select using (auth.uid() = user_id);

create policy "interests: users insert own" on public.user_interests
  for insert with check (auth.uid() = user_id);

create policy "interests: users update own" on public.user_interests
  for update using (auth.uid() = user_id);

create policy "interests: users delete own" on public.user_interests
  for delete using (auth.uid() = user_id);

-- ── user_preferences ─────────────────────────────────────────────────────────
create policy "prefs: users read own" on public.user_preferences
  for select using (auth.uid() = user_id);

create policy "prefs: users upsert own" on public.user_preferences
  for insert with check (auth.uid() = user_id);

create policy "prefs: users update own" on public.user_preferences
  for update using (auth.uid() = user_id);

-- ── bookmarks ────────────────────────────────────────────────────────────────
create policy "bookmarks: users read own" on public.bookmarks
  for select using (auth.uid() = user_id);

create policy "bookmarks: users insert own" on public.bookmarks
  for insert with check (auth.uid() = user_id);

create policy "bookmarks: users delete own" on public.bookmarks
  for delete using (auth.uid() = user_id);

-- ── user_interactions ────────────────────────────────────────────────────────
create policy "interactions: users read own" on public.user_interactions
  for select using (auth.uid() = user_id);

create policy "interactions: users insert own" on public.user_interactions
  for insert with check (auth.uid() = user_id);

-- ── user_feedback ────────────────────────────────────────────────────────────
create policy "feedback: users read own" on public.user_feedback
  for select using (auth.uid() = user_id);

create policy "feedback: users insert own" on public.user_feedback
  for insert with check (auth.uid() = user_id);

create policy "feedback: users delete own" on public.user_feedback
  for delete using (auth.uid() = user_id);

-- ── categories (public read) ─────────────────────────────────────────────────
create policy "categories: public read" on public.categories
  for select using (is_active = true);

-- ── Auto-create profile on sign-up ───────────────────────────────────────────
-- This function runs when a new user signs up via Supabase Auth
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, split_part(new.email, '@', 1))
  on conflict (id) do nothing;

  insert into public.user_preferences (user_id)
  values (new.id)
  on conflict (user_id) do nothing;

  return new;
end;
$$;

-- Attach trigger to auth.users
create or replace trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
