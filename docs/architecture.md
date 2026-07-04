# Architecture Notes

## Goal

The project demonstrates zero-downtime blue-green deployments for containerised microservices. The control plane is Ansible, the runtime is Docker Compose, and the traffic switch is an Nginx reload that changes upstream targets from one color to another.

## Components

- `app/service.py` is one reusable HTTP service implementation.
- Docker Compose runs ten service containers: five blue and five green.
- Nginx exposes one public gateway on `localhost:8080`.
- `ansible/roles/blue_green_switcher` owns health checks, upstream rendering, Nginx reload, verification, and rollback.
- `scripts/run_load_test.sh` runs wrk2 or wrk and writes output to `results/`.

## Request Flow

```text
GET /api/catalog
      |
      v
Nginx location /api/catalog
      |
      v
catalog_backend upstream
      |
      v
blue-catalog or green-catalog
```

The same pattern is used for `cart`, `checkout`, `payment`, and `user`.

## Deployment Sequence

1. The operator chooses a target color.
2. Ansible starts the target color containers.
3. Ansible probes `/health` inside each target container.
4. Ansible renders `nginx/conf.d/active-upstreams.conf` with target container names.
5. Nginx reloads configuration without restarting the container.
6. Ansible verifies all public service health routes.
7. The active color is saved to `.runtime/active_color`.

## Rollback Behavior

The role records the previous active color before switching. If public verification fails after the Nginx reload, the role renders the previous upstreams, reloads Nginx again, persists the previous color, and fails the playbook with a clear message.

## Why Nginx Reload

Nginx supports configuration reloads without stopping the master process. Existing worker processes finish in-flight requests while new workers pick up the new upstream configuration. This makes it suitable for fast blue-green traffic switching when the upstream services are already warm and healthy.
