#!/usr/bin/env bash
# Build the workshop images without starting or restarting services.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
exec docker compose build "$@"
