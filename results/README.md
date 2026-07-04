# Results

Load-test outputs from `scripts/run_load_test.sh` are written here as timestamped text files.

Suggested experiment:

1. Terminal A: `scripts/run_load_test.sh http://localhost:8080/api/catalog 60s 100`
2. Terminal B: `make deploy-green`
3. Repeat with `make deploy-blue`
4. Copy the key values into `docs/experiment-plan.md`

Track:

- request rate
- test duration
- active color before switch
- target color
- failed response count
- approximate failure window in milliseconds
- p95 and p99 latency
