CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  target_job_titles TEXT[] NOT NULL DEFAULT '{}',
  target_skills TEXT[] NOT NULL DEFAULT '{}',
  timezone TEXT NOT NULL DEFAULT 'UTC',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS users_email_normalized_idx
  ON users (LOWER(email));

CREATE TABLE IF NOT EXISTS resume_assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  object_key TEXT NOT NULL UNIQUE,
  original_filename TEXT NOT NULL,
  media_type TEXT NOT NULL CHECK (media_type = 'application/pdf'),
  byte_size BIGINT NOT NULL CHECK (byte_size > 0),
  sha256_digest CHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS resume_assets_user_created_idx
  ON resume_assets(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS source_feeds (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  config_ref TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  last_checked_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_feed_id UUID NOT NULL REFERENCES source_feeds(id) ON DELETE CASCADE,
  source_job_id TEXT NOT NULL,
  application_url TEXT NOT NULL,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  location TEXT NOT NULL DEFAULT '',
  description_excerpt TEXT NOT NULL DEFAULT '',
  published_at TIMESTAMPTZ,
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (source_feed_id, source_job_id)
);

CREATE INDEX IF NOT EXISTS jobs_first_seen_idx ON jobs(first_seen_at DESC);

CREATE TABLE IF NOT EXISTS discovery_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scheduled_for TIMESTAMPTZ NOT NULL,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL CHECK (status IN ('RUNNING', 'SUCCEEDED', 'PARTIAL', 'FAILED')),
  source_count INTEGER NOT NULL DEFAULT 0 CHECK (source_count >= 0),
  jobs_checked INTEGER NOT NULL DEFAULT 0 CHECK (jobs_checked >= 0),
  recommendations_created INTEGER NOT NULL DEFAULT 0 CHECK (recommendations_created >= 0),
  error_summary TEXT
);

CREATE INDEX IF NOT EXISTS discovery_runs_status_scheduled_idx
  ON discovery_runs(status, scheduled_for DESC);

CREATE TABLE IF NOT EXISTS recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  match_percentage SMALLINT NOT NULL CHECK (match_percentage BETWEEN 0 AND 100),
  matched_skills TEXT[] NOT NULL DEFAULT '{}',
  missing_skills TEXT[] NOT NULL DEFAULT '{}',
  rationale TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING_REVIEW'
    CHECK (status IN ('PENDING_REVIEW', 'APPROVED', 'SKIPPED')),
  decided_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, job_id)
);

CREATE INDEX IF NOT EXISTS recommendations_user_status_score_idx
  ON recommendations(user_id, status, match_percentage DESC);

CREATE TABLE IF NOT EXISTS application_link_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  recommendation_id UUID NOT NULL REFERENCES recommendations(id) ON DELETE CASCADE,
  opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS application_link_events_user_opened_idx
  ON application_link_events(user_id, opened_at DESC);
