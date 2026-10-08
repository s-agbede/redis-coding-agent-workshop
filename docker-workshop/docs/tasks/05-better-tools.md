# Make the reader useful on larger files

**7 minutes.** Your reader can supply a local fact. Let's give it a larger file and decide whether its result is useful for the question we asked.

## Give the reader a larger input

The supplied **checkpoints/release_log.md** has 200 lines. Most are routine entries; the release decision is near line 180. Select **Run code**, then press **Enter** when the checkpoint proposes its read:

```bash
uv run python -m checkpoints.stage2_one_tool \
  --prompt "Read checkpoints/release_log.md. What release decision is recorded near line 180? If range selection is available, read offset=170, limit=20."
```

When your plain reader executes, it returns all 200 lines. Find the decision in the tool result and look at the printed character count. How much of the returned text did you need to answer this question?

The answer may be correct. The problem we can observe is unnecessary output and difficulty finding its location in the source. The character count measures the returned text, not model tokens; this file does not have to exceed the model's context window for the result to be worth improving.

## Decide what a shorter result must preserve

Before opening our choice, discuss: **if we return only part of a file, what must the result include so the agent can locate it and continue?**

<details>
<summary>Compare your design with ours</summary>

| Keep | Why it matters |
| --- | --- |
| The selected text | Supplies evidence for the current question. |
| Line numbers | Lets the agent identify the source location and inspect nearby code. |
| Continuation guidance | Makes omissions visible and tells the agent how to request more. |

We will let the caller select a range with `offset` and `limit`. Returning a short answer without its location or omissions would make it harder to judge what the agent has actually read.

</details>

## Improve the result

Open **tools.py**. Add `offset` and `limit` to `read_file`, then pass the text to the supplied `file_excerpt` helper. It numbers lines, bounds the output and adds continuation information when content remains. Offsets start at **1**.

<details>
<summary>Hint</summary>

Keep the file read. Add defaults to the function signature and return `file_excerpt(text, offset, limit)`.

</details>

<details>
<summary>Copyable solution — replace the whole read_file function</summary>

```python
def read_file(path: str, offset: int = 1, limit: int = MAX_READ_LINES) -> str:
    text = Path(path).read_text(encoding="utf-8")
    return file_excerpt(text, offset, limit)
```

</details>

Save, then select **Run code** below. The only command change is `--paged`, which advertises the richer schema. The question is unchanged:

```bash
uv run python -m checkpoints.stage2_one_tool --paged \
  --prompt "Read checkpoints/release_log.md. What release decision is recorded near line 180? If range selection is available, read offset=170, limit=20."
```

Inspect the proposed arguments before pressing **Enter**. If the model requests `offset=170, limit=20`, the result contains numbered lines **170–189**, including the decision on line **180**, and continuation guidance for line **190**. The model chooses its arguments; the prompt requests a range but does not force it. Use the actual result to assess what it read.

Compare the two tool results: the text returned, the character counts and the source locations you can identify. The full agent's supplied `TOOL_SCHEMAS` already describes the new inputs.

**Your decision:** is the excerpt enough evidence for our question, or would you request another page? Point to the line that supports your choice.

<details>
<summary>Compare your reasoning</summary>

If the returned range includes the decision on line 180, it supports an answer about that recorded decision. A range that misses it does not. The line numbers let us check; the continuation information makes clear that other content remains unread.

A different question may need more evidence. To follow a reference or request another page, our harness must be able to handle another tool request. That is our next step.

</details>

The core exercise ends here. The two experiments below are for spare time.

<details>
<summary>Optional: try the continuation</summary>

To ask for the next page, run:

```bash
uv run python -m checkpoints.stage2_one_tool --paged \
  --prompt "Read checkpoints/release_log.md with offset=190 and limit=20. Show the returned lines."
```

Check the proposed arguments and returned lines. The file ends at line 200, so a read starting at 190 can return fewer than 20 lines.

</details>

<details>
<summary>Optional description experiment</summary>

The description in the `read_file` entry of **TOOL_SCHEMAS** is part of the model's input. A helpful description says when to use the tool, what it returns and how to request more.

Try this wording in the description:

```text
Read numbered lines from a known UTF-8 file. Use offset and limit to select a range. If the result reports more lines, read the next offset to continue.
```

Save, then rerun the same `--paged` release-decision command above. Stop a still-running checkpoint with **Ctrl+C** first. Compare the proposed arguments. The model may choose well with either description; editing it does not guarantee a different choice.

</details>
