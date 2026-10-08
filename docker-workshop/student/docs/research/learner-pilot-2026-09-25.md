# Learner pilot: coding-agent foundations

Status: protocol ready; no participant sessions or measured learning results have
been recorded. Automated and browser checks validate the materials and interface,
not whether a novice understands them or finishes in 90 minutes.

## Recruit and prepare

Recruit at least three developers who can write Python functions, dictionaries,
loops and exceptions but have never implemented an agent loop. Include a learner
who takes the entire offline path. Use a fresh starter copy and fresh browser
progress for each session. Do not preload solutions. Explain that the materials,
not the participant, are being evaluated. Use participant codes; never record API
keys or other credentials in notes.

Run setup separately from learning. Record Docker download/build time, startup,
Terminal orientation and environment errors. The 90-minute core estimate is a
hypothesis. Let the learner finish at their own pace; stop or split the session if
needed, retaining where and why they stopped. Time optional live experiments and
later practice separately. Record service failures as operational friction, not
conceptual failure.

## Session record

Participant code: ______  Date: ______  Facilitator: ______
Python experience: ______  Prior agent-loop implementation: ______
Path: offline / live / mixed  Setup minutes: ______
Core minutes: ______  Optional minutes: ______  Completed through lesson: ______

For each row record elapsed core time, errors, hints opened, solution use,
instructor interventions and the learner's explanation **before** showing answers.
Do not mark a concept understood merely because code/tests pass.

| Stage | Observe without supplying the answer | Minutes / help / evidence |
| --- | --- | --- |
| Orientation | After the greeting demo, identify the agent, model and target; name one thing implemented and one supplied. | |
| Lesson 1 | Construct the second and restarted request; explain whether printed output supplies context. Apply the Birch correction. | |
| Lesson 2 | Explain schema vs registry, JSON string vs decoded arguments, and match a changed tool ID to its result. Read a pytest failure and identify expected vs actual. | |
| Lesson 3 | Rewrite a tool description, predict a suitable use, and read the next excerpt using its returned offset. Explain what the offline trace does not establish. | |
| Lesson 4 | Implement stopping before dispatch. Draw a reply with two calls and its results. Identify inner vs outer loop and a missing result. | |
| Lesson 5 | Find supplied operations, system/project instructions and approval enforcement. Classify a new missing-file error, denial and nonzero command result. | |
| Lesson 6 | Follow browser → API → state; compare update response with subsequent read. Repair, rerun unchanged checks, refresh and reopen a task. | |
| Explain back | Reconstruct the architecture, diagnose the incomplete trace and write an evidence report without the answer rubric. | |

Keep a small excerpt of the learner's own explanation with each score. Record
whether it was independent, corrected after a prompt, or copied from an answer.
If a learner uses the supplied repair, assess their explanation but do not record
an independent implementation. If a live call fails, record the actual failure;
offline continuation remains valid learning evidence.

## Misconception rubric

Score each dimension 0 (incorrect or absent), 1 (partly correct or needs a prompt),
or 2 (correct explanation applied independently to the changed example).

| Dimension | Evidence for 2 | Common misconception to record |
| --- | --- | --- |
| Participants and ownership | Model proposes; Python executes; target app is separate; names implemented and supplied pieces. | Model directly reads files; target website is the agent. |
| History | Sends prior messages and results explicitly; restart creates a new list here. | Printing or a previous call automatically creates persistent memory. |
| Protocol | Explains four roles, argument decoding, registry dispatch, assistant-before-result ordering and matching IDs. | Schema executes a function; any ID/role is acceptable. |
| Control flow | Inner loop handles actions for one request; outer loop gathers human turns; no-tool/cap is not task success. | A final answer or cap proves repair. |
| Feedback and permissions | Distinguishes denial, exception and nonzero exit; points to actual wrapper. | Prompt instructions enforce permission; denied command passed. |
| Repair and evidence | Connects stored updated object to later reads; uses unchanged checks and fresh browser task; scopes report. | Successful PATCH response, passing loop tests or scripted demo proves live repair. |

Do not combine these into a single completion checkbox. Any remaining score of 0
marks a teaching gap even when tests pass. Preserve separate practical, conceptual
and live evidence, matching the workshop's progress records.

## Revision decision

After each session, record the first point of confusion, the exact text/control,
what the learner expected, and the smallest change to test next. Repeated stalls,
answer copying without explanation, and incorrect transfer are higher priority
than cosmetic preferences. Re-run affected tasks with another novice after fixes.

Report actual ranges and medians for setup, each core lesson and optional work.
Revise the public duration and lesson allocation using those results; do not use
an expert rehearsal as novice timing evidence. In particular, reassess the shared
15-minute tool segment. Publish remaining misconceptions and unfinished tasks
alongside completion counts. A small pilot informs revisions; it is not proof of
universal learning effectiveness.

## Results

Pending a real learner pilot. Do not fill this section from automated tests,
a scripted agent run, or an expert walkthrough.
