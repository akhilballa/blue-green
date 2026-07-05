#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p .runtime results

if [[ ! -f .runtime/active_color ]]; then
  printf "blue\n" > .runtime/active_color
fi

docker compose up -d --build

# Nginx resolves upstream container hostnames to IPs once, at config-load time,
# and caches them. Rebuilding/recreating the app containers gives them new IPs,
# so without a reload Nginx keeps routing to the old IPs -- which now belong to
# different containers, making routes point at the wrong service. Reload so it
# re-resolves the current container IPs. (The deploy playbook already reloads.)
docker compose exec -T nginx nginx -s reload >/dev/null 2>&1 || true

printf "\nGateway: http://localhost:8080\n"
printf "Active color: %s\n" "$(tr -d '\n' < .runtime/active_color)"
