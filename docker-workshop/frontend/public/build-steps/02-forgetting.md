---
title: The amnesiac and notes on the desk
editorFile: project/AGENTS.md
slides: /slides/02-forgetting.md
---
**7-minute demo, 4 minutes for you.** A preference works within a session and is gone in the next. Writing it down fixes that, at a cost.

## Demo: the amnesiac

Mention a preference the way you would to a colleague, then ask for a small function:

```text
By the way, I like Google-style docstrings on my functions.
```

```text
Show me a quick function that turns a title into a URL slug.
```

The function gets a Google-style docstring, with `Args:` and `Returns:`, because your preference is in the conversation and the conversation is part of the request.

Now run `/new-session` and ask for **the same function again**.

**Predict:** will the docstring look the same?

It may differ: the model can still choose Google-style on its own, so the output style alone is not proof of memory. Run `/view-context` to see why. The request holds the system prompt, `AGENTS.md` and your message, and nothing about docstrings. The model didn't forget; the application simply stopped sending it.

## Demo: write it down

The obvious fix is to write it where every session will see it:

```text
Add to AGENTS.md that I like Google-style docstrings on my functions.
```

Run `/new-session`, ask for the slug function again, and it works: the Google-style instruction is present in every new session. Check whether the model follows it. `/view-context` shows why: the rule is in the first message, because `AGENTS.md` is reloaded into every session.

## What writing it down costs

It works, but look at what it took and where it leads:

- **Someone had to decide and write it.** You noticed the preference and phrased it as a rule. Most preferences come up in passing and never get that treatment.
- **It applies to everyone.** `AGENTS.md` belongs to the project. A teammate who prefers NumPy-style docstrings now gets yours.
- **It only grows.** Every preference you add rides along in every request, relevant or not. Ask for FizzBuzz and it still carries the docstring rule, the logging rule, the testing rule…
- **Nothing expires or gets corrected.** Change your mind and you have to remember to edit the file; until then, old and new rules sit side by side.

So doing this well takes three jobs: **deciding what's worth keeping**, **managing it over time**, and **bringing back only what's relevant to the task**. Redis Agent Memory does those three, and the next two sections take them in turn.

Before moving on, take the rule back out, so you can tell later whether the preference came from memory or from the file:

```text
Remove the docstring line from AGENTS.md.
```

Having to remember that step is the "nothing expires" problem in miniature.

## Your turn (4 minutes)

**1.** Tell the agent your preference, then ask for the slug function:

```text
By the way, I like Google-style docstrings on my functions.
```

```text
Show me a quick function that turns a title into a URL slug.
```

**2.** Start a fresh conversation and ask for the slug function again (the same prompt as above):

```text
/new-session
```

**Look for:** nothing about your docstring preference in `/view-context`. The model may still choose the same style by chance.

**3.** Write it down, start fresh, and ask for the slug function once more:

```text
Add to AGENTS.md that I like Google-style docstrings on my functions.
```

**Look for:** after `/new-session`, Google-style again, and the rule in the first message of `/view-context`.

**4.** Take it back out, so later sections get it from memory, not the file:

```text
Remove the docstring line from AGENTS.md.
```

**Try your own:** any preference you'd want an agent to keep, such as "I prefer pathlib over os.path".

Next: [capture with Redis Agent Memory](/build?lesson=03-capture.md).
