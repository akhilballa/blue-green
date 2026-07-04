# Tutorial Draft: Zero-Downtime Blue-Green Deployments with Ansible and Nginx

## Introduction

Blue-green deployment is a release strategy where two production-like environments exist side by side. One environment serves live traffic while the other receives the next release. After the new release passes health checks, traffic moves to it in one controlled switch.

This project implements that strategy for a 5-service containerised application using Docker Compose, Nginx, and Ansible.

## What You Will Build

- A demo microservice application with `catalog`, `cart`, `checkout`, `payment`, and `user` services.
- Blue and green copies of every service.
- An Nginx gateway that routes to the active color.
- A reusable Ansible role that performs health-gated switchovers.
- A rollback playbook.
- A wrk2-based load-test harness for measuring application downtime.

## Step 1: Start the Stack

```bash
make up
```

This builds the shared service image and starts Nginx plus both blue and green service pools. The default active color is blue.

## Step 2: Check the Current Active Color

```bash
curl -s http://localhost:8080/api/catalog | jq
```

The response includes a `color` field. Before the first deployment, it should be `blue`.

## Step 3: Deploy Green

```bash
make deploy-green
```

The playbook starts the green services, checks their local health endpoints, updates the Nginx upstream file, reloads Nginx, then checks the public routes.

## Step 4: Verify the Switch

```bash
curl -s http://localhost:8080/api/catalog | jq
```

The `color` field should now be `green`.

## Step 5: Measure Downtime Under Load

In one terminal:

```bash
scripts/run_load_test.sh http://localhost:8080/api/catalog 60s 100
```

In another terminal:

```bash
make deploy-blue
```

The load-test script reports non-2xx responses and an approximate failure window. For a healthy local environment, the expected result should be near zero failed responses because Nginx reloads gracefully and the target services are already warm.

## Step 6: Roll Back

```bash
make rollback-blue
```

Rollback uses the same health-gated role, but targets the known rollback color.

## Production Considerations

- Use a real inventory instead of local Docker Compose.
- Store deployment state in a durable place, such as a deployment database or service registry.
- Add service-level readiness checks that validate dependencies, schema compatibility, and cache availability.
- Keep blue and green environments isolated enough to avoid cross-color dependency drift.
- Send metrics to a time-series system so downtime can be measured from both client-side and server-side perspectives.

## Conclusion

The important idea is to make the traffic switch a small, reversible operation. The expensive work happens before the switch: build images, start containers, warm services, and verify health. Ansible makes the release flow repeatable, while Nginx provides a simple and fast routing layer.
