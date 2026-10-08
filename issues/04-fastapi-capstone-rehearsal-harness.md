# Slice 4: FastAPI capstone + rehearsal harness

_Triage label to apply on publish: `ready-for-agent`_

## What to build

The pinned, verifiable capstone that ties everything together, plus the reliability tooling that
makes it safe to run live. The capstone task: the agent fetches the current FastAPI documentation
via `web_fetch`, writes a hello-world API, launches it with uvicorn via `run_bash`, and curls it to
prove it returns the expected response — a visible, unambiguous success. This exercises the full
loop across multiple tool calls and demonstrates that a tool lets the model use information it was
not trained on.

Ship the facilitator's reliability tooling: `rehearse.py` runs the capstone headless N times against
the real model and prints a clean-convergence pass rate; a **cached copy of the FastAPI docs page**
serves as a fallback against day-of docs drift; and a **saved transcript from a green rehearsal run**
serves as the fallback if a live run wanders. Participants can then modify the task (different
library, extra endpoint) as post-capstone self-exploration.

## Acceptance criteria

- [ ] Instructing the agent to build the FastAPI hello-world app drives fetch → write → run → curl end-to-end
- [ ] The capstone ends in a visible HTTP response proving the app works (not merely asserted)
- [ ] A follow-up instruction (e.g., add a `/health` endpoint) operates on the app the agent just built
- [ ] `rehearse.py` runs the capstone headless N times and reports a pass/fail rate
- [ ] A cached FastAPI docs page is available and used as a fallback when the live fetch is unavailable
- [ ] A saved transcript from a green run is included as a live-demo fallback
- [ ] `rehearse.py` is documented as an acceptance/reliability gate, separate from the deterministic test suite

## Blocked by

- Slice 3 (Full tool set + human-in-the-loop gating)
