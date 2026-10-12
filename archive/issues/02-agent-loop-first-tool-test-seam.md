# Slice 2: Agent loop + first tool (read_file) + the test seam

_Triage label to apply on publish: `ready-for-agent`_

## What to build

Introduce the agent core — `run_agent(client, messages, tools)` — the piece that turns the chat
loop into an agent. This is the workshop's central lesson, delivered as a fill-in-the-blank scaffold
with exactly two participant blanks:

1. **Termination** — stop the loop when the model returns no tool calls.
2. **Dispatch + feedback** — map a tool call to its Python function, run it, and append the result
   back into `messages` as a `role:"tool"` message so the loop continues with the new information.

The model client is an **injected dependency** so the loop can be driven by the real OpenAI client
in production and a fake scripted client in tests. Pre-baked around the blanks: the iteration cap
(start at 10), `messages.append(assistant_msg)` with an explanatory comment, and a per-turn
`rich` panel that prints each tool call as it happens (loop visibility is core pedagogy). One tool
is wired in — `read_file` — plus its JSON schema and a name→function registry. A filled-in solution
copy of the core is included for facilitator use.

Demoable as: "ask the agent to read a file, watch the loop request the tool, run it, and answer."

## Acceptance criteria

- [ ] `run_agent(client, messages, tools)` exists and accepts an injected model client
- [ ] The two participant blanks are clearly marked (termination; dispatch + append result)
- [ ] Asking the agent about a file causes it to call `read_file` and answer using the contents
- [ ] Each tool call is printed as a labelled panel as it occurs
- [ ] The loop halts at the iteration cap (default 10) even if the model keeps requesting tools
- [ ] The loop terminates and hands control back when the model returns no tool calls
- [ ] A filled-in solution version of the core is available
- [ ] Deterministic test: a fake scripted client drives `run_agent` and asserts tools are dispatched, results are appended as `role:"tool"` with the correct tool-call id, the loop stops on no-tool-call, and the cap is honored — with no real API calls

## Blocked by

- Slice 1 (Walking skeleton — rich REPL ↔ GPT-5 chat loop)
