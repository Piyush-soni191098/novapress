-- ─────────────────────────────────────────────────────────────────────────────
--  Migration 001 — Initial schema for Personalized News Intelligence Platform
--  Run this SQL in the Supabase SQL editor (Dashboard → SQL Editor → New query)
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Extensions ───────────────────────────────────────────────────────────────
create extension if not exists "uuid-ossp";

-- ── profiles ─────────────────────────────────────────────────────────────────
create table if not exists public.profiles (
    id               uuid primary key references auth.users(id) on delete cascade,
    display_name     text,
    avatar_url       text,
    preferred_lang   text not null default 'en',
    country          text,
    onboarding_complete boolean not null default false,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);

-- ── categories ───────────────────────────────────────────────────────────────
create table if not exists public.categories (
    id          serial primary key,
    slug        text unique not null,
    name        text not null,
    description text,
    icon        text,
    parent_slug text references public.categories(slug),
    is_active   boolean not null default true,
    created_at  timestamptz not null default now()
);

-- ── user_interests ───────────────────────────────────────────────────────────
create table if not exists public.user_interests (
    id            bigserial primary key,
    user_id       uuid not null references auth.users(id) on delete cascade,
    category_slug text not null,
    strength      numeric not null default 1.0,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),
    unique (user_id, category_slug)
);

-- ── user_preferences ─────────────────────────────────────────────────────────
create table if not exists public.user_preferences (
    user_id              uuid primary key references auth.users(id) on delete cascade,
    language             text not null default 'en',
    country              text,
    muted_topics         text[] not null default '{}',
    preferred_publishers text[] not null default '{}',
    tracking_enabled     boolean not null default true,
    updated_at           timestamptz not null default now()
);

-- ── bookmarks ────────────────────────────────────────────────────────────────
create table if not exists public.bookmarks (
    id          bigserial primary key,
    user_id     uuid not null references auth.users(id) on delete cascade,
    article_id  text not null,
    article_url text not null,
    title       text not null,
    description text,
    image_url   text,
    source      text,
    published_at text,
    provider    text,
    categories  text[] not null default '{}',
    created_at  timestamptz not null default now(),
    unique (user_id, article_id)
);

-- ── user_interactions ────────────────────────────────────────────────────────
create table if not exists public.user_interactions (
    id          bigserial primary key,
    user_id     uuid not null references auth.users(id) on delete cascade,
    article_id  text not null,
    article_url text not null,
    event_type  text not null,
    topic_slug  text,
    provider    text,
    created_at  timestamptz not null default now()
);

-- ── user_feedback ────────────────────────────────────────────────────────────
create table if not exists public.user_feedback (
    id            bigserial primary key,
    user_id       uuid not null references auth.users(id) on delete cascade,
    article_id    text not null,
    feedback_type text not null,
    topic_slug    text,
    publisher     text,
    created_at    timestamptz not null default now(),
    unique (user_id, article_id, feedback_type)
);

-- ── Indexes ──────────────────────────────────────────────────────────────────
create index if not exists idx_user_interests_user     on public.user_interests(user_id);
create index if not exists idx_bookmarks_user          on public.bookmarks(user_id);
create index if not exists idx_interactions_user       on public.user_interactions(user_id);
create index if not exists idx_interactions_event      on public.user_interactions(event_type);
create index if not exists idx_feedback_user           on public.user_feedback(user_id);

-- ── Auto-update updated_at ───────────────────────────────────────────────────
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create or replace trigger profiles_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();

create or replace trigger user_interests_updated_at
  before update on public.user_interests
  for each row execute function public.set_updated_at();
