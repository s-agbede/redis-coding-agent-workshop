# Part 2 story arc

A 90-minute follow-on to building a coding agent. Start with the completed Part 1
assistant and extend it through small data-validation tasks. The central promise is: extend your coding agent so it can recall a developer's
preferences and retrieve a published team procedure, then verify the resulting code.
The existing WORKSHOP.md is an earlier experiment walkthrough; it will be reshaped
around this arc. This document is a proposed teaching design, not a claim that
the session commands or Playbook integration have already been implemented.


## Audience and success criteria

Participants completed Part 1 or start with its supplied completed agent. They can
read Python and understand the model/tool feedback loop. Redis expertise is not
assumed. The instructor provisions services, keys, Python dependencies and isolated
learner workspaces before the session; account setup is not a timed learner activity.

By the end, a participant can:

- Identify which context survives a new session and explain why.
- Implement SDK event capture and scoped preference retrieval in the same agent.
- Distinguish recorded events, extracted memories, retrieved context and behaviour.
- Publish a supplied skill and inspect the published procedure retrieved for a task.
- Verify a small generated validator independently of the agent's success claim.

## Proposed 90-minute schedule

| Time | Activity | Learner action and evidence |
| --- | --- | --- |
| 0–5 | What we learned in Part 1 | Reconstruct the completed agent and identify its current context sources |
| 5–13 | Persistent project instructions | Edit AGENTS.md; start a new session; inspect reloaded instructions |
| 13–20 | A conversational preference disappears | State the comment preference; generate filename validation; inspect before/after a new session |
| 20–35 | Capture and extract | Implement event capture; inspect original events and automatic extraction |
| 35–50 | Retrieve and use | Implement scoped retrieval/context injection; use column validation to inspect fresh-session recall |
| 50–65 | Skills and Agent Playbook | Inspect and publish the supplied skill; retrieve its published procedure |
| 65–80 | Apply and verify | Generate the report validator; inspect context, code and independent test results |
| 80–90 | Catch-up and discussion | Explain the three context sources; discuss limitations and applications |

These are rehearsal targets, not validated timings. Keep the final verification and
10-minute buffer protected. Playbook provisioning and publishing latency must be
validated before committing to the 15-minute lesson.

## Opening overview — What we learned in Part 1

Start with the completed agent, before introducing any new product or capability.
Ask learners to reconstruct the path from their request to a verified result.

Recap the capabilities they built:

1. Make a model request through the Python SDK.
2. Keep user and assistant messages in a conversation list and resend that context.
3. Describe tools, execute requested calls and return results through the agent loop.
4. Read project files and bound output with paging.
5. Use editing and command tools to repair an application.
6. Inspect the change and verify it with independent checks.

Connect those capabilities to the supplied harness: project instructions are loaded
from AGENTS.md, command execution has an approval step, and request/tool displays
make the flow inspectable. Distinguish what learners implemented from supplied wiring.

Ask: “What does our agent already know when the next request arrives, and where did
that context come from?” Point to the current message list and loaded instructions.
Then introduce the Part 2 question: “Which of this context survives a new session,
and how can we bring useful preferences and team procedures into future tasks?”

**Image placeholder A — Part 1 learning journey:** a compact sequence of six labelled
steps: model call → conversation → tools and loop → reading and paging → repair →
independent verification. Use the workshop's existing visual style; distinguish
verification from the model's claim of success. Place this beside the opening recap.

**Image placeholder B — The completed Part 1 agent:** the existing architecture
with user/terminal, harness, current context, model, tool registry, execution and
returned results. Show AGENTS.md feeding the context and a separate independent
verification path. Highlight the message list when transitioning into memory.
This is the base image for the progressive diagrams below, not a second competing
architecture. Place it immediately after the learning journey.

## 1. We already have conversation memory

Revisit the list of user, assistant and tool messages from Part 1. The harness
appends messages and sends the history with each request. The list supplies
short-term context within the running session.

Use one consistent architecture diagram that gains components at each stage; keep
names, positions and colours stable so learners can identify what changed.

**Diagram placeholder 1 — Conversation-memory overlay on Image B:** user → terminal/harness → message
list → model; model tool requests → tool execution → results appended to the list.
Mark the list as process-local and show the next model request reusing it.

## 2. Some instructions already survive a new session

Learners edit AGENTS.md to add “Use uv for Python projects.” The harness reloads
project instructions when starting a session. Files are a valid, readable way to
maintain persistent instructions; global files and synchronisation can also share
instructions across projects.

Proposed terminal commands:

- `/new-session`: allocate a new session ID, clear conversation history and reload
  system and project instructions.
- `/view-context`: inspect current context without calling the model. Distinguish
  current context from the last submitted request; never show an old request as
  though it belongs to the new session.

These commands are planned and are not implemented in the experiment yet.

**Diagram placeholder 2 — A new session:** system prompt + AGENTS.md → fresh context;
old conversation history is absent. Show the file surviving independently of the
process-local history.

## 3. A preference emerges during work

In the coding terminal, the learner says: “Always add a short comment explaining
why each validation check exists.” They ask for a small Python function to validate
a report filename, then inspect the preference in the current context.

Start a new session. Project instructions remain, but the conversational preference
is absent. A model may still write comments, so inspect the request rather than
using output style alone as proof of memory.

We could build extraction, review and file-update logic. For this workshop we use
a service for extraction and storage, while implementing event capture, identity,
retrieval and context assembly ourselves. We do not build automatic AGENTS.md edits.

## 4. Learn a preference and bring it into new work

Learners implement capture and retrieval as separate small exercises:

1. Implement submission of original user messages and actual assistant responses
   through the Python SDK.
2. State the commenting preference again in a new captured exchange. The earlier
   pre-integration conversation was not recorded retroactively. Inspect both events,
   then inspect the automatically extracted user_preference and its scope.
3. Start a fresh session with the same user identity.
4. Ask for a function to validate a report's column names.
5. Retrieve relevant preferences for that task, inspect the assembled context, then
   evaluate whether the code follows the preference.

Use separate evidence for capture, extraction, retrieval and behaviour. Account for
asynchronous extraction. No manual long-term-memory insertion is presented as learning.
Project exceptions and corrections remain instructor discussion: observed `replaces`
metadata is imperfect and must not drive automatic deletion or precedence.

**Diagram placeholder 3 — Learning and recall:** conversation events → Agent Memory
session store → background extraction → long-term user preferences. A new task and
user identity → scoped retrieval → fresh context alongside system and project
instructions → model. Visually separate background extraction from request-time recall.

## 5. What about skills and procedural memory

Transition: “The agent remembers how you like code written. What about reusable
instructions for how your team performs a task?”

Introduce a skill as procedural knowledge: instructions for performing a task.
Provide a ready-made report-validation skill folder in the learner workspace.
Learners inspect its instructions and supporting files; they do not author a skill.
The exercise publishes that supplied skill to Agent Playbook, then retrieves the
published procedure for a validation task. Supply connection and publication plumbing;
limit learner coding to one small retrieval/context-wiring function, with a copyable
solution. Show the missing retrieved skill before the edit, then the actual published
source and version after it. Publication alone does not change the agent's context. Validate the supported upload/publishing
mechanism and folder format before writing executable lesson commands.
This is a conceptual bridge, not a claim that every skill system has identical
packaging or that local skills cannot be shared.

Then broaden the scope: a team or organisation has multiple published procedures
that should be discoverable and reusable by connected assistants. Explore Agent
Playbook as the shared source for those skills. Each assistant still needs discovery,
retrieval and context integration. Publishing a procedure does not itself enforce
its instructions or establish organisation-wide access control.

Proposed supplied example: a team report-validation skill specifies required columns,
duplicate-ID checks and how to report errors. The exact rules and publishing exercise
are still to be agreed and validated against the provisioned Playbook service.

Keep the distinction explicit:

- AGENTS.md: deliberately maintained project instructions.
- Agent Memory: preferences learned from interactions.
- Skills: reusable procedures for carrying out tasks.
- Agent Playbook: shared publication and retrieval of those procedures.

**Diagram placeholder 4 — From local skill to shared playbook:** first show the supplied local
skill folder → inspection → publication. Then show team-authored, published skills →
Agent Playbook → task-based discovery/retrieval by connected assistants A and B.
Label the second consumer as architectural potential unless the workshop actually
implements it. Annotate source/version visibility and the integration required at
each consumer; do not imply automatic compatibility or unverified access controls.

## 6. Bring the pieces together and verify

The next validation task combines project instructions, relevant user preferences
and a retrieved team procedure. Learners inspect each source in context, review the
produced code and run independent checks against sample data.

**Diagram placeholder 5 — Full request and verification:** current task + project
instructions + retrieved preferences + retrieved skill → assembled model context →
agent/tool loop → generated validation code → independent tests. Keep test outcomes
separate from the model's claims.

Semantic caching is excluded from the required 90-minute arc. It may become a
separate optional demonstration after rehearsal; it must not consume final-task
or catch-up time.

## Authoring requirements

Follow Part 1: observe → predict → small edit → rerun → inspect. Keep one evolving
agent, short lessons, revealable solutions, cumulative catch-up files, supplied
connection setup and the existing browser/editor/terminal layout. Final timing,
learner functions and Playbook provisioning must be settled before implementation.

## Proposed final challenge

“Build a validator for an incoming transaction report, using our team's published
validation procedure.” The transaction-report framing is a working proposal; the
user has agreed to small data-validation tasks, not yet the exact final schema.

Supply a tiny Python project with a stable validator signature, synthetic input
fixtures, a defined error format and independent tests. Pass already-parsed rows to
the validator so CSV parsing and financial-domain choices do not consume the lab. Proposed procedure: required columns, unique
transaction IDs and valid amounts. Define exact columns, amount semantics and
error format in both the published skill and the test contract before authoring
the lesson. Avoid introducing financial domain knowledge as an additional lesson.

The learner inspects three context sources: AGENTS.md project conventions, the
retrieved commenting preference, and the published validation skill. Agent tools
produce the implementation; the learner runs the unchanged checks and explains
one passing and one rejected input. Comment quality is reviewed separately from
functional correctness; a functional test pass does not prove preference adherence.

Require learners to identify which validation rule came from the retrieved skill
and explain why one invalid fixture was rejected.

Show the actual retrieved skill source/version in the request trace. The supplied
local folder can also contain useful instructions, so an accurate answer alone
cannot establish that Playbook was used. Publication acknowledgement and retrieval
trace must provide that evidence. A published procedure guides execution; it does
not enforce permissions or guarantee correctness.

## Mechanics to preserve from Part 1

- One evolving learner agent file and one normal terminal entry point. Supply SDK
  client setup, session commands, display and tool machinery. Learners implement
  the few functions that produce the lesson's behavioural change.
- Revealable explanations and copyable function solutions. Explicit cumulative
  catch-up files preserve previous lessons and do not load silently.
- Run live model/service exercises; use deterministic transport substitutes only
  in harness tests. Replay the published edits in a disposable learner workspace.
- Memory exercises preserve the current instruction stack. Retrieval adds context;
  it does not overwrite system instructions, AGENTS.md or the current task.
- `/view-context` reports current sources and session identity. Before a task,
  clearly indicate recall has not yet happened. After submission, expose the exact
  assembled request separately from later messages; clear that trace on new session.
- Allow for asynchronous extraction. Use inspection and a brief code walkthrough
  while waiting; after two configured intervals, escalate to the instructor and
  use a clearly labelled recorded example, never simulated live success. Record
  the reduced outcome as inspecting extraction evidence rather than completing
  live extraction.
- Owner filters are observable selection, not authorization. Use preprovisioned
  isolation where needed. Preference corrections and imperfect replacement metadata
  are instructor discussion, not mandatory learner implementation.

## Remaining design checks

1. Validate Playbook's actual supported skill format, publication and retrieval flow
   before promising upload commands or a particular organisational grouping feature.
2. Agree the small final validator contract and fixtures.
3. Choose the exact learner function boundaries and implement the supplied session
   and context commands with tests.
4. Rehearse the full progression in the browser workspace, including service latency,
   catch-up paths and unchanged independent checks.

## Instructional design review

A dedicated instructional-design subagent reviewed this arc against Part 1's
schedule, facilitator guidance and sample lessons. Verdict: ready for agreement
as an arc, not yet ready to publish as a runnable workshop.

Incorporated findings:

- Explicitly restate the preference after implementing capture; never imply
  retroactive recording of the earlier lost conversation.
- Supply Playbook plumbing and limit the learner edit to retrieval/context wiring.
- Bound the final task with a supplied signature, fixtures, error format and tests.
- Require learner judgments at each checkpoint, including attributing a rule to
  the retrieved skill and explaining a rejected fixture.
- Reuse a progressively extended architecture diagram across the five placeholders.
- Label recorded fallback as a reduced learning outcome rather than live completion.

The proposed timing is plausible with preprovisioned services and small edits. A
human rehearsal must validate it. If the final task needs 20 minutes, shorten the
opening recap/file exercise by five minutes; protect the memory section and buffer.

## Image production checklist

All entries below are placeholders; no new artwork has been produced yet.

| Placement | Image or diagram required | Teaching purpose |
| --- | --- | --- |
| Opening recap | A: Part 1 learning journey | Reconnect with the six capabilities already built |
| Opening recap | B: Completed Part 1 agent architecture | Establish the common architecture used throughout |
| Existing memory | 1: Highlight the current message list on B | Explain short-term conversation context |
| AGENTS.md exercise | 2: New-session before/after | Show reloaded instructions and cleared conversation |
| Memory integration | 3: Capture, extraction and recall | Separate background extraction from request-time retrieval |
| Playbook exercise | 4: Supplied skill folder to published procedure | Show publication, retrieval and agent integration |
| Final challenge | 5: Combined context and independent checks | Trace each source into the request and verify the resulting code |

Use consistent labels and colours for project instructions, conversation history,
retrieved preferences and retrieved skills. Label user identity and session identity
separately. Reuse the same architecture layout, adding only the newly taught component.
