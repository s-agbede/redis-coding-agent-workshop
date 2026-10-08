# Slice 1: Walking skeleton — rich REPL ↔ GPT-5 chat loop

_Triage label to apply on publish: `ready-for-agent`_

## What to build

The thinnest end-to-end path that runs: a `rich`-based pretty-REPL that reads a natural-language
prompt from the user, calls GPT-5 through the OpenAI SDK, shows a thinking spinner while the request
is in flight, prints the model's reply, and returns to the prompt. Conversation state (`messages`)
persists across turns so the session behaves like a real chat. The model client is configured
entirely from environment variables (base URL, API key, model) so pre-provisioned keys drop in with
no code edits. **No tools yet** — this slice establishes the loop shell and the "an LLM call is
stateless; I resend the whole conversation each turn" intuition.

## Acceptance criteria

- [ ] Running the entry command inside the container drops the user into a `you ›` REPL prompt
- [ ] Typing a message calls GPT-5 and prints the assistant reply in the console
- [ ] A spinner/status indicator is shown while the model is thinking
- [ ] `messages` accumulates across turns (a follow-up references earlier context correctly)
- [ ] Model provider base URL, API key, and model name are read from environment variables
- [ ] `exit` (or equivalent) cleanly leaves the REPL
- [ ] A bug in the loop surfaces as a clean Python traceback (no framework swallowing it)

## Blocked by

- None — can start immediately
