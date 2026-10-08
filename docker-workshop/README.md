# Coding-agent workshop workbench

The default browser interface uses the configurable workbench from
[semantic-cache-routing-workshop](https://github.com/redis-developer/semantic-cache-routing-workshop),
with our guided coding-agent lessons and a real VS Code editor.
Pinned sources and local adaptations are recorded in [UPSTREAM.md](UPSTREAM.md).

## Start

From this directory, copy `.env.example` to `.env` only if it does not already
exist. Before teaching, configure the model service key and endpoint for the live exercises.
The instructor provides access so learners can focus on the Python code.

```bash
docker compose up --build -d
```

Open **http://localhost:8080**. `WORKSHOP_PORT` chooses another port;
`WORKSHOP_BIND_ADDRESS` defaults to `127.0.0.1`. Each learner needs their own stack.
The first build downloads VS Code and the locked Python dependencies.

The Instructions panel guides you through **Welcome → Workshop**. The seven lessons begin with a FizzBuzz model call and PEAS design, then add conversation history, a plain reader, improved tool output and the agent loop. The final lesson asks the learner's agent to repair and test the task board.

## Workbench panels

| Panel | What to do there |
| --- | --- |
| Instructions | Follow the lessons and open hints or answers when useful. |
| Code | Edit workshop files in VS Code. Click underlined file names in lessons to reveal them here, or use Explorer. Save with Ctrl/Cmd+S. |
| Terminal | Run code sends a lesson shell command here. Read its output. Ctrl+C interrupts; `exit` leaves an agent conversation. |
| App Preview | View the target task-list app. Show it from the panel menu and start its server in the final lesson. |

Use each panel's expand/restore control, drag a divider to resize, and use the
menu to show or hide panels. Layout changes retain editor buffers and terminal
sessions. An explicit panel reload or a runtime restart is different: save first.

Code and Terminal share `student/` at **/workspace**, the same Python environment
and the same processes. VS Code's integrated terminal also uses this environment.
The root project's files are a separate CLI starter. Student files are bind-mounted;
VS Code settings and recovery data live in a named Docker volume. The host's macOS
`.venv` is not used.

VS Code detects saved file changes made by the agent or Terminal. If you have
unsaved edits, compare them with external changes before saving. The exercises are in `first_call.py`, `checkpoints/stage1_chat.py`, `tools.py` and `agent.py`; find the marked gaps. The guided exercises use live calls; their unit tests are grouped in the final evaluation. The capstone has a separate seeded bug; keep its independent checker unchanged.

Shell blocks have **Run code**, Python answers have **Copy code**, and prompts have **Copy text**. Save source edits first. Run code requires an idle shell; if the agent is running, enter `exit` or interrupt it before starting a new command. It does not save editor buffers or certify the command's result.

Old browser learning records are preserved on upgrade, though the active lessons no longer show evidence forms. They do not affect workshop navigation.

## App Preview

When instructed, start the supplied app once:

```bash
uv run uvicorn app:app --app-dir capstone --host 0.0.0.0 --port 8000 --reload > /tmp/capstone-preview.log 2>&1 &
```

Reload App Preview. Run `uv run python verify_capstone.py --project capstone` for
the failing baseline and again after repair. Completion should survive browser
refresh; server restart deliberately clears the in-memory task store. Create a
fresh task after code reload before checking the repaired browser flow.

## Stop, restart and upgrade

```bash
docker compose down
docker compose up -d
```

Saved files remain in `student/`. Stopping the runtime ends its shell processes
and capstone server. After configuration or image changes, use
`docker compose up --build -d`; changing `.env` requires recreating the runtime.
Never use `down --volumes` to perform a routine update.

The Compose project name remains `coding-agent-guided` for upgrades. The workbench
uses a new Debian Python environment volume; the former Alpine volume is retained.
The same student files remain in place. Restart the preview after upgrading.

## Verify and develop

```bash
uv run --project backend pytest backend/tests -q
node --test workbench/tests/*.test.cjs
cd frontend
npm ci
npm test
npm run typecheck
VUE_APP_BASE_PATH=/guide/ npm run build
```

Frontend tooling requires Node 24 or later; Docker supplies it. The Vue app now
renders instructions only at `/guide/` inside the workbench. Its existing standalone
development mode remains available through `npm run serve`; the default deployed
interface uses code-server. Open the root URL to use lessons and Code together.

## Layout

- `workbench/`: adapted upstream shell and panel behavior tests.
- `frontend/`: guided lessons, static production build and proxy.
- `backend/`: typed file API; the guide uses its workspace listing for file links.
- `docker/guided/`: VS Code, managed Python, API and ttyd/tmux runtime.
- `student/`: learner code, tests, checkpoints, cached documentation and solutions.
- `vendor/workshop-front-end-components/`: shared guided lesson components.

The earlier Docsify workbench remains optional via
`docker compose -p coding-agent-legacy -f docker-compose.legacy.yml up --build -d`
at http://localhost. Avoid editing the same student files in both interfaces.
Its historical setup is [SETUP.legacy.md](SETUP.legacy.md).
