#!/usr/bin/env bash
set -Eeuo pipefail

python3 -m unittest discover -s tests -v
for script in deploy/ci/*.sh deploy/server/*.sh deploy/dev/*.sh; do
    bash -n "$script"
done
docker compose --env-file deploy/compose/.env.example -f deploy/compose/compose.yaml config >/dev/null
docker compose -f deploy/dev/compose.yaml config >/dev/null
