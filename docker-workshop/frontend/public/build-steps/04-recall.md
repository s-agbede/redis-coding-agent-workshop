---
title: Recall in a fresh session
editorFile: agent.py
slides: /slides/04-recall.md
---
**10-minute demo, 5 minutes for you.** Bring back just the preference, not the whole conversation, and change your mind when you need to.

## Demo: extraction happened

`/memories` now shows what Redis Agent Memory extracted from the conversation, each with a type and a short ID:

- `coding_preference`: "Prefers Google-style docstrings."
- `semantic` and `episodic`: general facts and events, such as "The assistant provided a function that converts a title into a URL slug."

Nobody wrote these down. The `coding_preference` one came from the store's custom type; the built-in types catch everything else, including things the assistant did.

## Demo: retrieval, only what fits

In `agent.py:88`, set `RECALL = True`. That turns on `agent.py:110`, which searches long-term memory with the new task as the query:

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

Then `agent.py:127` builds the request, and adds what was found as one short message:

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

Suppose you go off Google-style docstrings. With `AGENTS.md` you had to remember to edit the file. Here, open the **Agent Memory** panel's **Long-term memories** tab and press **Forget** next to the preference (or run `/forget <id>` with the ID from `/memories`). Ask for the de-duplication function again: the terminal says *Recalled: nothing*.

Forgetting is per person and immediate, and the store's retention settings expire old memories without anyone remembering to. That's the lifecycle job.

## Your turn (5 minutes)

1. In `agent.py:88`, set `RECALL = True`. Save, type `exit`, and start again.
2. `/memories`. **Look for:** your docstring preference as a `coding_preference`, next to the built-in `semantic` and `episodic` memories.
3. Ask for the de-duplication function above, then `/view-context`. **Look for:** "What you know about this user's preferences" in the second message.
4. Forget the preference in the **Agent Memory** panel, and ask again. **Look for:** *Recalled: nothing*. Then mention the preference again, so it's there for the last section.

If `/memories` is empty, mention the preference again and wait a minute.

Next: [the team's way with Redis Agent Playbook](/build?lesson=05-playbook.md).
