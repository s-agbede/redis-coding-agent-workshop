# Give a Coding Agent Useful Memory

A 90-minute workshop, Part 2 of the coding agent series, for software engineers with some AI-agent experience. Starting from a working coding agent, the instructor demonstrates each section and attendees follow for five minutes: a preference is forgotten, a project instruction persists, **Redis Agent Memory** captures and recalls a preference, and **Redis Agent Playbook** supplies a published team procedure. The agent then writes a small report validator, checked independently.

Read the [learner welcome](docs/welcome.md), [lesson path](docs/home.md), [schedule](WORKSHOP.md) and [facilitator guide](FACILITATOR.md). The [implementation notes](IMPLEMENTATION.md) distinguish supplied code from live-service and timing evidence.

## Run locally

Preserve any existing `.env`; otherwise copy `.env.example` to `.env`. The instructor supplies model, Agent Memory and Playbook settings privately. From the repository root:

```bash
uv sync --group iris
uv run --group iris python main.py
```

At `You >`, enter `/status` to inspect capability flags, owner/session, configuration readiness and the next action. Enter `/help` for controls. A configured client is not proof of a successful live call. The initial agent works with capture, recall and Playbook disabled; lessons explicitly enable them.

**Learners edit `agent.py`; the agent edits `project/`.** Save Python changes, type `exit`, rerun the launch command in the shell, and inspect `/status`. `/new-session` clears history and reloads project instructions without reloading Python. The stable synthetic owner allows retrieval across sessions.

## Browser workshop

The supplied browser workbench combines instructions, an editor and a shared terminal. From the repository root:

```bash
bash start.sh
```

Open [the local workshop](http://localhost:8080). See [browser setup](docker-workshop/README.md) and [upstream provenance](docker-workshop/UPSTREAM.md). The generated learner workspace is `.workshop-memory/`, mounted at `/workspace`; preserve learner edits when restarting. Stop with `docker compose down`. Use the hosting environment's access controls; local-only access can use `WORKSHOP_BIND_ADDRESS=127.0.0.1` in `.env`.

## Source and authoring

- Root `agent.py` is the learner file. `main.py`, `runtime.py`, `tools.py`, `context.py` and `playbook.py` supply the terminal, loop integration, boundaries and adapters.
- `project/` is the learner's report project. `project-review/` supports an optional instructor demonstration of the same published procedure in another project.
- `skills/report-validation/` supplies the procedure; `challenge/` contains the independent contract, checker and fixtures. Keep these checks unchanged during the exercise.
- `solutions/steps/` contains cumulative catch-up agents. Copying one changes code, not captured events, extracted memories or published skills.
- `docs/tasks/` is the canonical lesson text. `docs/slides/` contains **only minimal labelled placeholders** until slide design is revisited. Learner diagram positions are text placeholders; no PDF is required.
- `docker-workshop/` contains browser deployment and generated content. After canonical documentation changes, run `uv run python scripts/publish_docs.py`; `--check` detects unpublished changes. Do not hand-edit generated lesson copies.
- `tests/` checks workshop behaviour; `archive/` retains historical material, separate from the active learner path.

The schedule is a 4-minute recap, five demo + hands-on sections (amnesiac and files, capture, recall, Playbook, verify), 10 minutes of discussion and 5 of buffer. See [WORKSHOP.md](WORKSHOP.md).

## Evidence and final check

`/events` shows original user/final assistant events, the source for background extraction. `/memories` shows extracted preferences. `/view-context` shows current sources and the exact latest submitted model request. These are distinct checkpoints; the runtime does not restore saved conversation or tool transcripts.

The instructor runs `/publish-skill` once; attendees set `PLAYBOOK_SKILL_ID` to that entry and only need read access. `/skills` inspects the published procedure; the validator task retrieves it into the request when Playbook is enabled. `uv run --group iris python main.py --project project-review` shows the same procedure in a second project.

Run `/verify` in the agent terminal, or exit and run:

```bash
uv run --group iris python challenge/check_contract.py project/validator.py
```

The checker validates the specified contract. Inspect retrieved context and comment quality separately. A reference validator is available in `solutions/validator.py`; using it must be distinguished from a successful agent-generated result.

The Docker learner workspace is `.workshop-memory/`, separate from an older `.workshop/` used by the first workshop. Existing first-workshop work is preserved.
