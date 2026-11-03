---
title: Recall in a fresh session
editorFile: agent.py
slides: /slides/04-recall.md
---
**10-minute demo, 4 minutes for you.** Bring back just the preference, not the whole conversation, and change your mind when you need to.

## Demo: extraction happened

`/memories` now shows what Redis Agent Memory extracted from the conversation, each with a type and a short ID:

- `coding_preference`: "Prefers Google-style docstrings."
- `semantic` and `episodic`: general facts and events, such as "The assistant provided a function that converts a title into a URL slug."

- The fixture preference, as "Uses [REDACTED] as the sample address in test fixtures." The email detector removed the address before the memory was stored.

Nobody wrote these down. The `coding_preference` one came from the store's custom type; the built-in types catch everything else, including things the assistant did.

Now run `/events`: the session still has the email, word for word. Exclusions protect **long-term** memory; session memory keeps the raw messages until it expires (a day on this store). Don't capture what you couldn't keep for a day.

## Demo: retrieval, only what fits

In `agent.py:88`, set `RECALL = True`. That turns on `agent.py:111`, which searches long-term memory with the new task as the query:

```python
if RECALL:
    found = services.memory.search_long_term_memory(request={
        "text": task,
        "filter_": {"owner_id": {"eq": session.owner}, "memory_type": {"eq": "coding_preference"}},
        "limit": 5,
    })
    preferences = [item.text for item in found.items]
```

**Predict:** why filter on the owner, not the session?

The preference came from an earlier session, so filtering on today's session would find nothing. It also filters on `coding_preference`, so the assistant's own actions never come back as "preferences", and it takes at most five, ranked by how well they fit the task. This is the third job: no dumping everything into every request.

Then `agent.py:132` builds the request, and adds what was found as one short message:

```python
if preferences:
    recalled.append("What you know about this user's preferences:\n" + "\n".join(f"- {p}" for p in preferences))
```

Save, type `exit`, start again (a new session, same owner), and ask:

```text
Show me a function that removes duplicates from a list but keeps the order.
```

The terminal shows what was recalled, and `/view-context` shows it as the second message, while the conversation holds only this task. Memory isn't the model remembering. It's your application choosing what to put back in the request.

## Demo: lifecycle, change your mind

Suppose you go off Google-style docstrings. With `AGENTS.md` you had to remember to edit the file, and until someone did, the old rule stayed. Here, just say so:

```text
Actually, I've switched to NumPy-style docstrings.
```

Give extraction a minute, then `/memories`: still **one** docstring memory, same ID, now "Prefers NumPy-style docstrings." Extraction compares what you said with what it already knows about you, and updates the old memory instead of keeping two that disagree.

To drop it altogether, open the **Agent Memory** panel's **Long-term memories** tab and press **Forget** next to the preference (or run `/forget <id>` with the ID from `/memories`). Ask for the de-duplication function again: the terminal says *Recalled: nothing*.

Forgetting is per person and immediate, and the store's retention settings expire old memories without anyone remembering to. That's the lifecycle job.

One catch: extraction runs about a minute after each message, on that minute's messages. If you forget a preference while a run is still pending, that run can learn it again. Before pressing **Forget**, open the session in the panel's **Sessions** tab (or run `/events`) and wait for *Extraction: up to date*. Forgetting removes what was learned, not the conversation: the session itself is kept until it expires (a day here).

## Your turn (4 minutes)

**1.** In `agent.py:88`, switch recall on:

```python
RECALL = True
```

Save, type `exit` in the terminal, then start the agent again:

```bash
uv run --group iris python main.py
```

**2.** See what Redis Agent Memory learned:

```text
/memories
```

**Look for:** your docstring preference as a `coding_preference`, the fixture one with `[REDACTED]`, and the built-in `semantic` and `episodic` memories.

**3.** Ask for something new, then look at what was sent:

```text
Show me a function that removes duplicates from a list but keeps the order.
```

```text
/view-context
```

**Look for:** "What you know about this user's preferences" in the second message.

**4.** If you have time, change your mind, wait a minute, and look again:

```text
Actually, I've switched to NumPy-style docstrings.
```

```text
/memories
```

**Look for:** the same memory, updated.

**5.** Run `/events` and wait for *Extraction: up to date*. Then forget the preference in the **Agent Memory** panel (**Forget** next to it), and ask for the de-duplication function again. **Look for:** *Recalled: nothing*. Then state the Google-style preference again, so it's there for the last section.

**6.** Ask one more question. Every agent will answer it differently; in the next section the team approves one answer:

```text
Can I use real customer data in test fixtures?
```

If `/memories` is empty, mention the preference again and wait a minute.

Next: [the team's way with Redis Agent Playbook](/build?lesson=05-playbook.md).
