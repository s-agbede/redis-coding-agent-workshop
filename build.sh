#!/usr/bin/env bash
# Run on macOS/Linux (or Linux inside WSL): bash install-requirements.sh
# Installs uv if missing, then installs the requirements into .venv.
# Official installation guide: https://docs.astral.sh/uv/getting-started/installation/
# Packages are installed into .venv beside this script.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

bash docker-workshop/start.sh
