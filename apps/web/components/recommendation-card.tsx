import Link from 'next/link';
import { apiClient, Recommendation } from '@/lib/api-client';

export function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  const statusClasses = {
    PENDING_REVIEW: 'border-blue-200 bg-blue-50 text-blue-800',
    APPROVED: 'border-primary/30 bg-emerald-50 text-emerald-800',
    SKIPPED: 'border-accent/30 bg-red-50 text-red-700',
  };

  return (
    <article className="rounded-2xl border border-border bg-white p-5 shadow-soft">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-muted">{recommendation.company}</p>
          <h3 className="mt-2 font-heading text-2xl font-bold text-text">{recommendation.title}</h3>
          <p className="mt-1 text-sm text-muted">{recommendation.location}</p>
        </div>
        <div className="rounded-full border border-border bg-surface px-3 py-1 text-sm font-semibold text-primary">
          {recommendation.matchPercentage}% match
        </div>
      </div>

      <div className="mt-5 flex items-center gap-2">
        <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${statusClasses[recommendation.status]}`}>
          {recommendation.status}
        </span>
      </div>

      <div className="mt-5 rounded-xl border border-border bg-surface p-4">
        <p className="text-sm font-semibold text-text">Match evidence</p>
        <p className="mt-2 text-sm leading-6 text-muted">{recommendation.rationale}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {recommendation.matchedSkills.map((skill) => (
            <span key={skill} className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-800">
              {skill}
            </span>
          ))}
          {recommendation.missingSkills.map((skill) => (
            <span key={skill} className="rounded-full bg-orange-100 px-2.5 py-1 text-xs font-medium text-orange-800">
              Missing: {skill}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            className="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
            onClick={async () => {
              await apiClient.updateRecommendationDecision(recommendation.id, 'APPROVE');
              window.location.reload();
            }}
          >
            Approve
          </button>
          <button
            className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent/90"
            onClick={async () => {
              await apiClient.updateRecommendationDecision(recommendation.id, 'SKIP');
              window.location.reload();
            }}
          >
            Skip
          </button>
        </div>
        <Link
          href={recommendation.applicationUrl}
          target="_blank"
          rel="noreferrer"
          className="text-sm font-semibold text-primary underline decoration-2 underline-offset-4"
          onClick={() => apiClient.recordApplicationLinkOpen(recommendation.id)}
        >
          Open employer page
        </Link>
      </div>
    </article>
  );
}
