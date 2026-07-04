# Experiment Plan

## Research Question

Can an Ansible-driven Nginx blue-green switch keep observed application downtime below 100 ms for a 5-service containerised microservice demo under simulated production load?

## Hypothesis

If all candidate services are started and health-checked before the Nginx upstream reload, then the observed downtime window during traffic switching should be close to zero and below 100 ms in normal local test conditions.

## Independent Variables

- Target color: blue or green
- Request rate: 100, 500, or 1000 requests per second depending on host capacity
- Connection count: 64, 128, or 256
- Health-check retry and delay thresholds

## Dependent Variables

- Failed response count
- Non-2xx response percentage
- Approximate failure window in milliseconds
- Latency distribution before, during, and after switchover

## Procedure

1. Start the stack with `make up`.
2. Run `make smoke`.
3. Start load with `scripts/run_load_test.sh`.
4. During the load test, run `make deploy-green`.
5. Save the output in `results/`.
6. Repeat for `make deploy-blue`.
7. Repeat each direction at least three times.
8. Compare failed response counts and latency distributions.

## Result Table Template

| Run | Start Color | Target Color | Rate | Duration | Failed Responses | Failure Window ms | p99 Latency | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | blue | green | 100 | 60s | TBD | TBD | TBD | TBD |
| 2 | green | blue | 100 | 60s | TBD | TBD | TBD | TBD |

## Validity Notes

Local Docker tests are useful for demonstrating the mechanism, but they do not fully represent production network behavior. For stronger evidence, repeat the experiment on separate hosts with realistic resource limits, external load generation, and independent observability.
