# Slice 3: Full tool set + human-in-the-loop gating

_Triage label to apply on publish: `ready-for-agent`_

## What to build

Complete the tool set and add the approval gate. Add the remaining four pre-baked tools with their
JSON schemas and registry entries: `write_file` (create/overwrite), `str_replace` (exact
find/replace), `run_bash`, and `web_fetch` (with output truncated to ~4–6k chars to prevent token
blowout). `str_replace` must raise a clear error when the target string is missing or not unique —
that error is what lets the model self-correct.

Add human-in-the-loop gating in the REPL: `run_bash` and `web_fetch` require a `y/n` approval before
they run; `read_file`, `write_file`, and `str_replace` auto-run. The gate is both the safety
boundary (arbitrary execution / network) and the pedagogical device for "the model only proposes;
the runtime disposes." `run_bash` executes inside the workshop container, which is what makes handing
execution to the model acceptable.

Demoable as: "ask the agent to edit a file and run a command, approving the risky steps as they come."

## Acceptance criteria

- [ ] `write_file`, `str_replace`, `run_bash`, and `web_fetch` are available with schemas + registry entries
- [ ] `str_replace` succeeds on a unique match and raises a clear error on missing/ambiguous matches
- [ ] `web_fetch` truncates oversized content to the configured limit
- [ ] `run_bash` and `web_fetch` prompt for `y/n` approval before executing; declining skips the call
- [ ] `read_file`, `write_file`, `str_replace` run without prompting
- [ ] The agent can complete an edit-a-file-then-run-a-command task end-to-end with approvals
- [ ] Direct tool tests cover str_replace (unique / missing / ambiguous), web_fetch truncation, and file round-trip

## Blocked by

- Slice 2 (Agent loop + first tool + the test seam)
