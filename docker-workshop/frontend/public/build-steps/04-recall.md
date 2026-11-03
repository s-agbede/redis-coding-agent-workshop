---
title: Recall in a fresh session
editorFile: agent.py
---
**10-minute demo, 5 minutes for you.** Bring back just the preference, not the whole conversation.

## Demo: extraction happened

`/memories` now shows what Redis Agent Memory extracted from the conversation, each with a type:

- `coding_preference`: "Prefers Google-style docstrings."
- `semantic` and `episodic`: general facts and events, such as "The assistant provided a function that converts a title into a URL slug."

Nobody wrote these down. The `coding_preference` type is ours: the workshop's store defines it, with a prompt that extracts only what *you* say about how you want code written. The built-in types catch everything else, including things the assistant did.

## Demo: search, then add to the request

Recall is two small functions. The first searches long-term memory, using the new task as the query:

```python
def recall_preferences(
    memory: AgentMemory, owner: str, query: str,
) -> list[dict[str, Any]]:
    response = memory.search_long_term_memory(request={
        'text': query,
        'filter_': {
            'owner_id': {'eq': owner},
            'memory_type': {'eq': 'coding_preference'},
        },
        'limit': 5,
    })
    return response.model_dump(mode='json', by_alias=True)['items']
```

**Predict:** should it filter on the session or on the owner?

On the owner. The preference came from an earlier session, so filtering on today's session would find nothing. It also filters on our `coding_preference` type, so the assistant's own actions never come back as "preferences".

The second function turns the results into a short message for the model:

```python
def preference_context(items: list[dict[str, Any]]) -> str:
    if not items:
        return ''
    return "What you know about this user's preferences:\n" + '\n'.join(
        f"- {item['text']}" for item in items
    )
```

With recall switched on, the instructor starts fresh and asks:

```text
Show me a function that removes duplicates from a list but keeps the order.
```

`/view-context` shows the preference as the second message, and the conversation holds only this task. Memory isn't the model remembering. It's your application choosing what to put back in the request.

## Your turn (5 minutes)

Type `exit`, then:

```bash
cp solutions/steps/02-recall.py agent.py
uv run --group iris python main.py
```

Read `recall_preferences` and `preference_context` in `agent.py`. Then:

1. `/memories`. **Look for:** your docstring preference as a `coding_preference`, next to the built-in `semantic` and `episodic` memories.
2. Ask for the de-duplication function above.
3. `/view-context`. **Look for:** "What you know about this user's preferences" in the second message.

The **Agent Memory** panel's **Long-term memories** tab shows the same record, with its type. You may also see a `semantic` memory: Redis Agent Memory extracts more than one kind.

If `/memories` is empty, mention the preference again and wait a minute.

Next: [the team's way with Redis Agent Playbook](/build?lesson=05-playbook.md).
