# Give a coding agent useful memory

A 90-minute workshop and Part 2 of the coding agent series. Part 1 built a working agent; the recap covers what you need if you missed it.

Today's question: **what should a coding agent know, where does that knowledge come from, and who owns it?** You will watch a preference disappear, persist a project instruction in a file, let **Redis Agent Memory** learn a preference from your work and recall it in a fresh session, then retrieve a team procedure from **Redis Agent Playbook** and check the validator the agent writes.

Each section is a short instructor demo followed by **five minutes for you**. Your turn copies a ready-made `agent.py` from `solutions/steps/`; the code is there to read, not to type.

**You edit `agent.py`; the agent edits `project/`.** Start the agent in the shell terminal from the repository root:

```bash
uv run --group iris python main.py
```

At the `You >` prompt, type `/status`, or `/help` for all commands. Shell commands go in the shell; tasks and slash commands go at `You >`. After changing `agent.py`: save, type `exit`, relaunch.

Your instructor provides the model and service connections. All data is synthetic.

Start with the [recap](tasks/01-recap.md).
