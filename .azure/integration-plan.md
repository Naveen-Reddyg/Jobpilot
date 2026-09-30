# Integration hand-off

## Backend
- Project folder: `services/jobs`
- Run command: `cd services/jobs && uvicorn app.api.main:app --host 0.0.0.0 --port 8000`
- Build command: `cd services/jobs && python -m compileall .`
- Health endpoint: `GET /api/health`
- Worker entry: `cd services/jobs && python worker_main.py`

## Frontend
- Project folder: `apps/web`
- Dev command: `cd apps/web && npm run dev`
- Build command: `cd apps/web && npm run build`
- API seam: `apps/web/lib/api-client.ts`
- Mock data files to replace: `apps/web/lib/api-client.ts`
- Local preview state files: not required for this scaffold; all API access is centralized in `apiClient`

## API routes
- `GET /api/health`
- `GET /api/v1/profile`
- `PUT /api/v1/profile`
- `GET /api/v1/recommendations`
- `PATCH /api/v1/recommendations/{id}/decision`
- `POST /api/v1/recommendations/{id}/application-link-opened`
- `GET /api/v1/history/runs`
- `POST /api/v1/resume`

## Database
- Type: PostgreSQL
- Migration directory: `services/jobs/migrations`
- Migration tool: SQL migration files + application startup validation
- Connection env var: `DATABASE_URL`
- Seed policy: no seed data; create schema only

## Shared types
- Shared seam: `apps/web/lib/api-client.ts`
- Typed client contract: `ApiClient` interface

## Services
- Essential: `web`, `api`, `discovery-worker`, `postgres`, `azurite`
- Enhancement: configurable LLM provider selection (`LLM_PROVIDER`, `LLM_MODEL`)

## Verification checklist
- Smoke-test health endpoint
- Confirm profile and recommendations endpoints respond
- Confirm history returns results
- Confirm frontend loads live-data pages with API-backed empty states
- Run frontend production build
- Validate migration folder and env docs

## Integration results

- Applied the PostgreSQL schema at API startup. The migration creates `users`, `user_profiles`, `resume_assets`, `source_feeds`, `jobs`, `discovery_runs`, `recommendations`, and `application_link_events`, with constraints and indexes; a matching down migration is available. The schema was verified with zero rows before UI testing, and no migration seed data was added.
- Backend smoke checks: `/api/health` returned 200 with database and storage healthy; profile/recommendation/history reads and invalid or missing write requests returned clean 200, 404, or 422 responses. All eight documented routes were exercised without a 500 response.
- Replaced the frontend mock client and page examples with typed live API calls. Profile reads/saves and PDF upload use the API; recommendations and run history show database-backed empty states. The Next.js `/api` rewrite targets the API service.
- End-to-end verification: the browser loaded the review and history pages from the running web service; saving a profile in Setup returned success, and the saved profile was read back through `http://localhost:3000/api/v1/profile` with 200. API logs confirmed proxied GET/PUT requests.
- Verification passed: `npm --prefix apps/web run build`, API Python compile, PostgreSQL table inspection, and route smoke checks.
- Authentication is not part of the scaffold route inventory. The local API currently scopes requests to the configured `LOCAL_USER_ID`; real login and identity enforcement remain necessary before multi-user or production use.
- Reverification: all eight API routes returned successful or expected validation/not-found statuses, and the Next.js history page rendered the API-backed empty state. Browser-side `GET` → `PUT` → `GET /api/v1/profile` through the `/api` rewrite returned 200 at each step and preserved the existing profile values.
