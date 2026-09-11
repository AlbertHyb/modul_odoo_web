#!/usr/bin/env bash
set -Eeuo pipefail

python3 -m unittest discover -s tests -v
for script in deploy/ci/*.sh deploy/server/*.sh; do
    bash -n "$script"
done
docker compose --env-file deploy/compose/.env.example -f deploy/compose/compose.yaml config >/dev/null
