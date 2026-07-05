#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL="${1:-http://localhost:8080/api/catalog}"
DURATION="${2:-60s}"
RATE="${3:-100}"
# Modest concurrency so the paced rate is smooth and the demo service is never
# overloaded during a steady (no-switch) run.
THREADS="${THREADS:-2}"
CONNECTIONS="${CONNECTIONS:-10}"
OUT_DIR="$ROOT_DIR/results"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT_FILE="$OUT_DIR/loadtest-$STAMP.txt"
RAW_FILE="$(mktemp)"
trap 'rm -f "$RAW_FILE"' EXIT

mkdir -p "$OUT_DIR"

# The Lua script uses these to pace requests to a constant rate under plain wrk.
export LOAD_TARGET_RATE="$RATE"
export LOAD_CONNECTIONS="$CONNECTIONS"

# Pick the load tool. wrk2 enforces the rate natively with -R. Plain wrk cannot,
# so we turn on client-side pacing in the Lua script instead.
LUA="$ROOT_DIR/scripts/wrk2_downtime.lua"
if command -v wrk2 >/dev/null 2>&1; then
  TOOL="wrk2"
  RATE_NOTE="enforced (wrk2 -R)"
  export LOAD_PACING="off"
  CMD=(wrk2 -t"$THREADS" -c"$CONNECTIONS" -d"$DURATION" -R"$RATE" -s "$LUA" "$URL")
elif command -v wrk >/dev/null 2>&1; then
  TOOL="wrk"
  RATE_NOTE="enforced (client pacing)"
  export LOAD_PACING="on"
  CMD=(wrk -t"$THREADS" -c"$CONNECTIONS" -d"$DURATION" -s "$LUA" "$URL")
else
  printf "Neither wrk2 nor wrk is installed. Install one (e.g. 'brew install wrk') to run the load test.\n" >&2
  exit 1
fi

printf "Running %s against %s for %s at ~%s req/s...\n\n" "$TOOL" "$URL" "$DURATION" "$RATE"

# Run the test, showing live output while capturing it for parsing.
"${CMD[@]}" | tee "$RAW_FILE"

# Pull the numbers out of the tool's own output. Pure awk (never exits non-zero
# on "no match") plus `|| true`, so a clean run with no error lines can never
# abort the script under `set -e`.
total=$(awk '/requests in/{print $1; exit}' "$RAW_FILE" || true)
failed=$(awk '/Non-2xx or 3xx responses/{print $NF; exit}' "$RAW_FILE" || true)
# "Socket errors: connect A, read B, write C, timeout D" (line only present if >0)
timeouts=$(awk 'match($0,/timeout [0-9]+/){s=substr($0,RSTART,RLENGTH); sub(/timeout /,"",s); print s; exit}' "$RAW_FILE" || true)
net_errors=$(awk '/Socket errors/{print $4+$6+$8; exit}' "$RAW_FILE" || true)  # connect+read+write
avg_latency=$(awk '$1=="Latency" && $2 ~ /^[0-9]/{print $2; exit}' "$RAW_FILE" || true)
throughput=$(awk -F'[: ]+' '/^Requests\/sec:/{print $2; exit}' "$RAW_FILE" || true)

total=${total:-0}; failed=${failed:-0}; timeouts=${timeouts:-0}
net_errors=${net_errors:-0}; avg_latency=${avg_latency:-n/a}; throughput=${throughput:-n/a}

# Total user-visible failures = HTTP errors + timeouts + dropped connections.
bad=$(( failed + timeouts + net_errors ))
if [[ "$total" -gt 0 ]]; then
  pct=$(awk "BEGIN{printf \"%.2f\", ($bad/$total)*100}")
else
  pct="0.00"
fi

if [[ "$bad" -eq 0 ]]; then
  verdict="0 failed requests. This is what a steady (no-switch) run should look like. If you deployed during this run, the switch caused no visible downtime."
else
  verdict="$bad of $total requests failed ($pct%). With the rate capped, a no-switch run should be ~0, so these failures are the impact of a colour switch during this run (the deployment downtime)."
fi

# Write the clean, human-readable report (summary first, raw output last).
{
  printf "===== LOAD TEST RESULT =====\n\n"

  printf "SETUP\n"
  printf "  URL            : %s\n" "$URL"
  printf "  Duration       : %s\n" "$DURATION"
  printf "  Target rate    : %s req/s (%s)\n" "$RATE" "$RATE_NOTE"
  printf "  Load           : %s threads / %s connections\n" "$THREADS" "$CONNECTIONS"
  printf "  Tool           : %s\n" "$TOOL"
  printf "  Started (UTC)  : %s\n\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  printf "RESULT\n"
  printf "  Total requests : %s\n" "$total"
  printf "  Failed (HTTP)  : %s\n" "$failed"
  printf "  Timed out      : %s\n" "$timeouts"
  printf "  Conn errors    : %s\n" "$net_errors"
  printf "  Failure rate   : %s%%\n" "$pct"
  printf "  Avg response   : %s\n" "$avg_latency"
  printf "  Throughput     : %s req/s\n\n" "$throughput"

  printf "VERDICT\n  %s\n\n" "$verdict"

  printf '%s\n' "----- raw ${TOOL} output -----"
  cat "$RAW_FILE"
} > "$OUT_FILE"

printf "\n----------------------------------------\n"
printf "Clean summary saved to %s\n\n" "$OUT_FILE"
sed -n '1,/^----- raw/p' "$OUT_FILE" | sed '$d'
