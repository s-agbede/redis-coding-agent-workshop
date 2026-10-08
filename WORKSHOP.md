# Workshop: Build a Coding Agent From First Principles

An instructor-guided workshop for experienced Python developers at Bank of America who are new to LLM applications. Learners build a small harness, add useful observations and actions, then ask their agent to repair a supplied FastAPI task board.

## Schedule

| Elapsed time | Activity | Minutes |
| --- | --- | --- |
| 0–2 | Welcome and concrete repair promise | 2 |
| 2–9 | Model and agent; first FizzBuzz request | 7 |
| 9–14 | Apply PEAS to the eventual repair | 5 |
| 14–23 | Retain conversation history; inspect actual request messages | 9 |
| 23–35 | Implement a plain reader; follow one tool exchange | 12 |
| 35–42 | Design a useful bounded observation | 7 |
| 42–55 | Complete the agent loop; choose a follow-up | 13 |
| 55–80 | Repair the task board, inspect the change and evaluate | 25 |
| 80–90 | Questions, catch-up and troubleshooting buffer | 10 |

Prepare service access and the Docker environment before the session. The setup check remains available when needed. These timings are a facilitation plan; validate them with a timed rehearsal.

## Design of the learning path

The welcome names the destination: investigate why task completion is lost after refresh, repair the application and check the result. Learners start building immediately with FizzBuzz and one SDK request. The first lesson explains LLMs, the OpenAI GPT model, API and Python SDK before code. It uses a compact flow diagram and one source-defined FizzBuzz prompt. API access is provided by the instructor; learners then distinguish the model from the growing harness. PEAS applies success criteria, environment, actions and observations to the promised repair.

Learners predict what a follow-up request contains, then use `--show-messages` to inspect its actual message count, roles and content previews. They compare the same follow-up after implementing retention, even if the earlier model guessed correctly. A local-file question then exposes the need for observations. The file lesson explains schema, function and result before learners implement a plain reader. A small fictional release brief gives the answer a checkable local source.

The larger-file exercise reveals unnecessary output and weak navigation. Before seeing our answer, learners decide what a shorter observation must preserve. They improve the reader using the supplied helper and compare the actual results. The core takes seven minutes; continuation and description experiments are spare-time options. Neither a wrong model answer nor context-window exhaustion is required to establish the tool-design problem.

The loop lesson begins with a reference-following task and inspection of any unanswered tool request. Small function gaps join the pieces, followed immediately by a working run. The loop command enables the supplied verbose display so learners can inspect the actual tool results. Learners then choose a follow-up question and judge whether the observations support its answer; the example distinguishes a release condition from evidence that checks passed. Existing conversation evidence can be reused; there is no prescribed tool-call count. Supplied editing, command execution, error reporting and approval helpers are introduced afterward as preparation for the repair.

The final task gives the repair ticket 25 minutes. Learners reproduce the bug, propose a cause and ask their own agent to investigate. Before accepting the result, they inspect the code change and explain why it affects the later read. Independent checks and a fresh browser task establish the outcome.

## What learners implement

- One SDK call in `first_call.py`.
- Conversation retention in `checkpoints/stage1_chat.py`.
- A plain reader, then a bounded reader in `tools.py`.
- Stopping, tool dispatch and feedback in `agent.py`.

The UI, schemas, remaining tools, approval prompts, bounded-output helper and evaluator are supplied. Prepared model clients stay inside deterministic tests; the guided exercises make live model calls. Learners need not build an evaluation framework. Full solutions are available for catching up, and the seeded application bug stays in distributed starters.

Every coding lesson gives enough context to predict, run and inspect a concrete result before explaining the gap and making a small change. It names the file and function and offers a hint and copyable answer. The welcome explains save/restart/run; local reminders cover transitions between a chat and shell commands. Shell blocks have Run code, Python answers have Copy code, and prompts have Copy text. Learners read actual command output; dispatch alone does not establish success. Discussion questions have revealable support. There are no required notes files, evidence forms or separate reflection phase.

The optional request preview is supplied scaffolding. It forwards the original request unchanged and prints only message roles and content, shortening long previews explicitly. It is not a model reply or an additional learner implementation task.

## Evaluation

Unit checks are introduced in the final evaluation, alongside the application checks. Distinguish three layers: tool tests check functions on real inputs; harness tests use prepared model replies to check message handling and control flow; independent application checks exercise observable outcomes. A live agent attempt adds information about model behavior that deterministic tests cannot establish.

The target app stores tasks in process memory. Completion must survive a later request and browser refresh while the same server runs. Persistence across server restarts is outside this exercise. The unchanged checker covers the repair and existing behaviors, including reopening and deleting tasks.

PEAS's Performance category is realized by those independent checks; Environment is the local project and runtime; Actuators are editing and execution; Sensors are file contents and action results.

## Sources and follow-on topics

- [Designing AI agents from the outside in](https://samuelagbede.com/posts/designing-ai-agents-from-the-outside-in/) grounds the PEAS design discussion.
- [OpenAI Chat Completions](https://developers.openai.com/api/reference/chat-completions/overview) explains the message-list request interface.
- [OpenAI tool calling](https://developers.openai.com/api/docs/guides/function-calling#how-it-works) grounds the schema, requested action, application execution and matching-result flow.
- [From chat to agent](https://vercel.com/academy/build-ai-agent-harness/from-chat-to-agent) supports the progression from message exchange to a tool-using harness.
- [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) informs the distinction between agent behavior, outcome checks and evaluation evidence.

Durable memory, advanced context management, production isolation and multiple agents are follow-on topics. Historical research and design notes remain under `docs/research/` and `docs/superpowers/`; they describe earlier iterations and do not replace this workshop path.
