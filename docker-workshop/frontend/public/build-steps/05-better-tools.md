---
title: Make the reader useful on larger files
editorFile: agent.py
---
**10 minutes.** The plain reader works, but sends an entire file on every read. You will improve the observation without taking navigation decisions away from the model.

## Design the result before coding

Take a minute to propose what a page should contain. How will the agent know the text is incomplete, locate evidence, and request the next part?

<details>
<summary>Our design</summary>

Return numbered lines within a budget, plus an explicit truncation notice and next offset. A silent cut could make the agent mistake a partial file for the whole file. The supplied `file_excerpt` helper handles empty files, invalid ranges and long lines as well as normal pages.

</details>

## Walk through a page

`offset` is a **line number**, starting at 1; `limit` is the maximum number of lines to return. Python list indexes start at 0. The helper converts between them like this:

```text
start_index = offset - 1
end_index = min(len(lines), start_index + limit)
for index in range(start_index, end_index):
    numbered = f"{index + 1}: {lines[index]}"
```

For a seven-line file, imagine these requests. This is an illustration; the model will choose its own pages in the live exercise.

| Requested page | Python indexes considered | Returned line numbers | Next offset |
| --- | --- | --- | --- |
| `offset=1, limit=3` | 0, 1, 2 | 1, 2, 3 | `1 + 3 = 4` |
| `offset=4, limit=3` | 3, 4, 5 | 4, 5, 6 | `4 + 3 = 7` |
| `offset=7, limit=3` | 6 | 7 | No continuation: end of file |

The helper adds numbered lines to `page`, stopping earlier if another line would exceed the character budget. Its continuation calculation is:

```text
next_offset = offset + len(page)
```

Use the number of lines **actually returned**, not the requested limit. If a page beginning at line 4 can fit only two lines, the next offset is `4 + 2 = 6`; jumping to 7 would skip evidence. The result tells the model whether more lines remain and where to continue.

If even one line exceeds the character budget, the helper labels that line as cut and suggests inspecting a column range with a command tool. Ordinary line paging cannot recover the rest of that same line. Our workshop's release log uses normal-sized lines; command tools arrive in the final lesson.

## Improve the same function and its contract

Type `exit`, then edit **agent.py**. Add `offset` and `limit` to `read_file` and return the supplied helper's formatted excerpt:

<details>
<summary>Copyable solution — replace the whole read_file function</summary>

```python
def read_file(path: str, offset: int = 1, limit: int = 80) -> str:
    text = Path(path).read_text(encoding="utf-8")
    return file_excerpt(text, offset=offset, limit=limit)
```

</details>

Also replace the `TOOL_SCHEMAS` line so the model knows those arguments exist:

```python
TOOL_SCHEMAS = [LIST_SCHEMA, PAGED_READ_SCHEMA]
```

This explicit schema change matters. Updating a Python signature alone does not tell the remote model how to call it. No `--paged` mode or signature detection is involved.

Save and restart:

```bash
uv run python main.py
```

```text
What's the latest release decision?
```

Inspect numbered lines and continuation guidance in the tool results. The model chooses which pages to request, and **your existing loop** executes those requests. There is no manual “next page” step. If the answer uses only the short brief, ask it to support the answer with the release log itself.

Compare the bounded results with the earlier whole-file output. A shorter individual result does not guarantee fewer total tokens or fewer calls: navigation has a cost too.

<details>
<summary>What should remain true after this change?</summary>

The answer should still have supporting evidence. For the log's decision, look near numbered line 180 in the output; this is a place to inspect after the run, not an offset to dictate in the prompt. If the model stops too early, ask what evidence is missing and inspect whether the continuation hint reached it.

</details>

Try a follow-up of your own about the conditions for release. Your history and reader now work together. Next, you will let this same program edit an application and check what happened.

<details>
<summary>Catch up if needed</summary>

Save your attempt separately first. After typing `exit` to leave the chat, this copies the complete learner file **through this lesson**, including the earlier exercises:

```bash
cp solutions/steps/05-paging.py agent.py
```

Restart with `uv run python main.py`. Refresh the open editor file after copying, before saving over it. This is an explicit replacement of your work, not an automatic fallback.

</details>
