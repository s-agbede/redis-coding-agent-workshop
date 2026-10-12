---
title: Build a Coding Agent
subtitle: From a first model call to an agent that repairs a Python app.
estimatedMinutes: 90
description: Build an agent that investigates why a task loses its completed status after refresh, repairs the app, and checks the result.
---

Your instructor will guide you through six connected lessons. You will:

- Explain how a model and its harness work together.
- Use a short PEAS discussion to decide what evidence and actions your agent needs.
- Build conversation history, useful tools and a working agent loop.
- Ask your agent to repair a Python app, then use supplied evaluation checks to assess the result.

Edit and save in **Code**, then select **Run code** on a command to run it in the visible **Terminal**. Use **Copy code** for Python answers and **Copy text** for prompts to paste into a running chat. Try each small function yourself; open a hint or copyable answer whenever it helps. Short questions are for discussion, with answers on the page.

Your request, history, loop and reader live in **agent.py**. Each edit changes what this same program can do. Start it with `uv run python main.py`; type questions into the running chat.

After changing code, save, leave any running chat with `exit`, and run the command again. This loads your changes and starts a fresh conversation. Press **Ctrl+C** to interrupt when needed.

If you need a quick environment check:

```bash
uv run python check_setup.py
```

Start with **Make your first model call**.
