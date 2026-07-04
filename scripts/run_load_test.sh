#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL="${1:-http://localhost:8080/api/catalog}"
DURATION="${2:-60s}"
RATE="${3:-100}"
THREADS="${THREADS:-4}"
CONNECTIONS="${CONNECTIONS:-64}"
OUT_DIR="$ROOT_DIR/results"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT_FILE="$OUT_DIR/loadtest-$STAMP.txt"

mkdir -p "$OUT_DIR"
export DOWNTIME_REQUEST_RATE="$RATE"

if command -v wrk2 >/dev/null 2>&1; then
  CMD=(wrk2 -t"$THREADS" -c"$CONNECTIONS" -d"$DURATION" -R"$RATE" -s "$ROOT_DIR/scripts/wrk2_downtime.lua" "$URL")
elif command -v wrk >/dev/null 2>&1; then
  printf "wrk2 not found; falling back to wrk without constant-rate scheduling.\n" | tee "$OUT_FILE"
  CMD=(wrk -t"$THREADS" -c"$CONNECTIONS" -d"$DURATION" -s "$ROOT_DIR/scripts/wrk2_downtime.lua" "$URL")
else
  printf "Neither wrk2 nor wrk is installed. Install wrk2 for constant-rate downtime measurement.\n" >&2
  exit 1
fi

{
  printf "url=%s\n" "$URL"
  printf "duration=%s\n" "$DURATION"
  printf "rate=%s\n" "$RATE"
  printf "threads=%s\n" "$THREADS"
  printf "connections=%s\n" "$CONNECTIONS"
  printf "started_at=%s\n\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf "command:"
  printf " %q" "${CMD[@]}"
  printf "\n\n"
  "${CMD[@]}"
} | tee -a "$OUT_FILE"

printf "\nSaved result to %s\n" "$OUT_FILE"
