#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p .runtime results

if [[ ! -f .runtime/active_color ]]; then
  printf "blue\n" > .runtime/active_color
fi

docker compose up -d --build

printf "\nGateway: http://localhost:8080\n"
printf "Active color: %s\n" "$(tr -d '\n' < .runtime/active_color)"
