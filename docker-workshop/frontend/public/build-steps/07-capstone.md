---
title: Ask your agent to fix the app
editorFile: main.py
---

**25 minutes.** Your coding agent now has the tools and loop needed to investigate the bug we set out to repair. Here is its ticket:

> Completing a task looks successful, but refreshing the page makes it incomplete again. Find the cause, repair it and check that existing behavior still works.

## Reproduce the ticket

Type **exit** to leave the previous agent session, so Terminal is ready for shell commands. Use **Run code** for the commands below.

Open **App Preview**. If the task board already loads, reuse that server. Otherwise, start it once in the embedded Terminal:

```bash
uv run uvicorn app:app --app-dir capstone --host 0.0.0.0 --port 8000 --reload > /tmp/capstone-preview.log 2>&1 &
```

In **App Preview**, create a task, mark it complete and refresh the page. The completion should disappear. Run the independent checker:

```bash
uv run python verify_capstone.py --project capstone
```

The starter should pass **8/9** checks, with **complete persistence** failing. The checker starts its own temporary server; it does not depend on App Preview. This is a useful bug report: one action appears successful, but a later read disagrees.

Before handing over the ticket, propose a cause: **did the update fail, or did the later read lose the update?** Keep that hypothesis in mind as you watch the investigation. You can change your mind when the agent finds evidence.

## Give the task to your agent

```bash
uv run python main.py --project capstone
```

Use **Copy text** to paste this prompt into the running agent:

```text
A task looks complete until the browser refreshes, then it becomes incomplete. Investigate and repair the app. Keep the existing API and page working. Do not change the verifier or workshop tests. Run python ../verify_capstone.py --project . before and after the repair. Finish with Changed files, Commands run, Results, and Unverified.
```

The harness loads the project's instructions and runs tools inside `capstone/`. Watch it read the code, make a change and request checks. Review each command before approving it. If checks fail, give the failure back to the agent and ask it to continue investigating.

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

Inspect `tail -n 30 /tmp/capstone-preview.log`. If port 8000 is already in use, reuse the existing preview server. If the checker cannot start, run `uv run python check_setup.py` and show the reported error to your instructor.

</details>

**Quick question:** why did we run the supplied evaluation checks after the agent ran checks?

<details>
<summary>Compare your answer</summary>

An agent's report can be incomplete or mistaken. Independent checks measure the app's actual behavior and guard against regressions. This is PEAS's Performance category made concrete: the requested outcome and preserved behavior, measured outside the model's claim.

</details>

Your request, history, tool execution and feedback loop enabled this repair; the independent checks establish what worked. If a check still fails, that result gives you a concrete next question for your agent.

Further reading: [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
