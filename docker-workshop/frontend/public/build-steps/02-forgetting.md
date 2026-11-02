---
title: The amnesiac and notes on the desk
editorFile: project/AGENTS.md
slides: /slides/02-markdown.md
---
**8-minute demo, 5 minutes for you.** A preference works within a session and is gone in the next. A file survives, but only holds what someone chose to write down.

## Demo: the amnesiac

The instructor states a preference in conversation:

```text
Always add a short comment explaining why each validation check exists. Keep this preference in our conversation only; do not write it to AGENTS.md or another file.
```

Then asks for a small piece of code:

```text
Write a Python function valid_report_filename(name: str) -> bool. Accept only names beginning report_ and ending .csv, with at least one character between them. Return code in your answer; do not create a file.
```

The answer follows the preference because the preference is in the conversation history, which is part of the request.

**Predict:** after `/new-session`, is the preference still in the request?

`/new-session` then `/view-context`: `conversation` is empty and the preference appears nowhere. The model did not "forget"; the application simply stopped sending it.

## Demo: notes on the desk

The instructor asks the agent to write a project convention to a file:

```text
Use your file tools to read AGENTS.md and add this project instruction: Use uv for Python projects. Preserve all existing text. Do not add the commenting preference or any other instruction. Show what you changed.
```

After `/new-session` and `/view-context`, `project_instructions` contains "Use uv for Python projects." The file survives because the application reloads it into every new session.

Files are a good home for conventions someone *decides* to write down. Most preferences come up in passing, while working, and never make it into a file. That is the gap the next section fills.

Keep the commenting preference out of `AGENTS.md` all workshop: later we need to show that Redis Agent Memory supplies it, not the file.

[Diagram placeholder: a new session clears conversation history while reloading the same AGENTS.md into fresh context.]

## Your turn (5 minutes)

1. Paste the commenting preference, then the `valid_report_filename` task, at `You >`.
2. Run `/new-session`, then `/view-context`. **Look for:** `conversation: []` and no commenting preference anywhere.
3. Paste the `AGENTS.md` request above. Check the agent's diff.
4. Run `/new-session`, then `/view-context`. **Look for:** "Use uv for Python projects." in `project_instructions`.

Next: [capture with Redis Agent Memory](/build?lesson=03-capture.md).
