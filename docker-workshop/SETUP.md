# Workbench setup

1. Install Docker with Compose.
2. In `docker-workshop/`, create `.env` from `.env.example` only if absent.
3. Set `AGENT_API_KEY` and optionally `AGENT_BASE_URL` / `AGENT_MODEL` for live work.
4. Run `docker compose up --build -d`.
5. Open http://localhost:8080 and begin in Instructions.

The workbench embeds the guided lessons, VS Code, Terminal and App Preview. Code
and both terminals share `/workspace` and the same Python environment. The model
key goes only to the runtime, never into frontend assets.

Use `docker compose logs runtime` for startup failures and `docker compose ps`
to check readiness. The runtime is ready when Code, the file API and Terminal
respond. The first build may take several minutes.

The Compose project remains `coding-agent-guided`, preserving the student directory
from the previous guided interface. Upgrading restarts running terminals/preview;
save edits first. A separate Debian virtualenv volume replaces the Alpine runtime
environment without deleting its old volume or learner code.

See [README.md](README.md) for panel controls, validation and shutdown commands,
and [UPSTREAM.md](UPSTREAM.md) for the pinned workbench and guide sources.
