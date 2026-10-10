#!/usr/bin/env bash
# Run on macOS/Linux (or Linux inside WSL): bash install-requirements.sh
# Installs uv if missing, then installs the requirements into .venv.
# Official installation guide: https://docs.astral.sh/uv/getting-started/installation/
# Packages are installed into .venv beside this script.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Make the default install location available in this same Bash session.
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv >/dev/null 2>&1; then
        echo "Error: uv was not found after installation. Check the installer output for its location." >&2
        exit 1
    fi
fi

if [[ ! -d .venv ]]; then
    uv venv --python 3.12 .venv
fi

uv pip install --python .venv/bin/python \
    'fastapi>=0.141.1' \
    'uvicorn[standard]>=0.34' \
    'pydantic>=2.10' \
    'pydantic-settings>=2.15' \
    'redisvl==0.26.0' \
    'onnxruntime>=1.23,<2' \
    'tokenizers>=0.22,<1' \
    'huggingface-hub>=0.34,<2' \
    'numpy>=2,<3' \
    'httpx>=0.28' \
    'redis-agent-memory>=0.4.1' \
    'jsonschema>=4.26,<5' \
    'referencing>=0.37,<1'
