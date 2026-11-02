# Iris memory feasibility experiment

This experiment uses the completed agent loop from `solutions/agent.py` and the
official `redis-agent-memory` Python SDK. The learner starter is unchanged.

Implementation sequence: test capture and scoped recall; implement SDK integration;
run a live teaching session; inspect automatic extraction; run a fresh recall session.

## Workshop materials

- [Part 2 curriculum](../WORKSHOP.md): current seven-lesson authoring package following Part 1.

- [Part 2 story arc](STORY.md): evolving narrative and architecture diagram placeholders.

- [Earlier experiment walkthrough](WORKSHOP.md): a 25-minute capture, inspect and recall lab; the Part 2 curriculum supersedes this as the teaching design.
- [Instructor notes](FACILITATOR.md): preparation, recorded fallback and correction limitations.

## Run

Configure `AGENT_MEMORY_URL`, `AGENT_MEMORY_STORE_ID`, and
`AGENT_MEMORY_API_KEY` in the root `.env`, alongside the existing model settings.
Use a unique synthetic owner for each experiment. Owner IDs and filters demonstrate
selection, not authenticated user isolation; this CLI is an instructor experiment.

```sh
uv run --group iris python -m experiments.iris_memory teach --owner YOUR_TEST_OWNER --session YOUR_TEACH_SESSION
uv run --group iris python -m experiments.iris_memory inspect --owner YOUR_TEST_OWNER --session YOUR_TEACH_SESSION
uv run --group iris python -m experiments.iris_memory recall --owner YOUR_TEST_OWNER --prompt 'How should I initialise a new Python project and manage dependencies?'
uv run --group iris pytest tests/test_iris_memory.py -q
```

Inspect again after the service extraction interval if results are empty. Recall
fails explicitly if no custom preferences are found; it never substitutes seeded
long-term memories. Every invocation exits after one operation; there is no
unbounded polling. Inspect reads session events and separately searches long-term
memory filtered by owner and `user_preference`.

The experiment sends the original user text and actual assistant answer, in order,
without truncation. It uses text-only turns through the completed loop: no file
contents, system prompt, tool results, or tool-call messages are submitted. It does
not yet demonstrate tool-enabled conversations or different agent implementations.
The learner's AGENTS.md loading is unchanged; this isolated text experiment does
not load project instructions. Only service-side extraction creates long-term memories.

Each successful command saves its prompts, answers, retrieved memories, and
server-returned session payload under ignored `output/iris-memory/`. Use synthetic
content: these reports intentionally contain the full experiment conversation.
No credentials are included. Live extraction and model adherence are evaluated
separately from the deterministic integration tests.

## Instructor extensions

After basic recall succeeds, submit a project-specific exception and then an
explicit correction with `teach --prompt`. Inspect actual extracted records before
claiming conflicts are resolved. Test an unrelated owner separately. Do not treat
retrieval filtering as an authorization mechanism.
