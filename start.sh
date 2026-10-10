#!/usr/bin/env bash
# Start the complete browser workshop. Requires Docker with Compose.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

compose=(docker compose)
if [[ -f .env ]]; then
    compose+=(--env-file .env)
elif [[ -f docker-workshop/.env ]]; then
    compose+=(--env-file docker-workshop/.env)
fi

exec "${compose[@]}" up --build -d --wait "$@"
