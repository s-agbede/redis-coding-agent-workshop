---
title: Give a coding agent useful memory
subtitle: Part 2 · Redis Agent Memory and Redis Agent Playbook
---
# Give a coding agent useful memory

A 90-minute workshop and Part 2 of the coding agent series. Part 1 built a working agent; the recap covers what you need if you missed it.

Today's question: **what should a coding agent know, where does that knowledge come from, and who owns it?** You'll watch a preference disappear, save a project convention to a file, let **Redis Agent Memory** learn your preference and bring it back in a new session, then have the agent follow a team procedure from **Redis Agent Playbook** and check its work with the tests.

Each section is a short demo followed by **five minutes for you**. All the code is already in `agent.py`: each section switches on one flag, and you read the lines it turns on.

Start the agent in the terminal:

```bash
uv run --group iris python main.py
```

Then type a task, or `/help` for commands. After changing `agent.py`: save, type `exit`, start it again.

Start with the [recap](/build?lesson=01-recap.md).
