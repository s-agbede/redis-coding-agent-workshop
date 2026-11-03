# Recap: what goes into the request

**4 minutes.** Part 1 built a working coding agent. Today we decide what that agent should *know*.

## Part 1 in one picture

The model never touches your files. It *asks* for a tool, your Python code runs it, and the result goes back in the next request. Every turn, the application builds a fresh request from:

1. The system prompt and the project's `AGENTS.md`
2. The conversation so far in this session
3. Your new message

The model knows only what is in that request. Everything today is a decision about what else belongs there.

## Today's question

**What should a coding agent know, where does that knowledge come from, and who owns it?**

| Source | Owner | Where it lives |
| --- | --- | --- |
| The conversation | This session | Gone when you start a new session |
| Project conventions | The project | `AGENTS.md` in the repository |
| Personal preferences | You | **Redis Agent Memory**, learned from your conversations |
| Team procedures | The organisation | **Redis Agent Playbook**, published and versioned |

## How each section runs

The instructor demonstrates, then you get **five minutes**. Each *Your turn* copies a ready-made `agent.py` from `solutions/steps/`; the code is there to read, not to type.

You edit **`agent.py`**; the agent edits files in **`project/`**. After changing `agent.py`, type `exit` and start it again.

## Your turn: get ready

In the terminal:

```bash
uv run --group iris python main.py
```

You'll see your owner ID, session ID, and which capabilities are on (all off for now). Commands you'll use:

| Command | What it does |
| --- | --- |
| `/view-context` | Shows exactly what was sent to the model last |
| `/new-session` | Starts a fresh conversation |
| `/sessions`, `/resume <id>` | Lists your stored sessions and brings one back |
| `/events`, `/memories` | What Redis Agent Memory stored, and what it learned |
| `/skills` | The team procedure from Redis Agent Playbook |
| `/verify` | Runs the project's tests |

Next: [the amnesiac](02-forgetting.md).
