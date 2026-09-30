'use client';

import { useEffect, useState } from 'react';
import { SiteShell } from '@/components/site-shell';
import { apiClient, RunHistoryItem } from '@/lib/api-client';

export default function HistoryPage() {
  const [runs, setRuns] = useState<RunHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .getRunHistory()
      .then(setRuns)
      .catch(() => setLoadError('Unable to load discovery run history.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <SiteShell>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">Run History</p>
        <h2 className="mt-2 font-heading text-4xl font-bold text-text">Scheduled discovery runs</h2>
      </div>

      <div className="overflow-hidden rounded-3xl border border-border bg-white shadow-soft">
        <table className="min-w-full divide-y divide-border text-left">
          <thead className="bg-surface">
            <tr>
              <th className="px-5 py-4 text-xs font-semibold uppercase tracking-[0.2em] text-muted">Scheduled time</th>
              <th className="px-5 py-4 text-xs font-semibold uppercase tracking-[0.2em] text-muted">Status</th>
              <th className="px-5 py-4 text-xs font-semibold uppercase tracking-[0.2em] text-muted">Jobs checked</th>
              <th className="px-5 py-4 text-xs font-semibold uppercase tracking-[0.2em] text-muted">Recommendations</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {loadError ? (
              <tr>
                <td colSpan={4} role="alert" className="px-5 py-10 text-center text-accent">{loadError}</td>
              </tr>
            ) : loading ? (
              <tr>
                <td colSpan={4} className="px-5 py-10 text-center text-muted">
                  Loading run history…
                </td>
              </tr>
            ) : runs.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-5 py-10 text-center text-muted">
                  No discovery runs yet.
                </td>
              </tr>
            ) : (
              runs.map((run) => (
                <tr key={run.id} className="hover:bg-surface/70">
                  <td className="px-5 py-4 text-sm text-text">{run.scheduledFor}</td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${
                        run.status === 'SUCCEEDED'
                          ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                          : run.status === 'PARTIAL'
                            ? 'border-amber-200 bg-amber-50 text-amber-800'
                            : 'border-red-200 bg-red-50 text-red-700'
                      }`}
                    >
                      {run.status}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-sm text-text">{run.jobsChecked}</td>
                  <td className="px-5 py-4 text-sm text-text">{run.recommendationsCreated}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </SiteShell>
  );
}
