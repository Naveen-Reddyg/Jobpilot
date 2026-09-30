export type RecommendationStatus = 'PENDING_REVIEW' | 'APPROVED' | 'SKIPPED';

export type Recommendation = {
  id: string;
  title: string;
  company: string;
  location: string;
  matchPercentage: number;
  status: RecommendationStatus;
  matchedSkills: string[];
  missingSkills: string[];
  rationale: string;
  applicationUrl: string;
};

export type Profile = {
  targetJobTitles: string[];
  targetSkills: string[];
  timezone: string;
  resumeName?: string;
};

export type RunHistoryItem = {
  id: string;
  scheduledFor: string;
  status: 'RUNNING' | 'SUCCEEDED' | 'PARTIAL' | 'FAILED';
  jobsChecked: number;
  recommendationsCreated: number;
};

export type DiscoveryResult = {
  runId: string;
  provider: string;
  queriedTitles: string[];
  jobsChecked: number;
  recommendationsCreated: number;
};

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface ApiClient {
  getProfile(): Promise<Profile>;
  saveProfile(profile: Partial<Profile>): Promise<Profile>;
  uploadResume(file: File): Promise<{ filename: string }>;
  getRecommendations(): Promise<Recommendation[]>;
  getRunHistory(): Promise<RunHistoryItem[]>;
  getDiscoveryProvider(): Promise<{ provider: string; configured: boolean }>;
  runDiscovery(): Promise<DiscoveryResult>;
  recordApplicationLinkOpen(recommendationId: string): Promise<void>;
  updateRecommendationDecision(recommendationId: string, decision: 'APPROVE' | 'SKIP'): Promise<void>;
}

type ProfileResponse = {
  target_job_titles: string[];
  target_skills: string[];
  timezone: string;
  resume: { filename: string } | null;
};

type RecommendationResponse = {
  id: string;
  job: { title: string; company: string; location: string; application_url: string };
  match_percentage: number;
  matched_skills: string[];
  missing_skills: string[];
  rationale: string;
  status: RecommendationStatus;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string; error?: { message?: string } } | null;
    throw new ApiError(response.status, body?.error?.message ?? body?.detail ?? response.statusText);
  }
  return response.json() as Promise<T>;
}

function mapProfile(profile: ProfileResponse): Profile {
  return {
    targetJobTitles: profile.target_job_titles,
    targetSkills: profile.target_skills,
    timezone: profile.timezone,
    resumeName: profile.resume?.filename,
  };
}

export const apiClient: ApiClient = {
  async getProfile() {
    return mapProfile(await request<ProfileResponse>('/v1/profile'));
  },

  async saveProfile(profile) {
    const response = await request<{ profile: Omit<ProfileResponse, 'resume'> }>('/v1/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_job_titles: profile.targetJobTitles ?? [],
        target_skills: profile.targetSkills ?? [],
        timezone: profile.timezone ?? 'UTC',
      }),
    });
    return mapProfile({ ...response.profile, resume: null });
  },

  async uploadResume(file) {
    const body = new FormData();
    body.set('file', file);
    return request<{ filename: string }>('/v1/resume', { method: 'POST', body });
  },

  async getRecommendations() {
    const response = await request<{ items: RecommendationResponse[] }>('/v1/recommendations');
    return response.items.map((item) => ({
      id: item.id,
      title: item.job.title,
      company: item.job.company,
      location: item.job.location,
      matchPercentage: item.match_percentage,
      status: item.status,
      matchedSkills: item.matched_skills,
      missingSkills: item.missing_skills,
      rationale: item.rationale,
      applicationUrl: item.job.application_url,
    }));
  },

  async getRunHistory() {
    const response = await request<{
      items: Array<{
        id: string;
        scheduled_for: string;
        status: RunHistoryItem['status'];
        jobs_checked: number;
        recommendations_created: number;
      }>;
    }>('/v1/history/runs');
    return response.items.map((item) => ({
      id: item.id,
      scheduledFor: item.scheduled_for,
      status: item.status,
      jobsChecked: item.jobs_checked,
      recommendationsCreated: item.recommendations_created,
    }));
  },

  async getDiscoveryProvider() {
    return request<{ provider: string; configured: boolean }>('/v1/discovery/provider');
  },

  async runDiscovery() {
    const response = await request<{
      run_id: string;
      provider: string;
      queried_titles: string[];
      jobs_checked: number;
      recommendations_created: number;
    }>('/v1/discovery/run', { method: 'POST' });
    return {
      runId: response.run_id,
      provider: response.provider,
      queriedTitles: response.queried_titles,
      jobsChecked: response.jobs_checked,
      recommendationsCreated: response.recommendations_created,
    };
  },

  async recordApplicationLinkOpen(recommendationId) {
    await request(`/v1/recommendations/${recommendationId}/application-link-opened`, { method: 'POST' });
  },

  async updateRecommendationDecision(recommendationId, decision) {
    await request(`/v1/recommendations/${recommendationId}/decision`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision }),
    });
  },
};