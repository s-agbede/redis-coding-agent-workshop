# Capture with Redis Agent Memory

**10-minute demo, 5 minutes for you.** Instead of asking people to write preferences down, record the work and let the memory service learn from it.

## What Redis Agent Memory does

Redis Agent Memory keeps two kinds of memory for an agent:

- **Session events (short-term memory):** what was said, by whom, in which session. Your application adds these as the conversation happens.
- **Long-term memories:** durable, typed records such as a `user_preference`. Redis Agent Memory **extracts** these from session events in the background. Your application does not write them.

Later, the application **searches** long-term memory, scoped to a person, and puts relevant results back into the request. This section covers capture; the next covers recall.

[Diagram placeholder: session events stored with owner and session IDs → background extraction → long-term user_preference memory.]

## Demo: record each exchange

The supplied runtime calls `record_event` twice per turn: once with your original message and once with the agent's final answer. Tool calls are not recorded.

```python
def record_event(
    memory: AgentMemory, session_id: str, actor_id: str,
    role: models.MessageRole, text: str,
) -> None:
    memory.add_session_event(
        session_id=session_id,
        actor_id=actor_id,
        role=role,
        content=[models.Text(text=text)],
        created_at=datetime.now(timezone.utc),
    )
```

Each event keeps **who said what in which session**: the role (`USER` or `ASSISTANT`), the speaker (`actor_id`: your owner ID, or `coding-assistant`) and the session. Roles matter: extraction should learn *your* preferences, not suggestions the model made.

With `CAPTURE_ENABLED = True` and a restart, the instructor restates the preference and the `valid_report_filename` task from the previous section. Earlier messages were never recorded, so they must be said again.

**Predict:** is a stored session event already a long-term preference?

- `/events` shows the two original messages with their roles and session ID.
- `/memories` may still be empty. Extraction runs in the background; we come back to it after the next demo.
- `/view-context` shows `retrieved_preferences: []`. Storing a memory does not put it in the request.

## Your turn (5 minutes)

Type `exit`, then from the repository root:

```bash
cp solutions/steps/01-capture.py agent.py
uv run --group iris python main.py
```

Refresh the editor and find `record_event` in `agent.py`. Then at `You >`:

1. `/status`: **look for** capture enabled, recall and Playbook disabled.
2. Paste the commenting preference, then the `valid_report_filename` task (both from the [previous section](02-forgetting.md)).
3. `/events`: **look for** your preference as a `USER` event and the agent's answer as an `ASSISTANT` event, with the same session ID.

Leave `/memories` for the next section; extraction needs a few minutes.

Next: [recall in a fresh session](04-recall.md).
