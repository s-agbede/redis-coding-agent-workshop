---
title: Recall in a fresh session
editorFile: agent.py
slides: /slides/04-recall.md
---
**10-minute demo, 4 minutes for you.** Bring back just the preference, not the whole conversation, and change your mind when you need to.

## Demo: extraction happened

`/memories` now shows what Redis Agent Memory extracted from the conversation, each with a type and a short ID:

- `coding_preference`: "Prefers Google-style docstrings."
- Other types may appear, such as `semantic`, `episodic`, or a store-specific `user_preference`. The exact set depends on the store and what extraction found.

- If the email detector is enabled with the redact action, an extracted fixture preference should hide the address. If that detector is off, the synthetic address may remain unchanged, as it did in the managed rehearsal. A missing fixture memory alone does not prove redaction.

Nobody wrote these down. The `coding_preference` one came from the store's custom type; other types can include facts about what the assistant did. Extraction need not produce a memory for every message.

Now run `/events`: the session still has the email, word for word. Configured exclusions apply to **long-term** memory; session memory keeps the raw messages until it expires (a day on this store). Don't capture what you couldn't keep for a day.

## Demo: retrieval, only what fits

In `agent.py:88`, set `RECALL = True`. That turns on `agent.py:111`, which searches long-term memory with the new task as the query:

```python
if RECALL:
    found = services.memory.search_long_term_memory(request={
        "query": task,
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

Give extraction a minute, then `/memories`: still **one `coding_preference`** for docstrings, same ID, now "Prefers NumPy-style docstrings." Extraction compares what you said with what it already knows about you, and updates the old memory instead of keeping two that disagree.

To drop it altogether, open the **Agent Memory** panel's **Long-term memories** tab and press **Forget** next to the preference (or run `/forget <id>` with the ID from `/memories`). Run `/new-session`, then ask for the de-duplication function again. The forgotten preference should be absent from *Recalled:* and `/view-context`. You see *Recalled: nothing* only if no other coding preferences remain. Starting fresh also removes the preference from conversation history.

Forgetting is per person and immediate, and the store's retention settings expire old memories without anyone remembering to. That's the lifecycle job.

One catch: extraction runs about a minute after each message, on that minute's messages. If you forget a preference while a run is still pending, that run can learn it again. Before pressing **Forget**, stop adding messages and wait until `/memories` shows the corrected preference. On GA, the service does not expose a per-session extraction bookmark; the panel and `/events` say so. Older services may show *Extraction: up to date*. Forgetting removes what was learned, not the conversation: the session itself is kept until it expires (a day here).

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

**Look for:** your docstring preference as a `coding_preference`. Other types and the fixture memory are conditional. Check the synthetic address against the actual detector settings; do not assume it was redacted.

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

**5.** Stop sending messages and wait until `/memories` shows the corrected preference. On GA, `/events` cannot report extraction completion. Then forget the `coding_preference` in the **Agent Memory** panel (**Forget** next to it), run `/new-session`, and ask for the de-duplication function again. **Look for:** the deleted preference is absent from *Recalled:* and `/view-context`. Other preferences may still be recalled. Then state the Google-style preference again, so it's there for the last section.

**6. Optional instructor promotion demo.** If the instructor has configured Playbook FAQ extraction from this Memory store, ask the following question. The instructor can review and publish a proposed answer in the next section. Without that setup, skip this step; section 5 uses an existing published FAQ instead:

```text
Can I use real customer data in test fixtures?
```

If `/memories` is empty, mention the preference again and wait a minute.

Next: [the team's way with Redis Agent Playbook](/build?lesson=05-playbook.md).
