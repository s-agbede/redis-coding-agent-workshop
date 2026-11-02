# Recap: what goes into the request

**4 minutes.** Part 1 built a working coding agent. Today we decide what that agent should *know*.

## Part 1 in one picture

The model never touches your files. It *asks* for a tool, your Python code runs it, and the result goes back in the next request. Every turn, the application assembles a fresh request from:

1. System and project instructions
2. Conversation history from this session
3. The new user message

The model knows only what is in that request. Everything in this workshop is a decision about what else belongs there.

[Diagram placeholder: user task → model → tool request → Python tool → tool result → model answer.]

## Today's question

**What should a coding agent know, where does that knowledge come from, and who owns it?**

| Source | Owner | Where it lives |
| --- | --- | --- |
| The conversation | This session | Process memory; gone after a new session |
| Project instructions | The project | `AGENTS.md` in the repository |
| Personal preferences | You | **Redis Agent Memory**, learned from your work |
| Team procedures | The organisation | **Redis Agent Playbook**, published and versioned |

## How each section runs

The instructor demonstrates each section, then you get **five minutes** for a *Your turn* card. Each card copies a ready-made version of `agent.py` from `solutions/steps/`. The code is there to read and understand, not to type.

You edit **`agent.py`**; the agent edits files in **`project/`**. After any change to `agent.py`: save, type `exit`, and relaunch.

## Your turn: get ready

In the shell terminal, from the repository root:

```bash
uv run --group iris python main.py
```

At the `You >` prompt, enter `/status`. Capture, recall and Playbook should all be disabled. The commands you will use today:

| Command | Shows |
| --- | --- |
| `/status` | Enabled capabilities, owner, session and the next step |
| `/view-context` | The current context sources and the exact latest model request |
| `/new-session` | Starts a fresh conversation (same owner); reloads `AGENTS.md` |
| `/events` | Session events stored in Redis Agent Memory |
| `/memories` | Long-term preferences Redis Agent Memory extracted for you |
| `/skills` | The team procedure retrieved from Redis Agent Playbook |
| `/verify` | Runs the independent checker against `project/validator.py` |

Next: [the amnesiac](02-forgetting.md).
