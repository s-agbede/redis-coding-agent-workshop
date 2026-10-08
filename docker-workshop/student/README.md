# Build a Coding Agent From First Principles

An instructor-guided Python workshop for experienced developers new to LLM applications. Start with a FizzBuzz model call, build a small agent harness, then ask your agent to repair a supplied FastAPI task board.

## Learning path

| Lesson | What you build or try |
| --- | --- |
| 1. First model call | Send a request through the Python SDK and inspect the returned text. |
| 2. PEAS | Choose performance measures, environment, actuators and sensors. |
| 3. Conversation | Preserve the context needed for a follow-up question. |
| 4. One tool | Implement a plain file reader and follow a structured request/result exchange. |
| 5. Better tools | Improve the reader with ranges, line numbers and continuation information. |
| 6. Agent loop | Add stopping, dispatch and feedback to the repeated model/tool exchange. |
| 7. Repair and evaluation | Ask your agent to fix the task board, then check the result independently. |

Use the hints and copyable answers on each lesson page when useful. Short questions and revealable answers support the instructor's discussion. The [workshop schedule](WORKSHOP.md) allocates 80 minutes to activities and ten minutes of buffer; validate timing in rehearsal.

Learner functions are in `first_call.py`, `checkpoints/stage1_chat.py`, `tools.py` and `agent.py`. Schemas, other tools, error handling, approval prompts, output formatting, deterministic test helpers and independent application checks are supplied. Completed examples live in `solutions/`. The application has an intentional bug that remains in the starter.

## Browser workspace

Code and Terminal share this learner workspace at `/workspace`. Save with Ctrl/Cmd+S before running commands, and follow **Welcome → Workshop**. Ask your instructor for environment setup help; the repository's `docker-workshop/README.md` describes deployment.

## Local commands

For local use, preserve an existing `.env`; otherwise copy `.env.example` and configure the model service. Then run:

```bash
uv sync
uv run python check_setup.py
```

Follow the [seven lessons](docs/home.md) in order. Save each edit before running its live exercise. In the guided browser, select Run code to run shell commands in Terminal; Python answers and prompts have copy actions. Unit checks are grouped in the final evaluation. The complete test suite intentionally fails while later exercise functions are still blank. Restart interactive programs to load changes; their in-memory chat history starts fresh.

`check_setup.py` checks dependencies and configuration presence without contacting the provider or printing the key. The guided exercises use the live configured model service. The first-call command reads its FizzBuzz prompt from source, and the default one-tool checkpoint asks for the release name from the supplied fictional brief. Prepared model replies are used internally by deterministic tests.

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

`main.py` is interactive: type `exit` before running the remaining shell commands. `--project` loads the project's `AGENTS.md` and changes the working directory; it is not a security sandbox. The app's completion state initially fails to survive a later read. The independent checker must remain unchanged while the agent repairs that behavior.

## Configuration

| Variable | Default | Effect |
| --- | --- | --- |
| `AGENT_API_KEY` | — | Model service key. |
| `AGENT_BASE_URL` | OpenAI | Optional compatible service endpoint. |
| `AGENT_MODEL` | `gpt-5` | Model ID. |
| `AGENT_MAX_ITERS` | `25` | Interactive loop cap per task. |
| `AGENT_REQUEST_TIMEOUT` | `90` | Request timeout in seconds. |
| `AGENT_AUTO_APPROVE` | off | `1` auto-approves gated tools. |
| `AGENT_VERBOSE` | off | `1` prints tool arguments and results. |

## Facilitation and rehearsal

Read [WORKSHOP.md](WORKSHOP.md) and [FACILITATOR.md](FACILITATOR.md). To rehearse with completed code and a fresh temporary copy of the broken app:

```bash
uv run python rehearse.py -n 1
```

This makes live model calls and saves the trace, checks and changes under `output/rehearsal/`. Deterministic tool and harness tests establish Python behavior; the live repair trial and independent app checks provide different evidence. Several trials are needed to assess variation.

Historical research and earlier designs remain in `docs/research/` and `docs/superpowers/` in the root repository. Use the current lesson manifest and workshop schedule for teaching. Durable memory, advanced context management and multiple agents are follow-on topics.
