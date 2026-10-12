# Ask your agent to fix the app

**25 minutes.** Your coding agent now has the tools and loop needed to investigate the bug we set out to repair. Here is its ticket:

> Completing a task looks successful, but refreshing makes it incomplete again. Find and fix the bug.

## Reproduce the ticket

Type **exit** to leave the previous agent session, so Terminal is ready for shell commands. Use **Run code** for the commands below.

Open **App Preview**. The workshop starts the task board for you.

In **App Preview**, create a task, mark it complete and refresh the page. The completion should disappear. Run the independent checker:

```bash
uv run python verify_capstone.py --project capstone
```

The starter should pass **8/9** checks, with **complete persistence** failing. The checker starts its own temporary server; it does not depend on App Preview. This is a useful bug report: one action appears successful, but a later read disagrees.

Before handing over the ticket, propose a cause: **did the update fail, or did the later read lose the update?** Keep that hypothesis in mind as you watch the investigation. You can change your mind when the agent finds evidence.

## Give your agent actions

So far, your registry could only discover and read files. In **agent.py**, replace the `TOOL_SCHEMAS` and `REGISTRY` assignments with:

```python
TOOL_SCHEMAS = [LIST_SCHEMA, PAGED_READ_SCHEMA, WRITE_FILE_SCHEMA, STR_REPLACE_SCHEMA, RUN_BASH_SCHEMA]
REGISTRY = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "str_replace": str_replace,
    "run_bash": run_bash,
}
```

Save the file. This registers supplied editing and command tools. Your request, history, reader and loop still drive the program. The terminal asks permission before `run_bash`; editing tools operate directly in the selected project. Only use this workshop's disposable project. A declined command is feedback, not a successful check.

The next command still starts **main.py**, which imports your functions from **agent.py**. `--project capstone` selects the working directory and its `AGENTS.md` instructions; it does not select another lesson or implementation.

## Give the task to your agent

```bash
uv run python main.py --project capstone
```

Use **Copy text** to paste this prompt into the running agent:

```text
Completing a task looks successful, but refreshing makes it incomplete again. Find and fix the bug.
```

The harness loads `capstone/AGENTS.md`, which tells the agent how to check its work and preserve existing behavior. Tools run inside `capstone/`. Watch it read the code, make a change and request checks. Review each command before approving it. If checks fail, give the failure back to the agent and ask it to continue investigating.

When it finishes, type **exit** to return to the shell. Agent tool edits are already saved to disk. Compare them in Code before saving over any unsaved editor buffer.

## Decide whether the repair explains the behavior

Before accepting the result, inspect the changed handler in **capstone/app.py**. **Which change explains why completion now survives refresh?** Trace what the update stores and what the later read returns. Explain the connection to your neighbour, then use the repair answer below if you want to compare.

If you changed the harness during the attempt, restart it after saving and provide the ticket again.

<details>
<summary>If the agent gets stuck — hints for the investigation</summary>

Follow the completed value through `PATCH /tasks/{task_id}` and the later `GET`. Does the update handler return the same object that the application stores? Pydantic's `model_copy(update=...)` creates a new object.

The smallest repair should update the state used by later reads. Ask your agent to inspect this relationship, then rerun the unchanged checker. A missing service connection can be handled by making the repair manually with your instructor; that checks the app but does not demonstrate a live agent completing the task.

</details>

<details>
<summary>Repair answer — open after trying the ticket</summary>

The updated task must be assigned back into the `tasks` dictionary before returning it. Returning a new object in the HTTP response does not update the stored object. The completed implementation is available in **solutions/capstone_app.py** for comparison with your attempt.

</details>

## Evaluate the result independently

The live run tells us what this agent did on one ticket. The supplied checks let us examine its parts and the application outcome separately. After the agent exits, use **Run code** for each group below.

**Tools:** exercise file reading, range selection, editing and command results on controlled inputs.

```bash
uv run pytest tests/test_read_file.py tests/test_tools.py -q
```

**Harness:** check your first request, retained history, stopping, dispatch and feedback. These tests use prepared model replies so the same cases can be checked reliably; they do not measure a live model's choices.

```bash
uv run pytest tests/test_first_call.py tests/test_conversation.py tests/test_agent.py -q
```

**Application:** run the unchanged checker against the actual app. It checks the repair and existing behaviors, including reopening and deleting tasks.

```bash
uv run python verify_capstone.py --project capstone
```

If an assertion fails, inspect the named behavior and its expected and actual values. A passing tool or harness test does not establish that the app is repaired; that is the application check's job.

You are using an evaluator, not building a new framework. Repeated live trials would be needed to assess how reliably the model and agent complete the ticket across runs.

The application checker should now show **9/9 acceptance checks passed**. Read any failure before accepting the agent's claim. Keep these checks unchanged.

Finally, reload App Preview, create a **fresh** task, complete it and refresh. Completion should remain. Mark it incomplete and refresh again to check the reverse action. Editing the app can restart Uvicorn and clear its in-memory tasks; a fresh task separates a code reload from a browser refresh. Persistence across server restarts is outside this ticket.

<details>
<summary>If preview or checking does not start</summary>

Reload App Preview. If it still does not load, ask your instructor to check the runtime. If the checker cannot start, run `uv run python check_setup.py` and show the reported error to your instructor.

</details>

**Quick question:** why did we run the supplied evaluation checks after the agent ran checks?

<details>
<summary>Compare your answer</summary>

An agent's report can be incomplete or mistaken. Independent checks measure the app's actual behavior and guard against regressions. This is PEAS's Performance category made concrete: the requested outcome and preserved behavior, measured outside the model's claim.

</details>

Your request, history, tool execution and feedback loop enabled this repair; the independent checks establish what worked. If a check still fails, that result gives you a concrete next question for your agent.

Further reading: [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).

<details>
<summary>Catch up if needed</summary>

Save your attempt separately first. After typing `exit` to leave the chat, this copies the complete learner file **through this lesson**, including the earlier exercises:

```bash
cp solutions/steps/06-repair.py agent.py
```

Restart with `uv run python main.py --project capstone`. Refresh the open editor file after copying, before saving over it. This is an explicit replacement of your work, not an automatic fallback.

</details>
