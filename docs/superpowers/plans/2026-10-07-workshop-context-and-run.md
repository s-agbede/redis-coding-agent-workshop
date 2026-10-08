# Workshop context and Run code implementation plan

> Use subagents with separate file ownership; review and integrate in this chat.

**Goal:** Apply the user's October 7 feedback: explain LLM/API/tool concepts before
implementation, make live exercise execution the main path, and run shell blocks
in the visible terminal with one click.

**Architecture:** Keep Vue lessons, the existing workbench and FastAPI backend.
Use the existing shared tmux session for terminal execution. Shell blocks get a
Run code action; Python answers and protocol examples remain copyable. Commands
must be refused when the terminal is busy, and failed dispatch must be visible.
No new frameworks, dependencies or datastore. Preserve learner blanks.

- [x] Python: remove the first-call scripted CLI path; run its single default
  FizzBuzz prompt with `uv run python first_call.py`. Keep fakes in tests.
  Simplify live checkpoint defaults and document their exact command contracts.
  Update behavior tests before implementation and replay tests as needed.
- [x] Lessons: explain LLMs, OpenAI, SDK/API/access and tool purpose before code.
  Explain the release fixture as a file-evidence experiment. Add small SVG flow
  diagrams and paragraph spacing. Remove offline runs from active lessons and
  move exercise test commands to final evaluation. Mirror task docs and maintain
  the 90-minute budget. Keep exact published solution snippets consistent.
- [x] Backend/workbench: test and implement typed command dispatch to the existing
  tmux pane, with same-origin protection, bounded input, errors and busy refusal.
  Reveal Terminal without recreating its iframe or hiding Instructions.
- [x] Frontend: test language-aware Run/Copy actions and success/failure handling.
  POST the displayed shell command, reveal Terminal, and report dispatched status
  without claiming the process succeeded. Keep source-code copying available.
- [x] Integration: run frontend/type/build, backend/workbench and Python regression
  checks. Deploy the changed services preserving student files and configuration.
  Browser-test real execution, busy rejection and revised lesson readability.
- [x] Review changes independently and record verification/remaining limitations.

The user's feedback authorizes these revisions to the approved workshop design.
No Git metadata is present; do not create a repository or invent commits.
