# Workshop environment

The instructor prepares the Docker environment before the session. The browser editor and embedded Terminal share the learner workspace.

Run this quick check in Terminal:

```bash
uv run python check_setup.py
```

It checks local dependencies and configuration presence, without contacting the model service. Save code changes before running a command. Type `exit` to leave a chat or use Ctrl+C to interrupt it, then rerun the lesson command to load saved changes.

Start with [Make your first model call](../tasks/01-first-call.md). Deployment details live in the repository's `docker-workshop/README.md` and `FACILITATOR.md`.
