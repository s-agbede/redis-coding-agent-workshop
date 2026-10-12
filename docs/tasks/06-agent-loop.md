# Let the agent take several steps

**15 minutes.** Your conversation now has history. It still cannot look at files on this computer. We will connect its requested actions to Python functions, then send the results back.

## Choose an observation

For our final repair, **PEAS** asks: what counts as success (**Performance**), where does the agent work (**Environment**), what can it do (**Actuators**), and what can it observe (**Sensors**)?

Take a minute to propose what the refresh bug will need. A useful first sensor is a list of project files. `list_files` is supplied; finding a name does not reveal its contents.

<details>
<summary>Compare your design</summary>

Success means completion survives a later read and refresh, while existing behavior still works. The environment is our local project. Reading files supplies observations; editing code and running commands are actions. Independent checks measure the outcome. We will add actions after the reader works.

</details>

A **tool schema** describes an available function to the model. A **tool call** is the model's request to use it. Our **registry** maps its name to real Python code. The model does not execute Python itself.

```text
model requests list_files → our Python calls list_files
            ↑                         ↓
      next model request ← matching tool result
```

## Follow one tool request

Here is an **illustrative example**, not a live request or code to paste. The model may choose different files and call IDs when you run it.

`PLAIN_READ_SCHEMA` in **tools.py** describes our reader:

```json
{
  "type": "function",
  "function": {
    "name": "read_file",
    "description": "Read the complete UTF-8 text of a known local file. Use list_files to discover paths.",
    "parameters": {
      "type": "object",
      "properties": {"path": {"type": "string"}},
      "required": ["path"]
    }
  }
}
```

The **name** identifies the function, the **description** helps the model choose it, and **parameters** describes the arguments it may request. This contract says that `path` is a required string. It does not contain the file's contents or execute any code.

After discovering a path, the model could return this call inside its assistant message:

```text
call.id                 = "call_42"
call.function.name      = "read_file"
call.function.arguments = '{"path": "checkpoints/release_log.md"}'
```

Notice the arguments are a **JSON string**. Our loop decodes that string, looks up the function and supplies its keyword arguments:

```text
tool_arguments = json.loads(call.function.arguments)
# Now: {"path": "checkpoints/release_log.md"}, a Python dictionary

registry[call.function.name](**tool_arguments)
# Equivalent to: read_file(path="checkpoints/release_log.md")
```

Our reader is still unfinished, so its error becomes this tool message:

```json
{
  "role": "tool",
  "tool_call_id": "call_42",
  "content": "Error: Implement read_file in agent.py"
}
```

Keep the assistant message **and then** append this result. Its `tool_call_id` connects the observation to the exact request. The next `ask` sends the extended history, so the model can respond to what actually happened. Once you implement the reader, file text will take the error's place.

## Advertise discovery and reading

Type `exit`, open **agent.py**, and replace the `TOOL_SCHEMAS = []` line with:

```python
TOOL_SCHEMAS = [LIST_SCHEMA, PLAIN_READ_SCHEMA]
```

The registry already contains working `list_files` and an unfinished `read_file`. These are the only available tools. Save and run:

```bash
uv run python main.py
```

Ask:

```text
What's the latest release decision?
```

The prompt gives no filename or location. The model can discover project files with `list_files`. Inspect the request preview and the pending-action message. A tool request is not a result: our one-call program has no dispatch yet. The starter returns you to the shell when it has an unexecuted tool request. If the model answers without a request, ask it to inspect the project files; do not treat an unsupported answer as evidence.

## Complete the loop

In `run_agent`, keep the request and message append, but repeat them with a step cap. Add three behaviors:

1. Stop when the assistant has no tool calls.
2. Decode each call's JSON arguments and invoke `registry[call.function.name](**tool_arguments)`.
3. Append a `role="tool"` result with the matching `tool_call_id`, then ask the model again.

The answer below supplies output panels and turns tool exceptions into matching error feedback. The model request stays outside that exception handler: a provider failure must remain a real failure. The `max_iters` cap limits the number of model requests for this turn. If the final allowed request asks for tools, their results are saved, but the loop cannot make another request to interpret them. Reaching the cap does not mean success; the terminal will let you continue with the retained history. The supplied approval helper will ask before running a shell command when we add that tool in the final lesson. Reading files needs no approval.

<details>
<summary>Copyable solution — replace the whole run_agent function</summary>

```python
def run_agent(
    client: Any, messages: list[Any], tool_schemas: list[dict[str, Any]],
    registry: dict[str, Callable[..., str]], max_iters: int = 10,
) -> list[Any]:
    for _ in range(max_iters):
        assistant_message = ask(client, messages, tool_schemas)
        messages.append(assistant_message)
        if not assistant_message.tool_calls:
            return messages
        for call in assistant_message.tool_calls:
            ui.show_tool_request(call.id, call.function.name, call.function.arguments)
            try:
                tool_arguments = json.loads(call.function.arguments)
                if call.function.name == "run_bash" and not ui.approve_command(tool_arguments["command"]):
                    result = "User declined to run this tool."
                else:
                    result = registry[call.function.name](**tool_arguments)
            except Exception as error:
                result = f"Error: {error}"
            ui.show_tool_result(call.id, result)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return messages
```

</details>

Save and restart:

```bash
uv run python main.py
```

Ask the **same question**. Now a file listing can become evidence in the next model turn. Look for a request ID and its matching result, then a later action chosen by the model. If it asks to read, you will see `Error: Implement read_file in agent.py`. The loop has worked: it executed the requested function and returned the actual error.

**Check the causal link:** match the request ID with its RESULT panel, then find the added `tool` role in the next request summary. What can the model learn from a filename? What is still missing?

<details>
<summary>Compare your answer</summary>

Discovery supplies paths, not contents. The reader error explains why the agent cannot establish the release decision yet. A good answer acknowledges that missing evidence; if it guesses, ask which actual observation supports the claim. There is no required tool-call count or scripted model response.

</details>

You have built the loop you will use for the rest of the workshop. Next, make that failed read succeed.

<details>
<summary>Catch up if needed</summary>

Save your attempt separately first. After typing `exit` to leave the chat, this copies the complete learner file **through this lesson**, including the earlier exercises:

```bash
cp solutions/steps/03-loop.py agent.py
```

Restart with `uv run python main.py`. Refresh the open editor file after copying, before saving over it. This is an explicit replacement of your work, not an automatic fallback.

</details>
