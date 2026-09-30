#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8000}"
curl -sS -i "$BASE_URL/api/v1/profile"
