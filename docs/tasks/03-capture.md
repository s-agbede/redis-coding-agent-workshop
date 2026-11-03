# Capture with Redis Agent Memory

**10-minute demo, 5 minutes for you.** Instead of writing preferences down by hand, record the conversation and let Redis Agent Memory decide what's worth keeping.

## The three jobs

| Doing it by hand | What Redis Agent Memory does | Where |
| --- | --- | --- |
| You decide what's worth writing down | **Extraction:** learns what's worth keeping, and screens out sensitive data | This section |
| Nothing expires; you edit the file | **Lifecycle:** retention, updating old facts when you change your mind, and forgetting | This section and the next |
| Everything goes in every request | **Retrieval:** brings back only what fits the task | The next section |

Redis Agent Memory keeps two kinds of memory:

- **Session memory (short-term):** every message, who sent it, and which session it belongs to. Your application adds these as you talk.
- **Long-term memory:** short facts such as "Prefers Google-style docstrings". Redis Agent Memory **extracts** these from your sessions in the background; your application never writes them.

## Demo: how the memory is set up

Before using it, look at what it's set up to keep. Open the **Agent Memory** panel (panel menu, top left) and choose **Store settings**:

- **Lifecycle:** sessions are kept for a day, long-term memories for a week. Nobody has to remember to clean up.
- **Extraction cadence:** it runs about every minute while a session is active.
- **`coding_preference`:** a memory type the workshop defined, with a prompt that tells extraction to keep only what *you* say about how you want code written, and to ignore what the assistant did. This is the "deciding what's worth keeping" job, written once for everyone instead of by each person.
- **`longTermMemoryExclusions`:** what must never be kept. Every memory is screened before it's stored long-term: an email address is **redacted**, and anything that looks like an API token (`ghp_…`, `sk_…`) **drops** the whole memory. Built-in detectors also cover card numbers, IP addresses, phone numbers and US Social Security numbers, and you can add your own as a regex or as a plain-language rule.

These are store settings, not code: whoever runs the store decides what it learns and how long it keeps it.

## Demo: switch on capture

In `agent.py:flags`, set `CAPTURE = True`. That turns on two places in `handle`. First, before the model is called, `agent.py:capture` records your message:

```python
if CAPTURE:
    services.memory.add_session_event(
        session_id=session.session_id, actor_id=session.owner, role=models.MessageRole.USER,
        content=[models.Text(text=task)], created_at=datetime.now(timezone.utc),
    )
```

Then, after the agent answers, `agent.py:answer` records the answer the same way, with the `ASSISTANT` role. The role matters: the memory should learn *your* preferences, not the model's suggestions.

Save, type `exit`, start the agent again, then mention the docstring preference and ask for the slug function. Mention one thing that should *not* be kept, too:

```text
In test fixtures, use my email jane.doe@example.com as the sample address.
```

- `/events` shows both messages and both answers, stored for this session.
- `/new-session`, then `/sessions`: the earlier session is listed. `/resume 1` (its number in the list) brings the whole conversation back, because Redis Agent Memory kept it.

Resuming replays everything, though, which is the "everything in every request" problem again. You want just the bits that matter. Run `/memories`: it may still be empty, because extraction runs in the background. We come back to it in the next section.

## Your turn (5 minutes)

**1.** In `agent.py:flags`, switch capture on:

```python
CAPTURE = True
```

Save, type `exit` in the terminal, then start the agent again:

```bash
uv run --group iris python main.py
```

**2.** State your preference, mention something that shouldn't be kept, and ask for the slug function:

```text
By the way, I like Google-style docstrings on my functions.
```

```text
In test fixtures, use my email jane.doe@example.com as the sample address.
```

```text
Show me a quick function that turns a title into a URL slug.
```

**3.** See what was stored for this session:

```text
/events
```

**Look for:** your messages and the agent's answers, word for word.

**4.** Start fresh, list your sessions, and bring the first one back:

```text
/new-session
```

```text
/sessions
```

```text
/resume 1
```

**Look for:** the conversation is back.

**5.** In the **Agent Memory** panel, choose **Sessions**: the same conversation, straight from Redis Agent Memory.

**Try your own:** state another preference in your own words; you'll see whether it was kept in the next section.

Next: [recall in a fresh session](04-recall.md).
