# Workshop Motivation Revision Plan

> For agentic workers: use superpowers:subagent-driven-development or
> superpowers:executing-plans to implement the tasks. Implemented on 2026-10-07;
> Follow-up learner review and targeted revisions completed on 2026-10-07.
> Live lesson and capstone checks passed; a timed human learner pilot remains
> a delivery follow-up before making claims about actual classroom pacing.

**Goal:** Give experienced Python developers a concrete reason to continue,
observable evidence of each new capability, and a few meaningful decisions while
they build their first LLM coding agent in 90 minutes.

**Architecture:** Preserve the seven lessons, scaffolded Python functions,
copyable solutions, live model calls, supplied tools and final evaluators. Revise
the teaching sequence within each lesson and add a small supplied request trace
for the history comparison. Keep the existing frontend and terminal workflow.

**Tech stack:** Python, the existing OpenAI SDK, pytest, Markdown, Vue and the
current Docker workshop. No new dependencies or services are planned.

## Approach and boundaries

Use targeted revisions to the existing experiments. A wording-only pass would
leave the weak observations and limited ownership intact. Rebuilding the entire
workshop around the capstone would increase scope and conflict with the agreed
immediate start. The recommended approach changes the framing, observations and
decisions while retaining the current implementation progression.

Keep the explanations of LLMs, OpenAI, API access, schemas and harness execution
before learners need those concepts. Within an exercise, use this sequence:

**Purpose → brief prediction → run → inspect evidence → explain the gap →
small change → rerun → explain what changed.**

The sequence is a writing guide, not a set of repeated labels or a new worksheet.
Predictions and judgments replace existing discussion questions. They do not add
mandatory notes, forms, quizzes or reflection sections. Keep hints and answers
available. Keep tests in final evaluation. Do not add a completed-agent opening
demo, new domain knowledge, or larger coding tasks.

## Revised timing

| Elapsed | Activity | Minutes |
| --- | --- | --- |
| 0–2 | Welcome and concrete promise | 2 |
| 2–9 | First model call | 7 |
| 9–14 | PEAS applied to the eventual repair | 5 |
| 14–23 | Conversation history with visible request messages | 9 |
| 23–35 | File reader and tool exchange | 12 |
| 35–42 | Design a useful bounded observation | 7 |
| 42–55 | Agent loop and a learner-chosen follow-up | 13 |
| 55–80 | Repair, inspect and independently evaluate | 25 |
| 80–90 | Questions and troubleshooting buffer | 10 |

Environment preparation remains before the workshop. The setup check stays
available for troubleshooting; it is not a new compulsory opening activity.
These are teaching budgets to validate in a timed rehearsal.

## File ownership

Author lesson revisions in these existing files:

- `docs/tasks/01-first-call.md`
- `docs/tasks/02-peas.md`
- `docs/tasks/03-conversation.md`
- `docs/tasks/04-one-tool.md`
- `docs/tasks/05-better-tools.md`
- `docs/tasks/06-agent-loop.md`
- `docs/tasks/07-capstone.md`

Publish the same bodies to `docker-workshop/docs/tasks/`,
`docker-workshop/student/docs/tasks/`, and
`docker-workshop/frontend/public/build-steps/`, preserving front matter and the
existing image-path convention. Update `docker-workshop/frontend/public/welcome.md`,
`WORKSHOP.md`, `FACILITATOR.md` and their existing student counterparts. Preserve
the manifest's seven steps.

The request-preview addition is `request_trace.py`, mirrored into
`docker-workshop/student/`. Integrate it into `first_call.py`,
`checkpoints/stage1_chat.py`, their solutions and student mirrors. Keep all
learner gaps, seeded capstone code and independent acceptance checks intact.
Review also identified that the loop hid tool observations: its command now
enables the existing verbose mode, and `ui.py` prints complete bounded file
results in that mode. This correction has focused regression tests.

## Task 1 Establish the destination and protect the early win

- [x] Add this promise to the welcome: “By the end, your agent will investigate
  why a task loses its completed status after refresh, repair the application,
  and check that the repair works.” Keep the actual reproduction in lesson 7.
- [x] Keep FizzBuzz as the small, familiar first request. Retain the model/API/SDK
  explanation, instructor-provided access and one source-defined prompt.
- [x] End the first run with the next question: “Can your program now handle
  ‘change it to stop at 20’?” Carry that exact question into the history lesson.
- [x] Apply PEAS to the promised refresh ticket, replacing the generic colleague
  scenario. Let pairs propose the four categories before revealing the example.
  Performance explicitly includes a subsequent read or refresh, not an agent's
  report. Keep this discussion to five minutes.

**Acceptance:** A learner can name the final useful outcome before the first
edit. They still make a model call in the opening nine minutes.

## Task 2 Make the history experiment observable

- [x] Add an optional `--show-messages` flag to the first-call and chat runners.
  Wrap the supplied client only when the flag is selected; do not add a new
  learner implementation task or replace the direct SDK call in their function.
- [x] The supplied adapter exposes the existing
  `client.chat.completions.create(...)` interface. Immediately before forwarding
  the call, print its message count, ordered roles and content previews. Use the
  actual `messages` argument, supporting both dictionaries and returned SDK
  message objects. Limit each preview to 600 characters, with an explicit
  “preview shortened; full content sent” marker. Forward all original arguments
  unchanged and return the original response. Do not print credentials, HTTP
  headers or environment configuration; do not save a log.
- [x] First write regression tests in `tests/test_learning_examples.py` for an
  unmodified forwarded request/response, dictionary and SDK messages, an explicit
  shortened-preview marker, ordinary CLI silence, and flag-enabled CLI output.
  Run them against the current code to establish the missing behavior, then add
  the adapter and rerun. Mirror the updated tests into the student distribution.
- [x] Use the flag in the two history commands. Before the first run ask:
  “Will this request contain the previous FizzBuzz code?” Let learners inspect
  the one-message request before explaining the missing history.
- [x] After the small function change, repeat the same two-turn conversation.
  Inspect `user → assistant → user` on the second request. Explain that the
  request evidence remains valid even if the earlier model guessed correctly.
  Keep the existing retained-history and fresh-session behavior tests.

**Acceptance:** The learner can see the actual difference between the requests,
and distinguish missing input from an incorrect model answer. The main path
continues to use live model calls; test doubles remain inside tests.

## Task 3 Give the reader lessons a consequential question

- [x] In lesson 4, keep the explanation of schema, Python execution and returned
  evidence. Ask “What can the model actually know about this local file?” before
  the first attempt. After enabling the reader, use the existing pause to predict
  which function will execute, then inspect the matching request/result IDs.
- [x] Keep the plain reader exercise small. End by connecting its observation
  to project investigation: the agent can now obtain evidence it was not sent in
  the initial prompt.
- [x] In lesson 5, first run the existing plain-reader example. Let learners see
  the 200-line result and its character count. Name the observed problem honestly:
  unnecessary output and poor navigation, even when the answer is correct.
- [x] Before revealing the improved contract, ask: “If we send only part of the
  file, what must the result include so the agent can locate it and continue?”
  Reveal the chosen contract: selected text, line numbers and continuation.
- [x] Keep the existing helper and small function edit. Compare the same question
  before and after range selection. Inspect the model's actual requested range,
  returned content and output size. Keep character counts distinct from tokens.
  Do not claim the prompt forces the model's arguments.
- [x] Replace the whole-file recall question with a decision: “Is this excerpt
  enough evidence for our question, or would you request another page?” Explain
  why a bounded result must reveal omissions. Treat continuation and description
  variations as optional material outside the seven-minute core.

**Acceptance:** Learners encounter an observable tool-design problem and improve
the tool after identifying it. The lesson works without requiring a model error
or pretending that 200 lines necessarily exceed the model's context window.

## Task 4 Add ownership without increasing implementation scope

- [x] In lesson 6, run the reference-following task before explaining the missing
  repetition. Ask learners to identify any requested read that has no returned
  result. Use the existing trace; do not script a provider response.
- [x] Keep stopping, dispatch and feedback as the three implementation gaps.
  Show where the supplied editing and command tools join the same registry and
  explain the existing command-approval boundary before the repair task.
- [x] After the working loop, replace the recall-only closing question with a
  one-minute learner-chosen follow-up: change the question about the supplied
  project/release files, predict the observations needed, and inspect whether the
  actual reads support the answer. Do not require a particular tool-call order.
  The fallback question asks whether the files actually establish that acceptance
  checks passed, rather than merely recording a condition for release. Its reveal
  distinguishes that condition from missing check results. The working loop runs
  immediately after the edits; supplied controls follow as repair preparation.

**Acceptance:** Every learner has a low-pressure opportunity to choose a question
and judge its evidence. A working answer is assessed by observations, not by a
prescribed transcript or a new written submission.

## Task 5 Make the repair a learner decision and an earned finish

- [x] Preserve the existing ticket, supplied prompt, command approvals, hints,
  source repair and independent verifier. Allow 25 minutes for the full task.
- [x] After reproducing the bug, ask for a brief hypothesis: “Did the update fail,
  or did the later read lose the update?” Let the agent investigate; the learner
  can revise their hypothesis from evidence.
- [x] Before accepting a successful run, ask: “Which change explains why
  completion now survives refresh?” Have learners inspect the changed handler
  in Code and explain its relation to the later read. Keep the answer available
  behind the existing repair reveal.
- [x] Run the supplied tool, harness and application checks, then verify the
  refresh behavior with a fresh task. Retain the distinction between a server
  restart and a browser refresh, and between one successful trial and reliability.
- [x] Finish with one sentence connecting the achievement to the work:
  “Your request, history, tool execution and feedback loop enabled this repair;
  the independent checks established what worked.” No separate reflection task.
- [x] If time is short, omit optional description/continuation experiments and
  shorten discussion. Preserve the independent application check and final
  browser verification. Use the existing hints or catch-up files when necessary.

**Acceptance:** The learner can connect the code change to the repaired behavior
and identify the evidence needed to accept the result.

## Task 6 Publish and validate the complete learner journey

- [x] Trim repeated save/restart instructions to a shared short reminder and
  local exceptions. Retain immediate instructions where a running chat must end
  before a shell command. Keep Python explanations appropriate for experienced
  developers; retain explanations of unfamiliar SDK and tool-call structure.
- [x] Synchronize the published lesson bodies, solutions, new trace helper and
  instructor timing. Update the published-answer replay if snippets change.
- [x] Run focused checks with `uv run pytest tests/test_learning_examples.py
  tests/test_learning_progression.py tests/test_workshop_docs.py -q`. Run the
  complete Python suite in a disposable solved copy, preserving the real starter
  gaps and capstone seed. Do not treat expected starter failures as regressions.
- [x] From `docker-workshop/frontend`, run `npm test`, `npm run typecheck` and
  `npm run build`. Browser-check the revised pages, closed reveals, readable
  diagrams, Run code and the trace output. Confirm source/served equality after
  publishing the revised assets; preserve learner files and environment settings.
- [x] Rehearse the revised path with live access in a disposable student workspace.
  Confirm actual request traces, tool results and the app repair; record failures
  rather than substituting scripted learner replies. If access is unavailable,
  mark the live rehearsal pending rather than claiming it passed.
- [ ] Run a timed pilot with a representative Python developer before calling the
  pacing or motivational effect validated. Observe whether they can state the
  destination, predict a missing input, explain the reader contract, choose one
  follow-up and justify accepting the repair. Note where they lose momentum or
  need rescue; do not add evidence forms to the learner UI.
- [x] Record technical checks, actual elapsed times and remaining uncertainties
  in `docker-workshop/VALIDATION.md`. Distinguish automated correctness from
  learner understanding and motivation. No Git commit is planned because this
  workspace currently has no Git metadata.

## Execution order

Set the story and timings first. Implement and test the small request trace next,
then revise the reader, loop and capstone activities. Publish mirrors and validate
the whole sequence last. If subagents are used, give one ownership of request
tracing and its tests, and another ownership of lesson prose; integrate once
their command and trace contracts agree.

## Validation status

The final completed disposable copy passed 138 Python tests; the frontend passed 80
tests, strict TypeScript checks and its production build; the workbench passed
16 tests. The runtime passed 38 focused tracing/display tests. Browser checks
covered the revised welcome, predictions, design reveal, follow-up and repair
judgment. The full Python suite, frontend checks and workbench checks were rerun
after the follow-up revisions. An independent agent reviewing as a learner found
no remaining must-fix pedagogical blocker and accepted the clarity and value.

The root project's existing configuration supports live requests. With the
user's explicit approval, GPT-5 demonstrated the first call, history comparison,
plain and bounded reading, pending reference read, complete loop and evidence
judgment. The Docker runtime was reconnected to that existing configuration and
its completed first-call example also succeeded; command approvals remain on.

Live verification found and corrected three concrete defects: punctuation joined
the rehearsal command's final `.` into `..`; rehearsal used a ten-step budget
instead of the interactive default of 25; and `list_files("")` incorrectly returned
no files. Regression tests were observed failing before each fix. The corrected
live repair then took 12 model turns and passed all nine independent checks.
Browser checks confirmed completion and reopening both survive refresh. A timed
human learner pilot cannot be inferred from these technical checks or the
simulated learner review; it is required before claiming validated class pacing.
