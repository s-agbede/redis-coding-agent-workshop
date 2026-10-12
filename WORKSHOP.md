# Workshop: Build a Coding Agent From First Principles

A 90-minute guided workshop for experienced Python developers at Bank of America who are new to LLM applications. One learner-facing **agent.py** grows into the agent that investigates and repairs a supplied FastAPI task board. Start it throughout with `uv run python main.py`.

## Schedule

| Elapsed | Activity | Minutes |
| --- | --- | --- |
| 0–2 | Welcome and concrete repair promise | 2 |
| 2–11 | LLM, OpenAI API and SDK; implement the model request | 9 |
| 11–20 | Observe missing history; retain it and repeat the follow-up | 9 |
| 20–35 | PEAS/tool design; build dispatch, feedback and repetition | 15 |
| 35–45 | Fix the missing reader; compare evidence with its earlier error | 10 |
| 45–55 | Improve bounded output and advertise paging arguments | 10 |
| 55–80 | Add supplied actions; repair and independently evaluate the app | 25 |
| 80–90 | Questions, catch-up and troubleshooting buffer | 10 |

Prepare API access and independent learner runtimes before the session. These timings require a timed human rehearsal; automated replay does not validate pacing.

## One evolving program

Learners edit `ask`, `remember`, `run_agent` and `read_file`, plus explicit `TOOL_SCHEMAS` and `REGISTRY` assignments. The initial program has one request and deliberately forgets earlier exchanges. Later TODOs do not block that request. The tool lesson advertises discovery and an unfinished reader, then replaces the one-call function with the learner's own bounded loop. The reader error becomes feedback rather than a hidden completed fallback.

`main.py` imports the functions and tool assignments from `agent.py` and supplies client setup, interactive input and project selection. `tools.py` supplies schemas, bounded output formatting and other actions. `ui.py` displays request/result/answer panels and asks for command approval. Request summaries show count and roles; full message previews are optional. Those files support the learner file without requiring a giant monolith.

The question stays natural: “What's the latest release decision?” Project context names the evidence directory; the model discovers filenames and chooses subsequent reads. No prompt dictates offsets, and no code introspects the learner function to switch stages. When paging is implemented, the learner explicitly advertises the schema that accepts its new arguments.

Each coding lesson follows observe → predict → edit → rerun → inspect the change. PEAS is a short discussion attached to tools and evaluation, not a separate non-coding lesson. Model outputs are not prescribed: a guess without evidence becomes a question to investigate, not proof the demo succeeded.

## Meaningful final task

Register supplied editing and command tools in the same file, then start `uv run python main.py --project capstone`. The argument selects the project; it does not select an implementation. Reproduce the lost-completion bug, propose a cause, let the accumulated agent investigate, inspect the diff and explain why the later read changes. Run the independent verifier and check a fresh browser task.

Shell commands require approval. Editing tools act directly on the selected disposable project. Project selection is a convenience, not isolation. A denied command is feedback; it never establishes a check passed.

The app stores tasks in memory. Completion must survive a later request and browser refresh in the same process. Persistence across server restarts is outside the ticket. The unchanged acceptance checker covers the repair and existing behaviors, including reopening and deleting tasks.

## Evaluation and catch-up

Unit checks appear in the final evaluation: real-file tool tests, prepared-reply harness tests, then independent HTTP application checks. The deterministic replay applies the published snippets and cumulative catch-up files in disposable workspaces created from the maintained starter and runs the actual agent CLI with test-only provider transport. It validates plumbing, not live model choices or learner motivation.

Each lesson includes copyable function answers and an explicit cumulative file in `solutions/steps/`. Learners preserve their attempt before copying one. `solutions/agent.py` is the complete reference. No solution is automatically loaded by the normal learner program. The generated learner workspace starts with the seeded application bug.

See [FACILITATOR.md](FACILITATOR.md) for preparation and the opening demo. Historical research remains in `archive/`; the learner workspace contains only the current exercises.

## Sources

- [OpenAI Chat Completions](https://developers.openai.com/api/reference/chat-completions/overview) and [tool calling](https://developers.openai.com/api/docs/guides/function-calling#how-it-works).
- [Vercel: From chat to agent](https://vercel.com/academy/build-ai-agent-harness/from-chat-to-agent): evolve the same program as limitations motivate capabilities.
- [Designing agents from the outside in](https://samuelagbede.com/posts/designing-ai-agents-from-the-outside-in/): PEAS design discussion.
- [Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents): separate behavior, outcome and evaluation evidence.
