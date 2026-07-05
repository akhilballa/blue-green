-- Load-generator script for blue-green downtime measurement.
--
-- Two jobs:
--   1. delay()  -> paces requests to a constant rate. Plain `wrk` has no
--      built-in rate limiting (it sends as fast as it can, which overloads the
--      tiny demo service and produces failures even when nothing is deployed).
--      Pacing keeps a steady run at ~0 failures, so the only thing that can
--      cause failures is an actual colour switch. (wrk2 uses -R instead, so
--      pacing is disabled for wrk2 to avoid double-limiting.)
--   2. done()   -> prints a correct summary from wrk's aggregated `summary`
--      object (the old version hand-counted per-thread and always showed 0).

local pacing      = (os.getenv("LOAD_PACING") == "on")
local target_rate = tonumber(os.getenv("LOAD_TARGET_RATE") or "0") or 0
local connections = tonumber(os.getenv("LOAD_CONNECTIONS") or "0") or 0

-- With N connections each waiting (N / rate) seconds between requests, the
-- aggregate request rate is exactly `target_rate`.
local per_conn_interval_ms = 0
if pacing and target_rate > 0 and connections > 0 then
  per_conn_interval_ms = (connections / target_rate) * 1000
end

function delay()
  return per_conn_interval_ms
end

function done(summary, latency, requests)
  local total    = summary.requests
  local failed   = summary.errors.status   -- HTTP non-2xx / 3xx responses
  local timeouts = summary.errors.timeout  -- requests that never got a reply
  local dur_s    = summary.duration / 1e6  -- summary.duration is microseconds
  local rate     = dur_s > 0 and (total / dur_s) or 0

  -- Rough downtime estimate: at the achieved rate, how long a window it would
  -- take to accumulate this many failed/timed-out requests.
  local downtime_ms = rate > 0 and (((failed + timeouts) / rate) * 1000) or 0

  io.write("\nDowntime summary\n")
  io.write(string.format("total_requests=%d\n", total))
  io.write(string.format("failed_responses=%d\n", failed))
  io.write(string.format("timed_out=%d\n", timeouts))
  io.write(string.format("p99_latency_ms=%.2f\n", latency:percentile(99) / 1000))
  io.write(string.format("estimated_downtime_ms=%.1f\n", downtime_ms))
end
