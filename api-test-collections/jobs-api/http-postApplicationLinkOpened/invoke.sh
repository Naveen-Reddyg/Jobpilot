#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8000}"
RECOMMENDATION_ID="${RECOMMENDATION_ID:-00000000-0000-4000-8000-000000000099}"
curl -sS -i -X POST "$BASE_URL/api/v1/recommendations/$RECOMMENDATION_ID/application-link-opened"
