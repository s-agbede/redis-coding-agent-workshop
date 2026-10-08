# Commands and concepts

In the guided workshop, save edits in Code, then select **Run code** on a shell block. Read its output in Terminal. Use **Copy code** for Python answers and **Copy text** for prompts to paste into a running chat.

Run code needs an idle shell. Type `exit` to leave a chat, or press Ctrl+C to interrupt, then run the next command. Restarting Python loads saved code and clears its in-memory conversation.

| Activity | Command |
| --- | --- |
| Environment check | `uv run python check_setup.py` |
| First model call | `uv run python first_call.py` |
| Conversation | `uv run python -m checkpoints.stage1_chat` |
| One file-tool exchange | `uv run python -m checkpoints.stage2_one_tool` |
| Agent on the task board | `uv run python main.py --project capstone` |
| Independent app checks | `uv run python verify_capstone.py --project capstone` |

The first model call uses the FizzBuzz prompt in its source. The file-tool checkpoint asks for the release name in the supplied brief. Its `--prompt` option changes the question; `--paged` advertises the improved reader. Tool arguments are chosen by the live model.

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
