---
title: Capture with Redis Agent Memory
editorFile: agent.py
slides: /slides/03-capture.md
---
**10-minute demo, 5 minutes for you.** Instead of writing preferences down by hand, record the conversation and let Redis Agent Memory decide what's worth keeping.

## The three jobs

| Doing it by hand | What Redis Agent Memory does | Where |
| --- | --- | --- |
| You decide what's worth writing down | **Extraction:** learns what's worth keeping from the conversation | This section |
| Nothing expires; you edit the file | **Lifecycle:** retention, and correcting or forgetting what it learned | This section and the next |
| Everything goes in every request | **Retrieval:** brings back only what fits the task | The next section |

Redis Agent Memory keeps two kinds of memory:

- **Session memory (short-term):** every message, who sent it, and which session it belongs to. Your application adds these as you talk.
- **Long-term memory:** short facts such as "Prefers Google-style docstrings". Redis Agent Memory **extracts** these from your sessions in the background; your application never writes them.

## Demo: how the memory is set up

Before using it, look at what it's set up to keep. Open the **Agent Memory** panel (panel menu, top left) and choose **Store settings**:

- **Lifecycle:** sessions are kept for a day, long-term memories for a week. Nobody has to remember to clean up.
- **Extraction cadence:** it runs about every minute while a session is active.
- **`coding_preference`:** a memory type the workshop defined, with a prompt that tells extraction to keep only what *you* say about how you want code written, and to ignore what the assistant did. This is the "deciding what's worth keeping" job, written once for everyone instead of by each person.

These are store settings, not code: whoever runs the store decides what it learns and how long it keeps it.

## Demo: switch on capture

In `agent.py:88`, set `CAPTURE = True`. That turns on two places in `handle`. First, before the model is called, `agent.py:103` records your message:

```python
if CAPTURE:
    services.memory.add_session_event(
        session_id=session.session_id, actor_id=session.owner, role=models.MessageRole.USER,
        content=[models.Text(text=task)], created_at=datetime.now(timezone.utc),
    )
```

Then, after the agent answers, `agent.py:147` records the answer the same way, with the `ASSISTANT` role. The role matters: the memory should learn *your* preferences, not the model's suggestions.

Save, type `exit`, start the agent again, then mention the docstring preference and ask for the slug function:

- `/events` shows both messages and both answers, stored for this session.
- `/new-session`, then `/sessions`: the earlier session is listed. `/resume <id>` brings the whole conversation back, because Redis Agent Memory kept it.

Resuming replays everything, though, which is the "everything in every request" problem again. You want just the bits that matter. Run `/memories`: it may still be empty, because extraction runs in the background. We come back to it in the next section.

## Your turn (5 minutes)

1. In `agent.py:88`, set `CAPTURE = True`. Save, type `exit`, and start again with `uv run --group iris python main.py`.
2. Mention your docstring preference and ask for the slug function.
3. `/events`. **Look for:** your messages and the agent's answers.
4. `/new-session`, `/sessions`, then `/resume` with your earlier session's ID. **Look for:** the conversation is back.
5. In the **Agent Memory** panel, choose **Sessions**: the same conversation, straight from Redis Agent Memory.

Next: [recall in a fresh session](/build?lesson=04-recall.md).
