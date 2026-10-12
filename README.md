# Build a Coding Agent From First Principles

An instructor-guided Python workshop for experienced developers new to LLM applications. Start with a FizzBuzz model call, build a small agent harness, then ask your agent to repair a supplied FastAPI task board.

## Learning path

| Lesson | What you build or try |
| --- | --- |
| 1. First model call | Send a request through the Python SDK and inspect the returned text. |
| 2. Conversation | Preserve context so follow-ups refer to earlier answers. |
| 3. Tool loop | Execute supplied discovery, return results and errors, request another step. |
| 4. Reader | Turn a failed read into evidence by implementing read_file. |
| 5. Paging | Bound reader output and expose continuation arguments explicitly. |
| 6. Repair and evaluation | Register supplied actions, repair the task board and check it independently. |

Use the hints and copyable answers on each lesson page when useful. Short questions and revealable answers support the instructor's discussion. The [workshop schedule](WORKSHOP.md) allocates 80 minutes to activities and ten minutes of buffer; validate timing in rehearsal.

All learner functions are in **agent.py**: `ask`, `remember`, `run_agent` and `read_file`. Each lesson changes the same running program. PEAS is a short discussion alongside tool design. Schemas, other tools, error handling, approval prompts, output formatting, deterministic test helpers and independent application checks are supplied. Completed examples live in `solutions/`. The application has an intentional bug that remains in the starter.

## Start the browser workshop

The [Redis workshop workbench](https://github.com/redis-developer/semantic-cache-routing-workshop) combines guided Instructions, VS Code, a shared Terminal and App Preview. The navigation is **Welcome → Workshop**.

From the repository root, preserve an existing `.env`; otherwise copy `.env.example` to `.env`. Configure `AGENT_API_KEY` and the model service, then run:

```bash
bash start.sh
```

Open **http://localhost:8080**. The browser workspace is prepared from the root Python source on first start; your edits are saved in `.workshop/`. App Preview starts automatically. See [browser setup](docker-workshop/README.md) and [upstream provenance](docker-workshop/UPSTREAM.md).

## Repository layout

- `docker-compose.yml`, `start.sh`, `build.sh`: the single workshop deployment and its entry points. The hosted lab can also invoke `bash build.sh` to build and start the workshop. Use `docker compose build` to build images only.
- `docker-workshop/`: browser platform — frontend, workbench, runtime backend, Docker image files and attributed shared components.
- `.workshop/`: generated learner workspace mounted into the browser at `/workspace`; ignored by Git. Existing learner edits survive restarts.
- Root Python files, `checkpoints/`, `capstone/`, `solutions/`, `tests/`: the maintained workshop source. Runtime startup refreshes supplied helpers from this source and initializes missing learner files without replacing edits to `agent.py` or `capstone/`.
- `docs/tasks/`: canonical lesson text. Run `uv run python scripts/publish_docs.py` after editing; `--check` reports unpublished changes. The publisher updates only documentation and assets, preserving learner Python and app edits. Historical plans, research and retired requirements are preserved in `archive/`.

To stop the workshop, run `docker compose down` from the repository root. Do not add `--volumes` unless you intend to delete saved environment/editor data.

The default listens on all interfaces on port 8080 for the hosted lab; keep it behind the lab's authentication gateway. For local-only access, set `WORKSHOP_BIND_ADDRESS=127.0.0.1` in the root `.env`.

## Local commands

For the instructor's opening demo, run `uv run python demo.py` with the model service configured. It starts the completed agent interactively against a separate copy of the task board. In the browser workshop, App Preview switches to that demo copy. Type your repair request, then `exit` to return the preview to the learner app. Learner code and the original app stay unchanged. See the [facilitator guide](FACILITATOR.md) for the suggested prompt.

For local use, preserve an existing `.env`; otherwise copy `.env.example` and configure the model service. Then run:

```bash
uv sync
uv run python check_setup.py
```

Follow the [six lessons](docs/home.md) in order. Save each edit before running its live exercise. In the guided browser, select Run code to run shell commands in Terminal; Python answers and prompts have copy actions. Unit checks are grouped in the final evaluation. The complete test suite intentionally fails while later exercise functions are still blank. Restart interactive programs to load changes; their in-memory chat history starts fresh.

`check_setup.py` checks dependencies and configuration presence without contacting the provider or printing the key. The guided exercises use the live configured model service. Start `uv run python main.py` and type the question into its prompt. The natural release question stays the same as discovery, reading and paging improve. Prepared model replies are used internally by deterministic tests.

After completing the harness, the final lesson uses:

```bash
uv run python main.py --project capstone
```

After exiting the agent, run the supplied evaluation checks:

```bash
uv run pytest tests/test_read_file.py tests/test_tools.py -q
uv run pytest tests/test_first_call.py tests/test_conversation.py tests/test_agent.py -q
uv run python verify_capstone.py --project capstone
```

The terminal session is interactive: type `exit` before running the remaining shell commands. `--project` loads the project's `AGENTS.md` and changes the working directory; it is not a security sandbox. The app's completion state initially fails to survive a later read. The independent checker must remain unchanged while the agent repairs that behavior.

## Configuration

| Variable | Default | Effect |
| --- | --- | --- |
| `AGENT_API_KEY` | — | Model service key. |
| `AGENT_BASE_URL` | OpenAI | Optional compatible service endpoint. |
| `AGENT_MODEL` | `gpt-5` | Model ID. |
| `AGENT_MAX_ITERS` | `25` | Interactive loop cap per task. |
| `AGENT_REQUEST_TIMEOUT` | `90` | Request timeout in seconds. |
| `AGENT_AUTO_APPROVE` | off | `1` auto-approves shell commands; for explicit instructor use. |
| `AGENT_TRACE_MESSAGES` | off | `1` expands the default count/role request summary with message content. |

## Facilitation

Read [WORKSHOP.md](WORKSHOP.md) for the schedule and [FACILITATOR.md](FACILITATOR.md) for teaching notes. Use `uv run python demo.py` to practise with the completed agent.

Historical research and earlier designs remain in `archive/`. Use the current lesson manifest and workshop schedule for teaching. Durable memory, advanced context management and multiple agents are follow-on topics.
