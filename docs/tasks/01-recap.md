# Recap: what goes into the request

**3 minutes.** Part 1 built a working coding agent. Today we decide what that agent should *know*.

## What Part 1 covered

An agent is a model plus a harness. You don't build the model; you build the harness around it:

1. **The agent loop:** the model decides to call a tool or answer; your code runs the tool and sends the result back.
2. **Tool design:** small, read-only tools with schemas, capped outputs, and errors returned as data.
3. **Production patterns:** sandboxed paths, a step budget, validated output, and a person approving changes.
4. **Testing agents:** fake-model tests on every commit, task evals on every change.

Part 1 ended here: *within a run, the context window is the agent's memory. Between runs, Redis keeps the state.* That's today.

## Part 1 in one picture

The model never touches your files. It *asks* for a tool, your Python code runs it, and the result goes back in the next request. That loop is `run_agent` in `agent.py:loop`. Every task, the application builds a fresh request from:

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

All of today's code is already in `agent.py`. One function, `handle` (`agent.py:handle`), takes a task from start to finish, and three switches at `agent.py:flags` turn its steps on: `CAPTURE`, `RECALL` and `PLAYBOOK`. They all start off.

The instructor demonstrates each section, then you get **a few minutes**: switch on that section's flag, restart, and read the lines it turned on. Click a file name like `agent.py:capture` in these lessons to open the editor at that line.

After changing `agent.py`: save, type `exit`, and start the agent again.

## Your turn: get ready

In the terminal:

```bash
uv run --group iris python main.py
```

You'll see your owner ID, session ID, and which capabilities are on (all off for now). Type `/` and matching commands appear as you type, with the best match in grey ahead of the cursor: press **→** to accept it, or **Tab** to move through the list. The suggestions come from Redis's autocomplete, and the commands you use most rise to the top. Commands you'll use:

| Command | What it does |
| --- | --- |
| `/view-context` | Shows exactly what was sent to the model last |
| `/new-session` | Starts a fresh conversation |
| `/sessions`, `/resume <number>` | Lists your stored sessions, numbered, and brings one back |
| `/events`, `/memories` | What Redis Agent Memory stored, and what it learned |
| `/forget <id>` | Makes Redis Agent Memory forget one of your memories |
| `/skills` | The team procedure from Redis Agent Playbook |

Next: [the amnesiac](02-forgetting.md).
