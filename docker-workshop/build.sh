#!/usr/bin/env bash
set -euo pipefail
# Compatibility entry point; the deployment lives at the repository root.
exec bash "$(dirname "${BASH_SOURCE[0]}")/../build.sh" "$@"
