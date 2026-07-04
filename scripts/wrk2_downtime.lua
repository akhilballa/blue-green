local total = 0
local failures = 0
local first_failure_index = nil
local last_failure_index = nil
local configured_rate = tonumber(os.getenv("DOWNTIME_REQUEST_RATE") or "0")

function response(status, headers, body)
  total = total + 1
  if status < 200 or status >= 300 then
    failures = failures + 1
    if first_failure_index == nil then
      first_failure_index = total
    end
    last_failure_index = total
  end
end

function done(summary, latency, requests)
  local estimated_window_ms = 0
  if configured_rate > 0 and first_failure_index ~= nil and last_failure_index ~= nil then
    estimated_window_ms = ((last_failure_index - first_failure_index + 1) / configured_rate) * 1000
  end

  io.write("\nDowntime approximation from non-2xx responses\n")
  io.write(string.format("total_responses=%d\n", total))
  io.write(string.format("failed_responses=%d\n", failures))
  io.write(string.format("configured_request_rate=%s\n", tostring(configured_rate)))
  io.write(string.format("estimated_failure_window_ms=%.3f\n", estimated_window_ms))
end
