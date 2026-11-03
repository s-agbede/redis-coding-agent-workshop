---
title: Capture with Redis Agent Memory
editorFile: agent.py
---
**10-minute demo, 5 minutes for you.** Record the conversation, and let Redis Agent Memory keep it and learn from it.

## What Redis Agent Memory does

- **Session memory (short-term):** every message, who sent it, and which session it belongs to. Your application adds these as you talk.
- **Long-term memory:** short facts such as "Prefers Google-style docstrings". A store can define its own memory types, with a prompt saying what to extract; ours has `coding_preference`. Redis Agent Memory **extracts** these from your sessions in the background; your application never writes them.

This section is about capturing sessions. The next is about using what was learned.

## Demo: record each message

The runtime calls `record_event` twice per turn: with your message, and with the agent's final answer.

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

The role (`USER` or `ASSISTANT`) matters: Redis Agent Memory should learn *your* preferences, not the model's suggestions.

With capture switched on, the instructor mentions the docstring preference again and asks for the slug function. Then:

- `/events` shows both messages and both answers, stored for this session.
- `/new-session`, then `/sessions`: the earlier session is listed. `/resume <id>` brings the whole conversation back, preference included, because Redis Agent Memory kept it.

Resuming replays everything, though. You don't want every old conversation in every request; you want the bits that matter. Run `/memories`: it may still be empty, because extraction runs in the background. We come back to it in the next section.

## Your turn (5 minutes)

Type `exit`, then:

```bash
cp solutions/steps/01-capture.py agent.py
uv run --group iris python main.py
```

Open `agent.py` and find `record_event`. Then:

1. Mention your docstring preference and ask for the slug function.
2. `/events`. **Look for:** your messages and the agent's answers.
3. `/new-session`, `/sessions`, then `/resume` with your earlier session's ID. **Look for:** the conversation is back.
4. Open the **Agent Memory** panel (panel menu, top left) and choose **Sessions**: the same conversation, straight from Redis Agent Memory.

Next: [recall in a fresh session](/build?lesson=04-recall.md).
