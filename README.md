# Give a Coding Agent Useful Memory

A 90-minute workshop, Part 2 of the coding agent series. Starting from a working coding agent, attendees add **Redis Agent Memory** so it remembers their preferences across sessions, and **Redis Agent Playbook** so it follows the team's published procedure. See the [schedule](WORKSHOP.md) and the [facilitator guide](FACILITATOR.md).

## Run it

Copy `.env.example` to `.env` and fill in the model, Agent Memory and Playbook settings. Then:

```bash
uv sync --group iris
uv run --group iris python main.py
```

Type a task, or `/help` for commands; typing `/` shows suggestions as you type, from Redis autocomplete (start the workshop's Redis with `docker compose up -d redis`). Learners edit `agent.py`; the agent works in `project/`.

## Browser workshop

```bash
bash start.sh
```

Open http://localhost:8080 for the instructions, editor and terminal side by side. The panel menu also has **Agent Memory** (this workspace's sessions, memories and store settings) and **Redis Insight**. To self-host Agent Memory instead of using the hosted service, see `docker-compose.selfhost.yml`. Stop it with `docker compose down`. Learner work lives in `.workshop-memory/` and survives restarts. See [browser setup](docker-workshop/README.md).

## What's here

- `agent.py`: the learner's agent. Part 1's loop, plus `handle`, which does one task from start to finish; each section switches on one of its flags (`CAPTURE`, `RECALL`, `PLAYBOOK`). `main.py`, `runtime.py`, `playbook.py`, `tools.py`, `ui.py` and `context.py` are the supplied runtime.
- `project/`: the small project the agent works in; its `AGENTS.md` holds the project's conventions.
- `skills/report-validation/`: the team skill published to Playbook.
- `agent-memory/`: the Agent Memory inspector panel, and setup for self-hosting.
- `docs/deck/`: the presenter deck's source (the Claude Slides artifact). `python3 scripts/render_slides.py` renders it to `docs/images/slides/`, which each lesson shows through `docs/slides/<lesson>.md`.
- `docs/tasks/`: the lessons. After editing them, run `uv run python scripts/publish_docs.py` to refresh the browser copies.
- `tests/`: tests for the workshop runtime (`uv run --group iris pytest`).
