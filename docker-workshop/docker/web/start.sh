#!/bin/bash
set -euo pipefail

create_session() {
  tmux -f /etc/tmux.conf new-session -d -s workshop -c /workspace \
    'bash -lc "uv sync; clear; echo \"Build a Coding Agent workshop\"; echo; echo \"Open the Instructions panel and start at Stage 1.\"; echo \"Useful commands:\"; echo \"  uv run python first_call.py\"; echo \"  uv run pytest tests/test_agent.py -q\"; echo \"  uv run python main.py\"; echo; exec bash"'
}

if ! tmux -f /etc/tmux.conf has-session -t workshop 2>/dev/null; then
  create_session
fi

ttyd -W -p 7681 bash -lc '
  if ! tmux -f /etc/tmux.conf has-session -t workshop 2>/dev/null; then
    tmux -f /etc/tmux.conf new-session -d -s workshop -c /workspace \
      "bash -lc \"uv sync; clear; echo Build a Coding Agent workshop; exec bash\""
  fi
  exec tmux -f /etc/tmux.conf attach-session -t workshop
'
