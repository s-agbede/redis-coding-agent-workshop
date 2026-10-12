# Keep the conversation

**9 minutes.** Your program answers one question. Let's see what happens when your next question depends on its answer.

## Observe the missing context

In the chat from the previous lesson, ask:

```text
Now change it to stop at 20.
```

Inspect the next **REQUEST PREVIEW**, not just the answer. You should see the system instruction and your latest question; the earlier FizzBuzz question and code are absent. Even a lucky model guess cannot change what we sent.

An API call does not automatically remember earlier calls. The conversation lives in our Python list, and our program decides what to include in each request.

## Make one small change

Type `exit` so Terminal returns to the shell. In **agent.py**, find `remember`. It currently clears earlier messages before appending your next question. Replace it so it **only appends** the new user message. `run_agent` already appends each assistant response.

<details>
<summary>Copyable solution — replace the whole remember function</summary>

```python
def remember(messages: list[Any], user: str) -> None:
    messages.append({"role": "user", "content": user})
```

</details>

Save and restart the same program:

```bash
uv run python main.py
```

Repeat both prompts: the FizzBuzz request first, then “Now change it to stop at 20.” The second preview should now include **system → user → assistant → user**. The earlier generated code is available to the model, so the follow-up has a clear referent.

Ask a follow-up of your own. Explain which previous message gives it meaning. Restarting this process creates a fresh list; this is session history, not durable memory or model training.

<details>
<summary>Compare your explanation</summary>

Keeping a Python list is only half the mechanism. `ask` sends that list again on every request. The model receives the previous answer as text in the next input, rather than remembering an earlier API connection.

</details>

Next, ask “What's the latest release decision?” It may say it lacks project information, or it may guess. Either way, has our program actually read a project file yet?

<details>
<summary>Catch up if needed</summary>

Save your attempt separately first. After typing `exit` to leave the chat, this copies the complete learner file **through this lesson**, including the earlier exercises:

```bash
cp solutions/steps/02-history.py agent.py
```

Restart with `uv run python main.py`. Refresh the open editor file after copying, before saving over it. This is an explicit replacement of your work, not an automatic fallback.

</details>
