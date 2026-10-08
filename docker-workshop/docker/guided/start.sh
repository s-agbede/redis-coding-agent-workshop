#!/bin/bash
set -euo pipefail

cd /workspace
uv sync --frozen

tmux -f /etc/tmux.conf new-session -d -s workshop -c /workspace \
  'printf "Build a Coding Agent\n\nCode and Terminal share /workspace. Save with Ctrl/Cmd+S before running.\nFollow the Instructions panel before filling the exercises.\nUse Run code beside a shell command to run it here.\n\n"; exec bash --noprofile --rcfile /opt/editor/terminal.bash -i'

mkdir -p /opt/code-server/User
if [ ! -f /opt/code-server/User/settings.json ]; then
  cat > /opt/code-server/User/settings.json <<'EOF'
{
  "workbench.startupEditor": "none",
  "workbench.colorTheme": "Default Dark Modern",
  "chat.disableAIFeatures": true,
  "workbench.secondarySideBar.defaultVisibility": "hidden",
  "files.autoSave": "off",
  "files.hotExit": "onExitAndWindowClose",
  "terminal.integrated.cwd": "/workspace",
  "terminal.integrated.defaultProfile.linux": "bash",
  "python.defaultInterpreterPath": "/opt/student/.venv/bin/python"
}
EOF
fi

code-server --auth none --bind-addr 0.0.0.0:8080 --disable-telemetry --disable-update-check \
  --disable-workspace-trust --user-data-dir /opt/code-server \
  --extensions-dir /opt/code-server/extensions /workspace &
code_pid=$!

/opt/editor/.venv/bin/uvicorn app:app --app-dir /opt/editor --host 0.0.0.0 --port 8081 &
editor_pid=$!
ttyd -W --check-origin -p 7681 --base-path /terminal -t fontSize=13 -t disableLeaveAlert=true \
  tmux -f /etc/tmux.conf attach-session -t workshop &
terminal_pid=$!

cleanup() {
  kill "$code_pid" "$editor_pid" "$terminal_pid" 2>/dev/null || true
  tmux kill-session -t workshop 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 0' TERM INT
# Code, editor API and Terminal share one Python environment and lifecycle.
wait -n "$code_pid" "$editor_pid" "$terminal_pid"
