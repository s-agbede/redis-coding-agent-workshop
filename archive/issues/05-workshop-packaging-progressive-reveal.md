# Slice 5: Workshop packaging — 3-stage reveal + facilitator guide

_Triage label to apply on publish: `ready-for-agent`_

## What to build

Repackage the finished agent into a teachable, paced workshop. Split the agent core into three
runnable checkpoints so no participant is stranded: (1) chat loop, no tools; (2) one tool
(`read_file`) + the two blanks; (3) all tools + the capstone. Each checkpoint runs on its own.

Write the facilitator guide (README): the whiteboard mental model (two nested loops + one approval
gate: REPL human turn → autonomous agent loop, ≤10 turns, model → tool calls? → [approve?] → run →
append → loop; no tool calls → answer → hand back), suggested pacing for a 2-hour session, and the
pre-workshop rehearsal checklist. Mark the stretch goals explicitly (mid-run interruption/steering,
a full-screen TUI) as layers that sit on top of the loop, for fast finishers.

## Acceptance criteria

- [ ] The agent core is delivered as three independently runnable checkpoints (chat-only → one tool → all tools + capstone)
- [ ] Each checkpoint runs and demonstrates its intended concept on its own
- [ ] A facilitator README documents the two-loops-one-gate mental model and 2-hour pacing
- [ ] The README includes the pre-workshop rehearsal checklist (run capstone 15–20×, verify fallbacks)
- [ ] Stretch goals (steering, TUI) are clearly marked as optional layers on top of the loop
- [ ] A participant can complete the full arc — from chat loop to green capstone — following the guide

## Blocked by

- Slice 4 (FastAPI capstone + rehearsal harness)
