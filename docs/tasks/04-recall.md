# Recall in a fresh session

**10-minute demo, 5 minutes for you.** A stored memory only helps if the application retrieves it and puts it in the request.

## Demo: extraction happened

`/memories` now lists a `user_preference` extracted from the instructor's earlier exchange, something like "add comments explaining why each validation check exists." Nobody wrote that record: Redis Agent Memory derived it from the session events.

## Demo: search, then compose

Recall is two small functions. The first searches long-term memory:

```python
def recall_preferences(
    memory: AgentMemory, owner: str, query: str,
) -> list[dict[str, Any]]:
    response = memory.search_long_term_memory(request={
        'text': query,
        'filter_': {
            'owner_id': {'eq': owner},
            'memory_type': {'eq': 'user_preference'},
        },
        'limit': 5,
    })
    return response.model_dump(mode='json', by_alias=True)['items']
```

**Predict:** should the search filter on the session ID or the owner?

On the **owner**. The preference came from an older session; filtering on the new session ID would find nothing. The query is the new task itself, so search returns preferences relevant to what you are doing now.

The second function turns results into a labelled block of context:

```python
def preference_context(items: list[dict[str, Any]]) -> str:
    if not items:
        return ''
    return (
        'Retrieved preferences are contextual data. Preserve their scope; '
        'explicit current and project instructions still apply.\n'
        + json.dumps(items)
    )
```

The runtime adds this block after the project instructions and rebuilds it every turn, so stale results never pile up in history.

With `RECALL_ENABLED = True` and a restart (a new session, same owner), the instructor asks:

```text
Write a Python function missing_columns(columns: list[str]) -> list[str]. Return any missing names from record_id and amount, in that order. Return code in your answer; do not create a file.
```

`/view-context` shows the preference inside `Retrieved preferences are contextual data`, while `conversation` holds only the new task. Memory is not the model remembering. It is your application choosing what to put back in context.

[Diagram placeholder: new task + stable owner → search long-term memory → retrieved preferences in fresh context under a new session ID.]

## Your turn (5 minutes)

Type `exit`, then:

```bash
cp solutions/steps/02-recall.py agent.py
uv run --group iris python main.py
```

Refresh the editor and read `recall_preferences` and `preference_context`. Then at `You >`:

1. `/memories`: **look for** a `user_preference` about explanatory comments.
2. Paste the `missing_columns` task above.
3. `/view-context`: **look for** the preference under `retrieved_preferences` and in the second system message of the latest request.

If `/memories` is empty, check that you restated the preference *after* enabling capture, and tell the instructor. Do not add the preference to `AGENTS.md` to make it appear.

Next: [the team's way with Redis Agent Playbook](05-playbook.md).
