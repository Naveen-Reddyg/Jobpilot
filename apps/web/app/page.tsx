'use client';

import { useEffect, useState } from 'react';
import { SiteShell } from '@/components/site-shell';
import { RecommendationCard } from '@/components/recommendation-card';
import { ApiError, apiClient, Profile, Recommendation } from '@/lib/api-client';

export default function HomePage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiClient.getRecommendations(),
      apiClient.getProfile().catch((error: unknown) => {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }),
    ])
      .then(([items, currentProfile]) => {
        setRecommendations(items);
        setProfile(currentProfile);
      })
      .catch(() => setLoadError('Unable to load data from the Jobs API.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <SiteShell>
      <div className="mb-8 flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">Review Queue</p>
          <h2 className="mt-2 font-heading text-4xl font-bold text-text">Recommended roles</h2>
        </div>
        <div className="rounded-full border border-primary/20 bg-white px-4 py-2 text-sm font-medium text-primary">
          {recommendations.filter((item) => item.status === 'PENDING_REVIEW').length} pending
        </div>
      </div>

      {loadError ? (
        <div role="alert" className="rounded-2xl border border-accent/30 bg-white p-10 text-center text-accent">{loadError}</div>
      ) : loading ? (
        <div className="rounded-2xl border border-border bg-white p-10 text-center text-muted">Loading recommendations…</div>
      ) : recommendations.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border bg-white p-10 text-center text-muted">
          No recommendations available yet.
        </div>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[1.5fr_0.75fr]">
          <div className="space-y-6">
            {recommendations.map((recommendation) => (
              <RecommendationCard key={recommendation.id} recommendation={recommendation} />
            ))}
          </div>

          <aside className="rounded-3xl border border-border bg-white p-5 shadow-soft">
            <p className="text-xs uppercase tracking-[0.18em] text-muted">Profile</p>
            <h3 className="mt-3 font-heading text-2xl font-bold text-text">Current profile</h3>
            <div className="mt-4 space-y-3 text-sm text-muted">
              <p><span className="font-semibold text-text">Target titles:</span> {profile?.targetJobTitles.join(', ') || 'Not configured'}</p>
              <p><span className="font-semibold text-text">Skills:</span> {profile?.targetSkills.join(', ') || 'Not configured'}</p>
              <p><span className="font-semibold text-text">Timezone:</span> {profile?.timezone ?? 'Not configured'}</p>
            </div>
            <div className="mt-6 rounded-2xl border border-border bg-surface p-4">
              <p className="text-sm font-semibold text-text">Resume</p>
              <p className="mt-2 text-sm text-muted">{profile?.resumeName ?? 'No PDF uploaded yet'}</p>
            </div>
          </aside>
        </div>
      )}
    </SiteShell>
  );
}
