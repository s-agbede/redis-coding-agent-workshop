# Facilitator guide

Guide the group from one FizzBuzz request to their own working coding agent. Use the [90-minute schedule](WORKSHOP.md), including ten minutes of buffer. The audience is experienced Python developers learning the boundaries of an LLM application.

## Prepare before the session

From the repository root, preserve any existing `.env`, configure the model service and run `bash start.sh`. Open http://localhost:8080. Each learner needs an independent stack. The runtime prepares a learner workspace from the root source and preserves browser edits in `.workshop/`. App Preview starts automatically.

The root `docker-compose.yml` is the single deployment configuration. `start.sh` uses root `.env` when present and falls back to an existing `docker-workshop/.env` for older installations. Reuse `bash start.sh` for updates to preserve that configuration selection.

Run `uv run python check_setup.py` in the embedded Terminal. It checks dependencies and configuration presence without contacting the provider or printing credentials. Validate an actual model request separately using completed code in a disposable workspace. After configuration changes, run `bash start.sh --force-recreate` from the repository root; this restarts the workshop, so save learner work first.

## Opening demo

Run this in the workshop terminal:

```bash
uv run python demo.py
```

This starts the completed agent and waits for you to type a task. Try:

```text
Completing a task looks successful, but refreshing makes it incomplete again. Find and fix the bug.
```

The demo uses a fresh copy of the broken app. App Preview switches to that copy, so you can show the same bug and repair the agent is working on. Shell commands use the normal approval prompts. The demo keeps its files under `output/` for later inspection.

Type `exit` when finished; App Preview returns to the unchanged learner app. Start `uv run python main.py` to build the learner agent with the group. No files need swapping or resetting.

## Teach one evolving agent

Use the six-lesson schedule in WORKSHOP.md. Give a two-minute welcome naming the concrete repair destination. All core learner changes go in **agent.py**; `main.py` is supplied terminal/client wiring. Start the same program with `uv run python main.py` after each save.

1. **Model request, 9m:** explain LLM, OpenAI GPT model, API and SDK before coding. Run the starter and ask FizzBuzz; its explicit missing-request message motivates `ask`. Implement the function, rerun and inspect the response. A code block is text, not executed code.
2. **History, 9m:** ask “Now change it to stop at 20.” Inspect the request's count/roles before trusting any lucky answer. Remove the reset from `remember`, restart and repeat both prompts. The second request now includes the earlier user and assistant. Restarting clears history.
3. **Tools and loop, 15m:** integrate a one-minute PEAS design discussion. Advertise supplied `list_files` and unfinished `read_file` by editing `TOOL_SCHEMAS`. Ask “What's the latest release decision?” and observe an unexecuted tool request. Complete stopping, dispatch and matching feedback in `run_agent`. Rerun the same question: discovery succeeds; the actual reader error reaches another model turn. Inspect call/result IDs and discuss unsupported guesses. The learner's own loop powers all later lessons.
4. **Reader, 10m:** implement UTF-8 reading in the same file, rerun the question and locate supporting evidence. Filenames do not establish contents; the release condition does not establish tests passed. If the model only reads the short brief, ask for support from the log itself.
5. **Paging, 10m:** propose a bounded observation before revealing ours. Add offset/limit and the supplied helper call, then explicitly replace the plain schema with the paging schema. Rerun the same program/question. The model chooses pages. Compare per-result limits and evidence; do not promise fewer total tokens or a fixed tool sequence.
6. **Repair/evaluation, 25m:** reproduce the refresh bug and propose a cause. Register supplied actions in agent.py and select `--project capstone`. This changes the workspace, not the implementation. Inspect approvals, errors and actual command results. After the attempt, explain the code change, run the unchanged checker and test a fresh browser task. Connect the observed outcome to PEAS Performance.

Aim to begin repair at minute 55; keep ten minutes of buffer. Protect the first working loop run and independent final checks. Shorten optional discussion rather than turning the final task into a rushed demo. Ask learners to choose a follow-up and explain what evidence supports it.

## Present the data flow in code order

Keep one path visible when introducing the harness: **`main()` → `messages` → `ask()` → tool schema → dispatch → feedback → next request**. Start with the imported learner functions in `main.py`, show the history list, then follow the direct SDK call in `agent.py`. Explain once why our user/tool messages are dictionaries while the SDK's assistant reply uses attributes.

Before revealing the loop, walk through the illustrative `read_file` call on the lesson page. Point to the schema's name and required path, the JSON arguments string, its decoded dictionary, the registry lookup, and the matching result ID. The unfinished reader's error is a real observation the next request can use. The live question stays natural; do not supply the example filename as part of the task prompt.

For paging, trace the small seven-line example before opening the helper. Show `offset - 1`, the selected indexes, and `offset + len(page)`. Ask which line comes next if the character budget allows fewer lines than requested. These short walkthroughs replace explanation during debugging; they are not extra exercises added to the schedule.

## Running, inspection and catch-up

Run code submits a shell command; it does not save the editor or establish success. Save first, type `exit` to leave the chat, then run again. Ctrl+C interrupts when appropriate. The default request display shows message count and roles alongside separate tool/answer panels. If needed, `AGENT_TRACE_MESSAGES=1` expands request content previews without changing the payload.

The model service is real in every guided exercise. Do not substitute prepared output for an outage. Prepared replies belong only inside evaluator tests. Check configuration privately without displaying credentials.

Inline answers replace one function or the named assignments. For catch-up, preserve the learner's attempt and copy the matching cumulative `solutions/steps/01-model.py` through `06-repair.py` to `agent.py`. Every snapshot includes preceding lessons and leaves later work unfinished. `solutions/agent.py` is the full reference. Neither is loaded automatically. Refresh an open editor buffer after an external copy before saving over it.

The active final tests import learner functions from agent.py. Run the published-snippet replay from the repository root with `uv run pytest tests/test_learning_progression.py -q`; it uses disposable workspaces created from the canonical starter, never replaces learner source, and substitutes only provider transport. Practise the live demo separately with `uv run python demo.py`. The `checkpoints/` directory now contains only the fictional release evidence used by the lessons.

If an outage blocks the final repair, a manual repair and independent check can demonstrate app behavior, but do not claim it was a live agent trial. The supplied `solutions/capstone_app.py` is a final catch-up option after preserving the attempt.

## Troubleshooting

- **An exercise raises NotImplementedError:** confirm the named function was changed and saved. Stop and rerun the Python process to load the edit.
- **History seems stale:** restarting creates a fresh list. Repeat both prompts when comparing conversation behavior.
- **Authentication or model errors:** check host `.env` and service configuration privately. Recreate runtime after changes; do not display credentials.
- **A tool repeats or its result disappears:** inspect the assistant request, matching `tool_call_id` and the next request's messages.
- **A command is denied:** that denial is feedback. It does not mean the command executed or passed.
- **Preview is blank or reports 502:** reload the panel, then inspect `docker compose logs --tail=100 runtime` on the host. The runtime starts and manages the preview; learners do not need to launch another server.
- **Tasks disappear during editing:** Uvicorn reload restarted the process and cleared its in-memory store. After repair, create a fresh task, complete it and refresh without editing again.
- **The agent claims success but checks fail:** use the failed behavior as the next prompt. Keep the independent checker unchanged.

The execution tool and working-directory choice are teaching conveniences, not a production security boundary. Discuss that limit when explaining the supplied approval helper, without turning it into a separate setup lesson.

## Pilot the pacing and learner decisions

Before treating the schedule as validated, rehearse with an experienced Python developer who is new to LLM applications. Observe whether they can name the destination early, identify the missing history from the request preview, justify the bounded reader's result, choose a follow-up and explain the accepted repair. Note elapsed times and moments of lost momentum or instructor rescue. Collect this as facilitator feedback, without adding forms to the learner workflow.

A successful technical run establishes that the exercises work. It does not establish the learner's understanding or motivation, and one live repair does not establish agent reliability.
