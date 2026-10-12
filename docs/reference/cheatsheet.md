# Commands and concepts

In the guided workshop, save edits in Code, then select **Run code** on a shell block. Read its output in Terminal. Use **Copy code** for Python answers and **Copy text** for prompts to paste into a running chat.

Run code needs an idle shell. Type `exit` to leave a chat, or press Ctrl+C to interrupt, then run the next command. Restarting Python loads saved code and clears its in-memory conversation.

| Activity | Command |
| --- | --- |
| Environment check | `uv run python check_setup.py` |
| Start your evolving agent | `uv run python main.py` |
| Select the task-board project | `uv run python main.py --project capstone` |
| Independent app checks | `uv run python verify_capstone.py --project capstone` |

Type your question into the running agent. It is not a shell command or a command-line flag. From the loop lesson onward, ask “What's the latest release decision?” The project context names the evidence directory; the model discovers files and chooses its reads. Update `TOOL_SCHEMAS` explicitly when adding the loop, paging and repair actions; there is no hidden stage detection.

The default request display shows message count and roles. `AGENT_TRACE_MESSAGES=1` enables full content previews when an instructor needs to inspect more detail; it does not change requests. Tool requests and results have their own panels.

All core code edits go in **agent.py**. `main.py` supplies the session and SDK setup, `tools.py` supplies schemas/helpers/actions, and `ui.py` supplies display and approvals. Cumulative catch-up files in `solutions/steps/` deliberately replace `agent.py` through the selected lesson; preserve your own attempt before copying one.

## Message roles

- `system`: instructions supplied by the harness.
- `user`: the human's request.
- `assistant`: the model's answer or tool requests.
- `tool`: an operation's result, paired with a `tool_call_id`.

Keep an assistant tool-request message before its results. Return one result for each call ID, including errors and denials. JSON arguments need decoding before dispatch to a Python function. Printing text is display; appending it to a later request provides context.

## Final evaluation

After completing the exercises, check tools and the request/history/loop behavior:

```bash
uv run pytest tests/test_read_file.py tests/test_tools.py -q
uv run pytest tests/test_first_call.py tests/test_conversation.py tests/test_agent.py -q
```

Pytest dots and a passing summary mean the selected tests passed. Tool tests exercise functions; harness tests use prepared replies internally to check repeatable cases. Neither substitutes for the live repair attempt or the independent application check.

See [Agent components](mental-model.md) and [Ask your agent to fix the app](../tasks/07-capstone.md).
