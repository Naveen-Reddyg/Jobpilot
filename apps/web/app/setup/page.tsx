'use client';

import { FormEvent, useEffect, useState } from 'react';
import { SiteShell } from '@/components/site-shell';
import { ApiError, apiClient, Profile } from '@/lib/api-client';

export default function SetupPage() {
  const [profile, setProfile] = useState<Profile>({
    targetJobTitles: [],
    targetSkills: [],
    timezone: 'UTC',
  });
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [discoveryConfigured, setDiscoveryConfigured] = useState<boolean | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [discoveryMessage, setDiscoveryMessage] = useState<string | null>(null);

  useEffect(() => {
    apiClient.getProfile().then(setProfile).catch((error: unknown) => {
      if (!(error instanceof ApiError && error.status === 404)) setMessage('Unable to load the saved profile.');
    });
    apiClient.getDiscoveryProvider().then(({ configured }) => setDiscoveryConfigured(configured)).catch(() => {
      setDiscoveryConfigured(false);
    });
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      setProfile(await apiClient.saveProfile({
        ...profile,
        targetJobTitles: profile.targetJobTitles,
        targetSkills: profile.targetSkills,
      }));
      setMessage('Profile saved.');
    } catch {
      setMessage('Unable to save the profile.');
    } finally {
      setSaving(false);
    }
  }

  async function onResumeSelected(file?: File) {
    if (!file) return;
    setUploading(true);
    setMessage(null);
    try {
      const uploaded = await apiClient.uploadResume(file);
      setProfile((current) => ({ ...current, resumeName: uploaded.filename }));
      setMessage('Resume uploaded.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to upload the resume.');
    } finally {
      setUploading(false);
    }
  }

  async function onSearchJobs() {
    setDiscovering(true);
    setDiscoveryMessage(null);
    try {
      await apiClient.saveProfile(profile);
      const result = await apiClient.runDiscovery();
      setDiscoveryMessage(
        `Checked ${result.jobsChecked} jobs; added ${result.recommendationsCreated} new recommendations.`,
      );
    } catch (error) {
      setDiscoveryMessage(error instanceof Error ? error.message : 'Unable to search for jobs.');
    } finally {
      setDiscovering(false);
    }
  }

  return (
    <SiteShell>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">Profile Setup</p>
        <h2 className="mt-2 font-heading text-4xl font-bold text-text">Target role and skills</h2>
      </div>

      <form onSubmit={onSubmit} className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
        <div className="rounded-3xl border border-border bg-white p-6 shadow-soft">
          <div className="space-y-6">
            <label className="block text-sm font-semibold text-text">
              Target job titles
              <input
                className="mt-2 w-full rounded-xl border border-border bg-surface px-3 py-3 text-sm text-text outline-none ring-0 transition focus:border-primary"
                value={profile.targetJobTitles.join(', ')}
                onChange={(event) =>
                  setProfile({
                    ...profile,
                    targetJobTitles: event.target.value.split(',').map((item) => item.trim()).filter(Boolean),
                  })
                }
              />
            </label>

            <label className="block text-sm font-semibold text-text">
              Target skills
              <input
                className="mt-2 w-full rounded-xl border border-border bg-surface px-3 py-3 text-sm text-text outline-none ring-0 transition focus:border-primary"
                value={profile.targetSkills.join(', ')}
                onChange={(event) =>
                  setProfile({
                    ...profile,
                    targetSkills: event.target.value.split(',').map((item) => item.trim()).filter(Boolean),
                  })
                }
              />
            </label>

            <label className="block text-sm font-semibold text-text">
              Timezone
              <input
                className="mt-2 w-full rounded-xl border border-border bg-surface px-3 py-3 text-sm text-text outline-none ring-0 transition focus:border-primary"
                value={profile.timezone}
                onChange={(event) => setProfile({ ...profile, timezone: event.target.value })}
              />
            </label>
          </div>

          <div className="mt-8 border-t border-border pt-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Job discovery</p>
                <h3 className="mt-2 font-heading text-xl font-bold text-text">JSearch via RapidAPI</h3>
                <p className="mt-2 max-w-xl text-sm text-muted">
                  Search remote public job listings using up to three target titles. Results are limited to the configured country.
                </p>
                <p className="mt-2 text-sm" role="status">
                  {discoveryConfigured === null
                    ? 'Checking RapidAPI configuration…'
                    : discoveryConfigured
                      ? 'RapidAPI key configured.'
                      : 'Add RAPIDAPI_KEY to the workspace .env file, then restart the API.'}
                </p>
              </div>
              <button
                type="button"
                className="shrink-0 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={!discoveryConfigured || discovering || saving}
                onClick={onSearchJobs}
              >
                {discovering ? 'Searching…' : 'Find jobs'}
              </button>
            </div>
            {discoveryMessage && <p role="status" className="mt-4 text-sm text-muted">{discoveryMessage}</p>}
          </div>

          <div className="mt-8 flex justify-end">
            <button
              type="submit"
              className="rounded-full bg-primary px-5 py-3 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:opacity-60"
              disabled={saving}
            >
              {saving ? 'Saving…' : 'Save profile'}
            </button>
          </div>
          {message && <p role="status" className="mt-4 text-right text-sm text-muted">{message}</p>}
        </div>

        <aside className="rounded-3xl border border-border bg-white p-6 shadow-soft">
          <p className="text-xs uppercase tracking-[0.18em] text-muted">Resume</p>
          <h3 className="mt-3 font-heading text-2xl font-bold text-text">Private PDF upload</h3>
          <div className="mt-4 rounded-2xl border border-dashed border-border bg-surface p-6 text-sm text-muted">
            {profile.resumeName ?? 'No PDF uploaded yet'}
          </div>
          <label className="mt-6 block cursor-pointer rounded-full border border-primary bg-primary/5 px-4 py-3 text-center text-sm font-semibold text-primary">
            {uploading ? 'Uploading…' : 'Upload PDF'}
            <input type="file" accept="application/pdf" className="hidden" disabled={uploading} onChange={(event) => onResumeSelected(event.target.files?.[0])} />
          </label>
        </aside>
      </form>
    </SiteShell>
  );
}
