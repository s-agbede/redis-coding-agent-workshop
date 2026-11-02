# Workshop implementation and validation

This branch contains one memory and shared-knowledge workshop. Start from the repository root:

```bash
uv run --group iris python main.py
```

## Layout

- `agent.py`: completed coding loop plus four learner memory/context functions, initially disabled.
- `main.py`: configuration and terminal entry point.
- `runtime.py`: context composition, project-bound file tools, session controls and inspections.
- `context.py`, `playbook.py`: typed published procedure and SDK publication/retrieval adapter.
- `project/`: agent-editable report-validator project with sample data.
- `project-review/`: optional second-project demonstration using the same published procedure.
- `challenge/`: independent contract, fixtures and checker.
- `skills/report-validation/`: supplied procedure; students do not author it.
- `solutions/steps/`: cumulative capture, recall and Playbook implementations.
- `docs/tasks/`: canonical lessons; `docs/slides/`: explicit presentation placeholders.

The learner guide is `/guide/` in the workbench, with `/guide/build` for lessons. A standalone development preview uses `/` and `/build`. Old part URLs redirect to this single workshop. There is no second source tree or workshop chooser. Historical task-board materials are archived outside the active learner path.

## State and evidence

Each launch creates a new session. The owner persists in `output/workshop/owner.json`; `--owner` overrides it. `--project` selects agent files; it is not a shell sandbox. File tools enforce the project boundary; shell commands require approval. `/new-session` clears conversation/retrieval/request history and reloads AGENTS.md without erasing external memory. Python edits require save, exit and relaunch.

`/status` reports capabilities, owner/session, configured clients and a suggested next action. It does not contact services or claim that configured connections are healthy. `/view-context` separates current context sources from the latest submitted model request. `/events` reads captured user/final-answer events; `/memories` inspects automatic extraction. The application does not restore a full tool transcript or resume a past session.

`/publish-skill` is an instructor step: it creates and publishes the supplied package and stores a receipt; a changed package becomes the next version of the same entry. Attendees set `PLAYBOOK_SKILL_ID` to that entry, need only read access, and are refused if they try to publish. `/skills` reads the published procedure for inspection; only a normal task with Playbook enabled injects it. `/verify` runs the unchanged checker against the selected project's validator.

## Slides

Presentation UI is retained, but all four decks are brief labelled placeholders. No finished slide designs or diagrams are claimed. Future slides can be authored as Markdown separated by `---`; the existing viewer provides guided, text and focus views. `SLIDES` in `scripts/publish_docs.py` associates decks with lessons. PDF export is not implemented.

Publish after changing lessons or placeholders:

```bash
uv run python scripts/publish_docs.py
uv run python scripts/publish_docs.py --check
```

## Checks and remaining delivery work

Automated tests exercise the real loop with deterministic service responses, context/session isolation, SDK call arguments, publication retry, project file edits and independent validation. Browser tests cover the single workshop and slide controls. Run:

```bash
uv run --group iris pytest -q
npm --prefix docker-workshop/frontend test
npm --prefix docker-workshop/frontend run typecheck
npm --prefix docker-workshop/frontend run build
```

Earlier live experiments verified capture, asynchronous extraction and fresh-session recall against configured Agent Memory. They do not establish current service availability. Live publication previously failed with read-only Playbook keys. Only the instructor now needs a write/publish-capable key; attendee read-only retrieval by `PLAYBOOK_SKILL_ID` and a full rehearsal still need live confirmation. Human timing validation remains necessary for the 90-minute schedule.

Docker uses `.workshop-memory/` to avoid collisions with the older `.workshop/`. The workspace preparer preserves existing student agents and project files. Use a fresh learner workspace for this branch; an older Part 1 workspace may contain an incompatible saved `agent.py`. Back up that attempt before explicitly replacing it with this branch's starter. Never silently replace student work during rebuild.
