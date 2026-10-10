#!/usr/bin/env bash
# The hosted lab invokes this entry point to build and start the workshop.
# For image builds only, use: docker compose build
set -euo pipefail
exec bash "$(dirname "${BASH_SOURCE[0]}")/start.sh" "$@"
