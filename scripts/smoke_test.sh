#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"
SERVICES=(catalog cart checkout payment user)

curl -fsS "$BASE_URL/health" >/dev/null

for service in "${SERVICES[@]}"; do
  printf "checking %s... " "$service"
  curl -fsS "$BASE_URL/api/$service/health" >/dev/null
  printf "ok\n"
done

printf "smoke test passed for %s\n" "$BASE_URL"
