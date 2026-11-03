# Give a Coding Agent Useful Memory

A 90-minute workshop, Part 2 of the coding agent series. Starting from a working coding agent, attendees add **Redis Agent Memory** so it remembers their preferences across sessions, and **Redis Agent Playbook** so it follows the team's published procedure. See the [schedule](WORKSHOP.md) and the [facilitator guide](FACILITATOR.md).

## Run it

Copy `.env.example` to `.env` and fill in the model, Agent Memory and Playbook settings. Then:

```bash
uv sync --group iris
uv run --group iris python main.py
```

Type a task, or `/help` for commands. Learners edit `agent.py`; the agent works in `project/`.

## Browser workshop

```bash
bash start.sh
```

Open http://localhost:8080 for the instructions, editor and terminal side by side. The panel menu also has **Agent Memory** (this workspace's sessions, memories and store settings) and **Redis Insight**. To self-host Agent Memory instead of using the hosted service, see `docker-compose.selfhost.yml`. Stop it with `docker compose down`. Learner work lives in `.workshop-memory/` and survives restarts. See [browser setup](docker-workshop/README.md).

## What's here

- `agent.py`: the learner's agent. `main.py`, `runtime.py`, `playbook.py`, `tools.py`, `ui.py` and `context.py` are the supplied runtime.
- `project/`: the small report project the agent works in, with its tests.
- `skills/report-validation/`: the team skill published to Playbook.
- `solutions/steps/`: ready-made `agent.py` for each section; `solutions/validator.py` is a reference answer.
- `agent-memory/`: the Agent Memory inspector panel, and setup for self-hosting.
- `docs/tasks/`: the lessons. After editing them, run `uv run python scripts/publish_docs.py` to refresh the browser copies.
- `tests/`: tests for the workshop runtime (`uv run --group iris pytest`).
