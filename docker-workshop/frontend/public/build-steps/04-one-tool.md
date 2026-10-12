---
title: Give the model a file reader
editorFile: agent.py
---
**10 minutes.** Your own loop can discover files, but `read_file` returns an error. Let's supply the missing observation and repeat the same question.

## Implement the missing capability

Type `exit` to leave the chat. In **agent.py**, replace `read_file(path)` so it returns the file's UTF-8 text. Leave the schema and loop unchanged. Python's `Path` is already imported.

<details>
<summary>Copyable solution — replace the whole read_file function</summary>

```python
def read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")
```

</details>

Save, restart, and ask the same question:

```bash
uv run python main.py
```

```text
What's the latest release decision?
```

Watch `list_files` reveal candidate names and `read_file` bring actual text into the conversation. `list_files` returns usable paths: listing `checkpoints/`, for example, includes `checkpoints/release_log.md`. Your reader uses that path from the same working directory. The model chooses which file to read, and your loop can handle several requests. You do not supply filenames, offsets or a sequence of actions in the user question.

Compare the new reader result with the error you saw before. Locate the exact sentence that supports the answer. Does the decision say that checks **have passed**, or that release is conditional on checks passing?

<details>
<summary>Evidence to look for</summary>

The fictional release log records that Cedar is ready **after acceptance checks pass**. That is a condition for release, not evidence that somebody ran those checks. Your reader supplies the source; the model still needs to interpret it accurately.

</details>

The release log is deliberately long. Look at the **RESULT** panel's character count. Returning the whole file can bury the useful evidence among routine entries. If your model chose only the short project brief, ask “Please inspect the release log itself and support your answer.” This is an evidence request, not instructions for paging.

**Before the next lesson:** what should a shorter tool response preserve so the agent can still find evidence later in the file?

<details>
<summary>Catch up if needed</summary>

Save your attempt separately first. After typing `exit` to leave the chat, this copies the complete learner file **through this lesson**, including the earlier exercises:

```bash
cp solutions/steps/04-reader.py agent.py
```

Restart with `uv run python main.py`. Refresh the open editor file after copying, before saving over it. This is an explicit replacement of your work, not an automatic fallback.

</details>
