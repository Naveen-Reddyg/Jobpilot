#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8000}"
curl -sS -i -X PUT "$BASE_URL/api/v1/profile" \
  -H "Content-Type: application/json" \
  --data '{"target_job_titles":["Platform Engineer","Data Engineer"],"target_skills":["Python","PostgreSQL","FastAPI"],"timezone":"UTC"}'
