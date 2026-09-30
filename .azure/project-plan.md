# Project Plan

**Status**: Integrated
**Created**: 2026-09-30
**Mode**: NEW
**Execution Mode**: auto

---

## 1. Project Overview

**Goal**: Build a job recommendation portal where users manage their target roles, resume uploads, and generated job matches. The project is designed so that every module is independently testable.

**App Type**: SPA + API

**API Login**: Yes

**Mode**: NEW

**Deployment Plan**: No deployment plan found

---

## 2. Jobs API — backend

| Component | Technology |
|-----------|-----------|
| **Language** | Python |
| **Runtime** | CPython |
| **Package Manager** | pip |
| **Test Runner** | pytest |
| **Mocking Library** | unittest.mock |
| **Test Command** | pytest |
| **Orchestration** | docker-compose |

---

## 3. Job Recommendation Portal — frontend

| Component | Technology |
|-----------|-----------|
| **Language** | TypeScript |
| **Framework** | Next.js |
| **Package Manager** | npm |
| **Test Runner** | vitest |
| **Mocking Library** | vi.mock |
| **Test Command** | npm test |

---

## 4. Scheduled Discovery and Agent Worker — worker

| Component | Technology |
|-----------|-----------|
| **Language** | Python |
| **Runtime** | CPython |
| **Package Manager** | pip |
| **Test Runner** | pytest |
| **Mocking Library** | unittest.mock |
| **Test Command** | pytest |
| **Orchestration** | docker-compose |

---

## 5. Services Required

| Azure Service | Role in App | Environment Variable | Default Value (Local) | Classification |
|---------------|------------|---------------------|----------------------|----------------|
| Blob Storage | Store and retrieve resume PDFs and signed file metadata | STORAGE_CONNECTION_STRING | UseDevelopmentStorage=true | Essential |
| PostgreSQL | Primary relational data store for profiles, recommendations, and run history | DATABASE_URL | postgresql://jobsync:jobsync_dev@localhost:5432/jobsync | Essential |

---

## 6. Prerequisites

### Run

| Tool | Service(s) | Installed | Version |
|------|------------|-----------|---------|
| Node.js | Job Recommendation Portal | ✅ | v26.10.0 |
| npm | Job Recommendation Portal | ✅ | 11.19.1 |
| Python | Jobs API, Discovery Worker | ✅ | 3.14.7 |
| pip | Jobs API, Discovery Worker | ✅ | 26.0.1 |
| Docker | Jobs API, Discovery Worker | ✅ | 29.8.1 |
| Docker Compose | Jobs API, Discovery Worker | ✅ | v5.5.1 |

### Debug

| Tool | Service(s) | Installed | Version |
|------|------------|-----------|---------|
| Chrome | Job Recommendation Portal | ✅ | 154.0.8037.93 |
| Docker | Jobs API, Discovery Worker | ✅ | 29.8.1 |
| Docker Compose | Jobs API, Discovery Worker | ✅ | v5.5.1 |

---

## 7. Design System & UI

**Component Library**: Fluent UI v9
**Style Direction**: Modern, low-noise job review experience with compact cards, strong hierarchy, and subtle status colors. The interface emphasizes quick scanning of recommended roles, clear match evidence, and confident actions without visual clutter.
**Typography**: Inter, system-ui

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `primary` | `#1D4ED8` | Primary actions, navigation, active jobs |
| `accent` | `#F59E0B` | Secondary emphasis, alerts, and status highlights |
| `surface` | `#F8FAFC` | Page background and neutral panels |
| `text` | `#0F172A` | Main body text and title hierarchy |
| `muted` | `#475569` | Metadata, timestamps, and helper text |
| `border` | `#E2E8F0` | Card edges, dividers, and input outlines |

### Pages

| Page | Route | Purpose | Layout |
|------|-------|---------|--------|
| Review Queue | `/` | Surface ranked roles with match explanations and review actions | `header + hero + card-list + actions` |
| Profile Setup | `/setup` | Capture target roles, skills, and resume status | `header + form + actions` |
| Run History | `/history` | Show scheduled discovery outcomes and recommendation counts | `header + tabs + table + footer` |

### Sample Content

Review Queue — opportunity:
| Role | Company | Match | Status |
|------|---------|-------|--------|
| Senior Backend Engineer | Northstar Labs | 94% | Approved |
| Data Platform Engineer | BlueOrbit | 88% | In Review |
| ML Infrastructure Engineer | Signal Forge | 81% | Saved |

Profile Setup — target profile: Senior Python Engineer · Remote / Austin · Skills: Python, FastAPI, PostgreSQL, Docker

Run History — discovery run:
| Started | Source | Jobs Checked | Recommendations |
|---------|--------|--------------|----------------|
| 2026-09-30 06:00 UTC | Public ATS feed | 42 | 17 |
| 2026-09-29 18:00 UTC | Public ATS feed | 31 | 11 |
| 2026-09-29 06:00 UTC | Public ATS feed | 27 | 9 |

---

## 8. Project Structure

```text
Job_applier_agent/
├── .azure/
│   ├── project-plan.md
│   ├── requirements.json
│   └── .preview-temp/
├── apps/
│   └── web/
│       ├── app/
│       │   ├── globals.css
│       │   ├── layout.tsx
│       │   ├── page.tsx
│       │   ├── history/
│       │   │   └── page.tsx
│       │   └── setup/
│       │       └── page.tsx
│       ├── components/
│       ├── lib/
│       ├── public/
│       ├── package.json
│       ├── next.config.mjs
│       └── tsconfig.json
├── services/
│   └── jobs/
│       ├── app/
│       │   ├── api/
│       │   ├── agents/
│       │   ├── database.py
│       │   ├── models/
│       │   └── settings/
│       ├── migrations/
│       ├── tests/
│       ├── api_main.py
│       ├── worker_main.py
│       ├── Dockerfile
│       └── requirements.txt
├── api-test-collections/
├── compose.yaml
├── src/
└── source/
```

---

## 9. Route Definitions

| # | Method | Path | Description | Request Body | Response Body | Status Codes |
|---|--------|------|-------------|-------------|--------------|-------------|
| 1 | GET | `/api/health` | Health check for API and required services | — | `{ status, services }` | 200, 503 |
| 2 | GET | `/api/profile` | Read the current user's profile and resume metadata | — | `{ target_job_titles, target_skills, resume_status }` | 200, 404 |
| 3 | PUT | `/api/profile` | Update target titles and skills | `{ target_job_titles, target_skills, timezone }` | `{ profile }` | 200, 422 |
| 4 | POST | `/api/resume` | Upload and validate a PDF resume | `multipart/form-data: file` | `{ id, filename, size_bytes, uploaded_at }` | 201, 413, 415, 422 |
| 5 | GET | `/api/recommendations` | Retrieve the current recommendation queue | Query: `status`, `limit` | `{ items: [{ id, title, company, score, rationale, status }] }` | 200, 422 |
| 6 | PATCH | `/api/recommendations/{id}/decision` | Approve or skip a recommendation | `{ decision: "APPROVE" | "SKIP" }` | `{ id, status, decided_at }` | 200, 404, 409, 422 |
| 7 | POST | `/api/application-link-opened` | Record user action when the external application page is opened | `{ recommendation_id }` | `{ recorded: true }` | 202, 404 |
| 8 | GET | `/api/history/runs` | Read scheduled discovery runs and summarized results | Query: `limit` | `{ items: [{ id, started_at, status, jobs_checked, recommendations_created }] }` | 200, 422 |

---

## 10. Next Steps

1. Run azure-project-scaffold to execute this plan
2. Run azure-project-integrate to wire the frontend to live data, smoke-test the backend, and create the migrations
3. Run azure-debug-plan → azure-debug-generate for Docker emulators and VS Code debugging
4. Run the azure-deploy agent when ready; it uses azure-app-onboard for architecture, cost estimation, IaC generation, provisioning, and health verification
