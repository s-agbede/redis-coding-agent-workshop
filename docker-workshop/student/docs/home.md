# Build a Coding Agent

Build a small Python harness and give a model useful tools. By the end, your agent will investigate why a task loses its completed status after refresh, repair the application, and check that the repair works. Your instructor guides the session; hints and copyable answers are available throughout.

In the guided workshop, edit and save in Code, then select Run code to run a shell command in the visible Terminal. Use the copy actions for Python answers and prompts. Leave a running chat with `exit` before starting another command. A quick environment check is available if needed:

```bash
uv run python check_setup.py
```

## Workshop

1. [Make your first model call](tasks/01-first-call.md)
2. [Design the agent with PEAS](tasks/02-peas.md)
3. [Keep the conversation](tasks/03-conversation.md)
4. [Give the model a file reader](tasks/04-one-tool.md)
5. [Make the reader useful on larger files](tasks/05-better-tools.md)
6. [Let the agent take several steps](tasks/06-agent-loop.md)
7. [Ask your agent to fix the app](tasks/07-capstone.md)
