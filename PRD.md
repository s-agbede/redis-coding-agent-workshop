# PRD: "Build a Coding Agent" — Workshop Teaching Artifact

> Historical planning document. The current 90-minute guided workshop and repair capstone are described in [WORKSHOP.md](WORKSHOP.md) and [FACILITATOR.md](FACILITATOR.md).

> Status: Draft — not yet published to an issue tracker (none configured in this repo).
> Once a tracker is set up (`/setup-matt-pocock-skills`), publish and apply the `ready-for-agent` label.

## Problem Statement

Engineers who have not worked with LLMs experience coding agents (pi, Claude Code, Cursor)
as magic. They can use them, but they have no mental model of *how* they work, which leaves
them unable to reason about, trust, extend, or debug them. Existing agents are the wrong
teaching tool: they are large, feature-rich, and their core mechanism is buried under TUIs,
multi-provider abstractions, session trees, RAG, and extension systems. A learner staring at
pi's or Claude Code's source cannot find the ~50 lines that actually matter.

The facilitator needs to run a **2-hour hands-on workshop** for a room of ~30 LLM-newcomer
engineers and have every one of them leave able to say, honestly: *"I understand the mechanism
behind coding agents now — it's a loop around an LLM with tools. It's fairly simple, actually."*
Nothing off-the-shelf delivers that in 2 hours without drowning beginners in setup friction and
incidental complexity.

## Solution

A **minimal, from-scratch Python coding agent** built as a teaching artifact, delivered as a
**fill-in-the-blank scaffold** that participants complete during the workshop. The design borrows
pi's philosophy — *"primitives, not features"* — but is a fresh, deliberately tiny implementation.

The core insight the artifact makes visible: an agent is two nested loops and one approval gate —
an outer REPL (human turns) wrapping an inner autonomous loop (the model proposes tool calls, the
runtime executes them and feeds results back, repeat until the model stops asking or a cap is hit).

Participants write only the two lines that *are* the lesson (loop termination + tool dispatch/
result-feedback). All incidental machinery — tool implementations, the `rich` pretty-REPL, the
model client wiring, safety gating, and the rehearsal harness — is pre-baked so the room's time and
attention stay on the mechanism. The session culminates in a pinned, verifiable, web-facing
capstone: the agent fetches live FastAPI docs, writes a hello-world API, runs it, and curls it to
prove it responds — demonstrating both that the loop iterates and that a tool extends the model
beyond its training data.

## User Stories

### Workshop participant — understanding the mechanism
1. As a participant, I want to see that an LLM call is stateless and that the whole conversation is resent each turn, so that I stop imagining the model "remembers" on its own.
2. As a participant, I want to see the `messages` array grow turn by turn, so that I understand conversation state is just a list I maintain.
3. As a participant, I want to understand that the model does not execute anything — it only *emits a request* to call a tool — so that I grasp the central mechanism of agents.
4. As a participant, I want to write the loop-termination condition myself, so that I internalize when and why the agent stops.
5. As a participant, I want to write the tool-dispatch step myself, so that I understand how a tool call becomes a real Python function call.
6. As a participant, I want to write the step that feeds a tool result back into `messages`, so that I feel why the loop is a loop.
7. As a participant, I want to walk out able to say "a coding agent is just a loop around an LLM with tools," so that agents stop being magic to me.

### Workshop participant — running and interacting with the agent
8. As a participant, I want to launch the agent with a single command inside a prepared container, so that I spend no time on environment setup.
9. As a participant, I want a REPL prompt where I type a task in natural language, so that interacting feels like a real coding agent.
10. As a participant, I want each tool call printed as a clear, labelled panel as it happens, so that I can watch the loop turn.
11. As a participant, I want a spinner while the model is thinking, so that I know the agent is working and not frozen.
12. As a participant, I want to approve `run_bash` and `web_fetch` calls with a `y/n` prompt, so that I physically enact "the model proposes, I dispose."
13. As a participant, I want `read_file`, `write_file`, and `str_replace` to run without prompting, so that low-risk actions don't bury me in approvals.
14. As a participant, I want the agent's conversation to persist across my REPL turns, so that I can give follow-up instructions ("now add a /health endpoint") and see it operate on state it built.
15. As a participant, I want the agent to stop after a bounded number of iterations, so that a confused model can't spin forever and burn my time.
16. As a participant, I want a clean Python traceback when my loop code has a bug, so that I can find and fix my mistake without fighting a framework.

### Workshop participant — the capstone
17. As a participant, I want to instruct the agent to build a hello-world FastAPI app from the current docs, so that I see an end-to-end agentic task succeed.
18. As a participant, I want the agent to fetch live FastAPI documentation via a tool, so that I understand a tool lets the model use information it wasn't trained on.
19. As a participant, I want the agent to write the app file, launch it, and curl it, so that I see the loop chain multiple tool calls toward a goal.
20. As a participant, I want the capstone to end in a visible, unambiguous success (an HTTP response), so that "it worked" is proven, not asserted.
21. As a participant, I want to then modify the task myself (different library, extra endpoint), so that I can confirm my understanding by breaking and extending it.

### Facilitator / instructor
22. As a facilitator, I want the loop revealed in three runnable checkpoints (chat-only → one tool → all tools + capstone), so that I can pace the room and no one is stranded.
23. As a facilitator, I want a filled-in solution version, so that I can demo, unblock stuck participants, and recover quickly.
24. As a facilitator, I want a rehearsal harness that runs the capstone headless N times and reports a pass rate, so that I can prove the demo is reliable before the workshop.
25. As a facilitator, I want a cached copy of the docs page used by the capstone, so that a live docs change on the day cannot break my demo.
26. As a facilitator, I want a saved transcript from a green rehearsal run, so that I have a fallback if a live run wanders in front of the room.
27. As a facilitator, I want the model provider/endpoint configurable via environment variables, so that I can point every participant at the pre-provisioned keys without code edits.
28. As a facilitator, I want the whole thing to run inside the workshop Docker/uv template, so that `run_bash` is sandboxed and every laptop is identical.
29. As a facilitator, I want a whiteboard-ready mental model (two loops + one gate), so that I can explain the architecture in under two minutes.

### Workshop organizer
30. As an organizer, I want participants to bring nothing but a laptop and the repo, so that onboarding is trivial and predictable across the cohort.
31. As an organizer, I want the artifact to be small enough to read in full, so that motivated participants can study the complete source afterward.
32. As an organizer, I want clearly marked stretch goals (interrupt/steering, a real TUI), so that fast finishers have somewhere to go without derailing the core.

## Implementation Decisions

- **Language / SDK / model.** Python, the OpenAI SDK, targeting GPT-5 for reliable multi-step tool-calling. Provider base URL and API key read from environment variables so the pre-provisioned keys (plain OpenAI, Azure, or a proxy) drop in without code changes.
- **Modules (all new; greenfield).**
  - **Agent core** — owns the two nested loops. Exposes `run_agent(client, messages, tools)`. Contains the two participant blanks: (1) the termination condition (stop when the model returns no tool calls) and (2) the dispatch step that maps a tool call to a Python function and appends the result back into `messages` as a `role:"tool"` message. The iteration cap (start at 10) and `messages.append(assistant_msg)` are pre-baked with explanatory comments.
  - **Tools** — five pre-baked tools plus their JSON schemas and a name→function registry: `read_file`, `write_file` (create/overwrite), `str_replace` (exact find/replace), `run_bash`, `web_fetch`. Participants read but do not write these.
  - **UI / pretty-REPL** — pre-baked `rich`-based linear REPL: a `you ›` prompt, a thinking spinner, one colored panel per tool call, `y/n` approval prompts, optional syntax-highlighted before/after for edits. Strictly linear (no full-screen layout) to preserve legible control flow and clean tracebacks.
  - **Entry point** — pre-baked wiring of the model client + REPL + agent core; holds the short system prompt.
  - **Rehearsal harness** — pre-baked script that runs the pinned capstone headless N times against the real model and prints a pass/fail rate.
  - **Solution** — a filled-in copy of the agent core (branch or folder) for facilitator use and rehearsal.
- **The model client is an injected dependency** of `run_agent` — the real OpenAI client in production, a fake scripted client in tests. This is the single primary test seam.
- **Editing strategy: `str_replace`, not unified diffs.** Chosen for reliability and teachability; it is what production text-editor tools actually use. `str_replace` errors clearly when the target string is missing or not unique — that error is what enables the model to self-correct.
- **Human-in-the-loop gating.** `run_bash` and `web_fetch` are gated behind a `y/n` prompt; `read_file`, `write_file`, `str_replace` auto-run. The gate is both a safety boundary (arbitrary execution / network) and the pedagogical device for "model proposes, runtime disposes."
- **Sandboxing.** The agent runs inside the workshop Docker container (uv-based template); the container is what makes handing `run_bash` to an LLM acceptable.
- **web_fetch safeguards.** Output is truncated (~4–6k chars) to prevent token blowout; a cached copy of the FastAPI quickstart page is shipped as a fallback against day-of docs drift.
- **Loop visibility.** Instrumentation (per-turn tool-call panels) is treated as core pedagogy, not decoration — the loop must be observable as it runs.
- **Interaction model.** Persistent conversational REPL: `messages` accumulates across human turns so follow-up instructions operate on prior state. The inner agent loop runs to completion (or the cap) before returning control to the human — no mid-run interruption.
- **Progressive reveal.** The agent core is delivered in three runnable stages: (1) chat loop, no tools; (2) add `read_file` + write dispatch + termination; (3) unlock all five tools + the capstone.
- **Pinned capstone.** "Fetch the current FastAPI docs, build a hello-world API, run it with uvicorn, and curl it to prove it returns the expected response." Verified via a real HTTP response. Open-ended variants (other libraries/apps) are a post-capstone self-exploration segment.

## Testing Decisions

- **What makes a good test here:** assert external, observable behavior of the loop and tools — never internal wording of prompts or the exact shape of intermediate log lines. Tests must be deterministic and must not call a real model.
- **Primary seam — `run_agent(client, messages, tools)` with a fake scripted client.** Inject a fake model client that returns pre-scripted responses (a sequence of tool calls, then a final no-tool-call message) and assert: tool calls are dispatched to the right functions; each tool result is appended back into `messages` as a `role:"tool"` entry with the correct tool-call id; the loop terminates when the model returns no tool calls; the loop halts at the iteration cap even if the fake client keeps requesting tools.
- **Secondary — tools tested directly** (deterministic, no model): `str_replace` succeeds on a unique match and raises a clear error on missing/ambiguous matches; `write_file`/`read_file` round-trip; `web_fetch` truncates oversized content.
- **Acceptance (not a unit test) — `rehearse.py`** exercises the full stack against the real model to measure capstone pass-rate. It is a reliability gate for the facilitator, run before the workshop; it is explicitly out of the deterministic test suite.
- **Prior art:** none in-repo (greenfield). The fake-client pattern is standard dependency-injection testing; establish it here as the reference pattern for the codebase.

## Out of Scope

- Mid-run interruption / steering (submitting a message while the agent works). Stretch goal only.
- A full-screen terminal UI (TUI). Deliberately excluded; the pretty-REPL is the interface. TUI is named as a stretch goal that layers on top of the loop.
- Multi-provider abstraction, model switching, MCP, sub-agents, plan mode, session trees/branching, RAG, extension/skill/package systems — all pi/Claude-Code features intentionally omitted to keep the core visible.
- Robust unified-diff editing, glob/list-files tools, and any additional tools beyond the five.
- Production concerns: auth, persistence beyond in-memory `messages`, rate-limit/retry hardening, cost controls beyond the iteration cap, security hardening of `run_bash` beyond container isolation.
- Publishing this PRD to an issue tracker (none configured in this repo yet).

## Further Notes

- **The single biggest open risk is rehearsal.** The thesis is "it's simple *and it works*." An unrehearsed live, web-facing demo bets that thesis on a coin flip. Before the workshop, run the pinned FastAPI capstone end-to-end 15–20 times via `rehearse.py`, record the clean-convergence rate, and confirm the cached-transcript fallback works.
- **pi is a philosophical reference only**, not a code reference — the artifact is fresh Python and does not port pi's TypeScript, TUI, RPC, or extension system.
- **Setup de-risking is what makes 2 hours feasible:** pre-provisioned keys + Docker/uv template + fill-in-the-blank scaffold. Do not let a default TUI or bare `pip install` quietly reintroduce setup friction.
- **Whiteboard mental model:** REPL (human turn) → agent loop (autonomous, ≤10 turns: model → tool calls? → [approve?] → run → append result → loop; no tool calls → answer, hand back) → back to REPL.
- **Open input needed from the facilitator:** the exact keys/endpoint configuration (plain OpenAI vs. Azure vs. proxy base URL) to hardcode the correct env-var names in the entry point.
