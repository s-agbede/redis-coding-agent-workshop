---
title: The amnesiac and notes on the desk
editorFile: project/AGENTS.md
---
**8-minute demo, 5 minutes for you.** A preference works within a session and is gone in the next. A file survives, but only holds what someone chose to write down.

## Demo: the amnesiac

Mention a preference the way you would to a colleague:

```text
By the way, I like Google-style docstrings on my functions.
```

Then ask for something small:

```text
Show me a quick function that turns a title into a URL slug.
```

The function gets a Google-style docstring, because your preference is in the conversation, and the conversation is part of the request.

Now run `/new-session` and ask for another function:

```text
Show me a function that counts the words in a sentence.
```

**Predict:** will this one get a Google-style docstring?

Run `/view-context`. The request holds the system prompt, `AGENTS.md` and your new message. The preference isn't there. The model didn't forget; the application simply stopped sending it.

## Demo: notes on the desk

Some things you'd rather write down:

```text
Add a note to AGENTS.md that we target Python 3.12.
```

Run `/new-session` and ask:

```text
Which Python version do we target?
```

The agent knows, and `/view-context` shows why: the Python 3.12 note is in the first message. `AGENTS.md` is reloaded into every session.

That works for conventions someone *decides* to write down. Most preferences come up in passing and never make it into a file. The next section deals with those.

## Your turn (5 minutes)

1. Tell the agent your docstring preference, then ask for the slug function.
2. `/new-session`, ask for the word-count function, then `/view-context`. **Look for:** no docstring preference in the request.
3. Ask the agent to add the Python 3.12 note to `AGENTS.md`.
4. `/new-session`, ask which Python version you target, then `/view-context`. **Look for:** the Python 3.12 note in the first message.

Next: [capture with Redis Agent Memory](/build?lesson=03-capture.md).
