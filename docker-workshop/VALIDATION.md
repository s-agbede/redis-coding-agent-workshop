# Learner acceptance follow-up — 2026-10-07

The revised loop lesson is deployed at http://127.0.0.1:8080/. Learners now run
their completed loop immediately after the three edits. The example follow-up
asks whether the observed files establish that acceptance checks passed. Its
reveal distinguishes a conditional release decision from actual test results.
Supplied actions and approval controls follow as preparation for the repair.
Facilitator guidance protects a minute-55 capstone start and asks learners to
explain who executes a tool and how its result reaches the next model request.

## Pedagogical acceptance audit

An independent agent reviewed as an experienced Python developer new to LLM
applications. It read the original feedback, welcome, active manifest, seven
lessons, scaffolds, capstone and evaluator, then re-read the final edits. Its
verdict was **satisfied with the pedagogical clarity and value**, with no
remaining must-fix pedagogical blocker. This is a simulated learner review;
it is not evidence of a human learner's understanding or actual class pacing.

| Requirement | Current evidence |
| --- | --- |
| Explain LLM, OpenAI, API access and SDK before coding | Lesson 1 introduces each before `ask`; one source-defined FizzBuzz prompt is run once. |
| Earn new capabilities through observable problems | Lesson 3 exposes missing messages; lesson 4 exposes absent file evidence; lesson 5 improves excessive reader output; lesson 6 handles the next requested observation. |
| Explain tools and harness execution | Lesson 4 separates schema, Python execution and matching result; the learner predicts execution at a pause and later implements dispatch and feedback. |
| Small scaffolded edits and supported attempts | Published snippets and catch-up files replay successfully for both root and browser distributions. Hints and answers stay closed until requested. |
| Motivation, learner decisions and a meaningful finish | Welcome names the repair; PEAS uses that ticket; reader design and the new follow-up require evidence judgments; lesson 7 requires explaining the changed state before accepting checks. |
| Friendly teaching with room to read | Short sections, architecture diagrams and revealable explanations remain. The browser check verified the new follow-up and answer in the rendered lesson. |
| Run code instead of copying shell commands | The welcome button submitted `uv run python check_setup.py` to the existing visible terminal; actual output was inspected. Python answers remain copyable. |
| Supplied evaluators at the end | Lesson 7 separates tool, harness and application checks, explains prepared test replies and requires independent HTTP checks plus browser refresh. Lessons 1–6 have no required pytest command. |
| Roughly 90 minutes for experienced Python developers | Budgets total 90 minutes, including 25 for repair/evaluation and 10 buffer. The facilitator guide protects the final task. Timed human pacing remains unvalidated. |

## Fresh technical checks

- **138 Python tests passed** in the final disposable completed copy in 29.83s.
  The real starter functions and seeded capstone were not completed in place.
- **10 documentation and published-progression checks passed** in 16.14s,
  including applying the actual snippets and solution files to both distributions.
- The Docker frontend build passed **80 frontend tests**, strict TypeScript
  checking, production compilation and **16 workbench tests**. Existing module
  type and bundle-size warnings remain.
- **13 served assets match their source files**. The frontend was replaced.
  The runtime was subsequently reconnected to the existing root model configuration.
- **10 protected files retain their initial hashes**, covering first-call and
  agent starters, seeded app, verifier and environment files in both distributions.
  Only the supplied listing function changed within the two protected `tools.py`
  files; the learner's reader gap remains unfinished. Source and test mirrors match.

The saved [browser view of the evidence judgment](../docs/research/screenshots/2026-10-07-learner-evidence-judgment.jpg)
shows the new question, explanation and transition to repair. Root, student,
Docker documentation and guided lesson copies are synchronized.

## Live evidence and corrections

The root project's existing credentials supported a real GPT-5 FizzBuzz call
in 8.0s. Three further live requests verified the history lesson in 40.332s:
the isolated follow-up sent only `user` and asked for context; the retained
follow-up sent `user → assistant → user` with the prior code and produced the
requested 20-item behavior. The generated function retained its earlier name,
reinforcing the lesson's instruction to inspect the result. Local evidence is
under `/private/tmp/workshop-live-first-call.json` and
`/private/tmp/workshop-live-lessons-9zdq3g3x/`.

After the user explicitly approved sending the fictional workshop files, prompts
and tool results to OpenAI, live file checks observed all the intended contrasts:

- Chat without tools reported that it could not access the local file.
- The plain reader supplied Cedar from the actual brief.
- Reading the full release log returned 200 lines and **16,934 characters**;
  the model's paged request used offset 170, limit 20 and returned **1,857 characters**,
  including line 180 and continuation at line 190.
- The one-exchange checkpoint ended with an unexecuted request for the referenced
  file. The completed loop obtained both observations and answered from them.
- The revised follow-up distinguished conditional readiness from evidence that
  checks passed. Its natural completion used the interactive 25-step budget.

The file rehearsal used 18 real provider requests in 82.628s. An early artificial
six-step probe was superseded by natural completion from the same actual tool
observations; this limitation is recorded in
`/private/tmp/workshop-live-files-mkmxtk5d/REVIEW.md`.

The first live repair exposed two facilitator-rehearsal defects. Sentence
punctuation changed a command ending in `--project .` into `--project ..`.
Rehearsal also inherited a ten-step function default instead of the interactive
agent's 25-step budget. The model described a fix without saving it, and the
independent checker correctly remained at **8/9**. The command is now fenced on
its own line, and rehearsal passes `main.MAX_ITERS` explicitly. Both regressions
were observed failing first; the corrected rehearsal suite passed **14 tests**.

A separate live tool call found that `list_files("")` validated the current
directory but enumerated an empty path, falsely reporting no files. Normalizing
the path consistently fixes this in the supplied tool and solution. The two
implementation regressions failed before the fix and passed afterward. A separate
code review found no remaining actionable issue in these corrections.

A fresh live repair with the fixes took **12 model turns and 33.9s**. It changed
only the task update handler, stored the updated object, ran the correct verifier
before and after, and passed **9/9** independent acceptance checks. In the actual
agent-repaired disposable app, browser completion survived refresh; reopening
then survived a second refresh. See the
[refreshed repaired app](../docs/research/screenshots/2026-10-07-live-repair-refresh.jpg).
Both the failed and successful trial reports and diffs are preserved under
`output/rehearsal/20261007-learner-acceptance/` in the repository root. This is one
successful final trial, not a reliability estimate.

The running Docker service now uses the existing root configuration through
`docker compose --env-file .env -f docker-workshop/docker-compose.yml` at the time of rehearsal. Following repository cleanup, use `bash start.sh` from the root instead.
The terminal was idle and its preview empty before restart. Saved source and
credential files remain unchanged, and command auto-approval remains disabled.
The setup check now finds the key, and `uv run --no-sync python -m solutions.first_call`
succeeded against the real service inside Docker. The empty seeded preview was
restored and the browser was left at lesson 1 with learner gaps intact.

A timed human pilot remains necessary before claiming validated classroom pacing
or human learning outcomes. The allowed simulated learner review accepts the
current clarity and value. Prepared replies remain confined to automated tests;
the live outcomes above used the actual provider.

Earlier entries below are historical where status or counts differ.

# Motivation and request evidence verification — 2026-10-07

The approved motivation revision is running at http://127.0.0.1:8080/.
The welcome now names the concrete repair goal above Start Workshop. PEAS uses
that ticket, and learners predict outcomes before comparing requests or tool
results. The reader lesson asks learners to design a useful shortened result;
the loop includes a learner-chosen follow-up; the capstone asks them to explain
the code change before accepting the result. The schedule remains 90 minutes,
with 25 minutes for repair/evaluation and ten minutes of buffer.

`--show-messages` optionally previews the actual message count, roles and content
in the first-call and conversation runners. The supplied adapter forwards the
original arguments and response unchanged; long display previews have an
explicit 600-character cutoff marker. The loop lesson enables the existing
verbose mode, which now shows complete non-command tool results, including the
reader's own bounds and continuation guidance. Default output and command
approval behavior remain unchanged.

## Automated checks and review

- **136 Python tests passed** in a disposable completed copy. Published-snippet
  and catch-up-file replay cover both distributions, including the request trace.
- **80 frontend tests**, strict TypeScript checking, the production build and
  **16 workbench tests** passed in the final Docker build. Existing module-type
  and bundle-size warnings remain.
- **38 focused tracing/display tests passed inside the running Linux runtime**.
  These tests use test doubles and real local file results without provider calls.
- **6 documentation checks passed** after the last prose adjustments. Lesson
  bodies and Python source/test mirrors match. Timing totals 90 minutes.
- Independent code and pedagogical reviews completed. Two findings were fixed:
  tool evidence was hidden by the normal terminal display, and an old starter
  docstring incorrectly directed learners to tests during the loop lesson.
- The seeded app, acceptance verifier and environment files retain their
  pre-change hashes. Learner functions remain unfinished. No dependencies or
  runtime services were added.

The first disposable regression copy omitted this validation file, causing its
documentation-link check to fail. Restoring that fixture resolved the failure;
the complete final suite then passed. No product change was needed for it.

## Deployed browser checks

The frontend was rebuilt and replaced; the runtime and shared terminal session
were preserved. Thirteen served lesson/configuration/diagram assets match their
sources. The browser walkthrough checked the visible opening promise, working
setup Run code action, request-preview commands, closed answers, the expanded
reader-design table, the verbose loop command and the capstone judgment. The
welcome was checked again after reload and left ready to start.

Screenshot: [reader-design question and comparison](../docs/research/screenshots/2026-10-07-motivation-reader.jpg).

## Remaining validation

The runtime reports no model key configured. No live-provider request or timed
human learner pilot was performed. The approved plan leaves these two checks
pending: technical tests establish behavior, while the pilot must assess actual
pacing, understanding and motivation. Prepared replies remain inside tests and
are not presented as a live workshop success.

Earlier entries below are historical where behavior or counts differ.

# Lesson context and Run code verification — 2026-10-07

The revised workshop is running at http://127.0.0.1:8080/ with the first lesson
selected. The first-call lesson now introduces LLMs, OpenAI, API access and the
Python SDK before implementation. The file-reader lesson explains tool schemas,
host execution and results, and why the project-brief question tests access to
local evidence. Compact diagrams and paragraph spacing support both lessons.

Live execution is the main path. The first-call command uses the prompt already
defined in its source; the early exercises no longer offer scripted CLI replies.
Test commands are collected in evaluation. Shell blocks have a Run code action
that reveals the shared Terminal and dispatches the displayed command. Python
answers remain copyable source snippets. Busy terminals and unfinished input
are refused without interrupting the running program.

## Automated and independent checks

- **113 Python tests passed** in a disposable completed copy after the final
  changes. These include published-answer replay, application tests and the
  capstone. Test doubles replace provider requests; the real learner functions
  remain unfinished. Ten root/student Python source mirrors match.
- **80 frontend tests**, strict TypeScript checking and the production build
  passed. Existing module-type and bundle-size warnings remain.
- **93 backend tests** and **16 workbench tests** passed. **15 real tmux tests**
  also passed against an isolated session in the Linux runtime, including busy
  input, exact dispatch, concurrent requests and Ctrl+C recovery. These tests did
  not send commands to the learner's terminal.
- Root and student documentation checks passed (**6 each**). All **13 checked
  served assets** matched their sources: welcome, configuration, manifest,
  seven active lessons and three diagrams.
- Independent curriculum/UI and runtime reviews completed with no remaining
  actionable findings.

## Deployed browser checks

Both the frontend and runtime were rebuilt and are healthy. Student files,
environment configuration and persistent volumes were preserved. The browser
walkthrough verified the welcome Run code action, visible command and output,
rejection while a Python program awaited input, and successful execution after
that program exited. Model and tool explanations were inspected in the normal
lesson column and expanded view; the complete tool diagram fits the normal
column. The workshop was left on the revised first lesson.

- [Run code in the shared terminal](../docs/research/screenshots/2026-10-07-run-code.jpg)
- [Model and API context](../docs/research/screenshots/2026-10-07-model-context.jpg)
- [Tool exchange in the lesson column](../docs/research/screenshots/2026-10-07-tool-context.jpg)

## Remaining validation

The runtime has no API key configured, so no live-provider requests were made.
Deterministic tests verify the scaffold and command delivery, not live-model
reliability. The 90-minute schedule still needs a timed learner rehearsal.

Earlier entries below are historical where behavior or counts differ.

# Causal workshop redesign verification — 2026-10-06

The revised instructor-led workshop is running at http://127.0.0.1:8080/.
Seven lessons build from a first model call through PEAS, conversation history,
a plain file reader, bounded file reading, an agent loop and a task-board repair.
The welcome and navigation no longer require evidence forms, learner notes or
progress summaries. Small function exercises have optional hints and copyable
answers, and tool, harness and application checks are already supplied.

## Automated and independent checks

- The completed Python copy passed **108 tests** before the final pending-tool
  trace correction. After that correction, the checkpoint and published-lesson
  replay suite passed **12 tests**. The replay applies the actual Markdown
  answers and catch-up solution files to disposable copies of both starters.
- The final published-lesson replay and documentation suite passed **10 tests**.
  It exercises first call, lost/retained history, plain/bounded reading and the
  completed agent loop without contacting a provider.
- **70 frontend tests**, **15 workbench tests** and **67 backend tests** passed.
  Strict TypeScript checking and the production frontend/Docker builds passed.
  Existing dependency deprecation and bundle-size warnings remain.
- The intentional learner exercises remain unfinished: the targeted starter
  checks produced **22 expected failures and 10 passes**. Both capstone source
  copies remain byte-for-byte unchanged. The independent capstone checks report
  **8/9** on the seed and **9/9** with the supplied repair in a temporary copy.
- Independent curriculum/UI and runtime reviews completed with no remaining
  actionable findings. Runtime review also exercised serialization through the
  installed OpenAI SDK with `httpx.MockTransport`; this made no network calls.

## Deployed browser checks

The browser walkthrough covered the welcome, all seven lessons, PEAS reveal,
copyable code, source-file links into Code, lesson focus/navigation and the final
return to welcome. The editor and terminal panels remain available alongside the
instructions. Legacy `/guide/review` and `/guide/demo` URLs redirect to
`/guide/build`. The browser was returned to the welcome with the first lesson
selected for the next start.

An older browser cache initially displayed previous lesson content. The
frontend now sends `Cache-Control: no-cache` for its entry pages and Markdown/YAML
content. Nginx configuration validation passed, and HTTP checks confirmed these
headers and exact source/served equality for the welcome, configuration,
manifest and all seven active lessons after deployment. Only the frontend
container was rebuilt; student data and runtime configuration were preserved.

Screenshot: [agent-loop diagram in the workbench](../docs/research/screenshots/2026-10-06-agent-loop.jpg).

## Remaining validation

No live-provider requests or timed learner pilot were performed for this change.
Prepared responses and deterministic tests establish the scaffold behavior, not
live agent reliability. The schedule budgets 3 minutes for welcome, 77 minutes
for lessons and 10 minutes of buffer; it still needs a timed rehearsal.

The hard-coded credential was removed from both first-call sources in favor of
environment configuration. It was not used or printed; the previously exposed
credential should be rotated by its owner. The environment files were unchanged.

Earlier entries below are historical where lesson paths, UI or counts differ.

# Workbench port verification — 2026-09-25

The default UI now uses the reference workbench with native VS Code, shared
Terminal, App Preview and the revised lessons at `/guide/`. See the
[port verification record](../docs/research/workbench-port-2026-09-25.md)
for coordination, browser checks, corrected integration issues and limits.

The final build passed 68 frontend tests, strict TypeScript, the production build
and 15 workbench tests. Backend tests passed 67/67; the isolated completed Python
copy passed 71/71 in the new runtime. Both services are running, with the runtime
healthy. Student exercises and the capstone seed remain intact.

Earlier entries below describe previous versions of the shell and test counts.

# Pedagogical foundations verification — 2026-09-25

The guided frontend at http://localhost:8080 was rebuilt after the ten-area
pedagogical redesign. See the [coverage record](../docs/research/pedagogical-fixes-2026-09-25.md)
for implemented changes and the [learner pilot](../docs/research/learner-pilot-2026-09-25.md)
for the remaining empirical validation.

- 71 Python tests pass in an isolated completed copy; the actual starter retains
  13 expected reader/loop failures and 58 passes.
- 49 frontend tests, strict TypeScript, the production Docker build and 67 backend
  tests pass. Existing dependency and bundle-size warnings remain.
- Capstone verification remains 8/9 on the seed and 9/9 after the supplied repair
  in temporary copies. Learner blanks and capstone seed were preserved.
- New history and completed-agent demonstrations also ran inside the actual Linux
  student container with no provider key. Replies are scripted; file operations
  and independent greeting checks are real.
- Browser verification covered the map, tables, closed answers, reference panel,
  independent evidence/notes, reload persistence and finish counts. Narrow tables
  scroll; temporary progress records and viewport settings were restored.
- Independent spec/quality review findings were fixed, including a regression
  test for emphasis around inline code.

No live-model calls or real novice participant sessions were performed for this
change. The 90-minute estimate remains provisional. Earlier entries below are
historical when test counts or lesson descriptions differ.

# Self-paced workshop verification — 2026-09-25

The guided frontend at http://localhost:8080 was rebuilt and deployed after the
instructor-free usability improvements. The earlier redesign evidence below is
historical where counts differ.

- **68 Python tests passed** in a temporary completed-solution copy inside the
  actual Linux student runtime. Learner files were not substituted in place.
- **37 frontend tests passed**, strict TypeScript passed and the production
  Docker build passed. Existing Node module-type and webpack bundle-size warnings
  remain. Regression tests cover queued file reads/saves, preserved selected code,
  indent/outdent/undo, external-file reload protection, code-copy failures,
  self-check persistence, summary honesty and responsive focus/scroll behavior.
- Readiness and tool-feedback changes were tested first: failed shell commands
  exposed the previous false-green display; the replacement reports exit status
  and output even outside verbose mode. Setup checks make no provider requests.
- The actual offline checkpoint outputs match the lesson expectations: matched
  read-1 requests/results, explicitly scripted description proposals, and distinct
  missing-file, denial and exit-3 feedback.
- The untouched capstone reports **8/9** checks, failing only completion
  persistence. The supplied repair reports **9/9** in an isolated temporary app.
- Independent content/Python and UI spec/quality reviews completed. The responsive
  scrolling finding was fixed and reviewed again; no significant findings remain.

## Plain-language update

Student-facing wording was revised after the usability changes. Abstract titles
were replaced with actions, including “Try the app and find the bug” and “Run
the tests before fixing it.” Setup, explanations, progress messages and the six
lessons now use common words and introduce necessary technical terms.

For this wording-only update, **37 frontend tests** and **14 focused Python/docs
tests** passed, along with strict TypeScript and the production Docker build.
The deployed browser walkthrough confirmed the new phase names, app steps,
lesson titles and progress wording. Screenshots: output/playwright/plain-language-demo.png
and plain-language-build.png at repository root. No model calls were made.

## Writing directly to the student

All six build lessons now open with a direct introduction explaining what you
will do and why. Instructor-style competency statements were replaced with
questions about the student's own code and results. API-key alternatives explain
where to continue without progress-bookkeeping language in the introduction.
The mirrored lesson docs and authoring guidance were updated too.

For this copy-only change, **37 frontend tests**, **5 documentation tests**,
strict TypeScript, the local production build and the Docker frontend build
passed. Both existing in-app browser tabs were refreshed from their older
content. The rendered first lesson was checked in the user's existing tab:
the new introduction, API-key guidance and closing questions were visible.
No model requests were made.

## Browser walkthrough

Playwright exercised the deployed UI at 1366×768 and 800×900:

1. Welcome visibly renders prerequisites, offline/live routes and host setup.
2. Demo and Build select their requested files; the default selector has 13
   relevant files, with 61 available via All files in the current workspace.
3. Unsaved selected scratch code survives Tab and Shift+Tab; keyboard undo works.
   Reload file is disabled while dirty. Scratch text was restored without saving.
4. The Copy control places the exact command on the clipboard. The capstone task
   is visually wrapped while remaining one logical line for the agent REPL.
5. All six lesson transitions reset desktop instruction scroll to zero and focus
   the title. Narrow-layout navigation brings the title to viewport top.
6. A self-check persists after reload and can be unchecked. After restoring all
   checks to unconfirmed, Finish shows 0/6 with each lesson unconfirmed rather
   than claiming success or silently navigating home.
7. Root/student first_call.py, tools.py, agent.py and capstone/app.py remain
   identical; all student blanks and the seeded app defect remain intact.

Screenshots at repository root: output/playwright/self-paced-demo.png,
self-paced-first-lesson.png, self-paced-finish.png and self-paced-narrow.png.

## Remaining limits

No additional live model calls were made. The local CLI has a key present, but
its validity was not tested; the browser student runtime currently reports no
configured model key. The visible setup instructions explain configuration and
runtime recreation. The offline learning route is available without it.

The previously measured live repair failed; these UI/teaching changes do not
establish live agent reliability. There is still no timed novice learner pilot.
Self-checks are explicitly learner reports, not automatic grading.

---

# Workshop redesign verification

Verified on 2026-09-25. The redesigned guided workshop runs at http://localhost:8080.

## Automated checks

- Completed agent/tool implementations substituted into an isolated temporary copy:
  **59 workshop tests passed** on macOS after adding four trace regressions.
  The earlier **55-test suite passed** inside the actual Linux runtime container.
  No learner source was overwritten for these suite runs.
- Editor API: **67 passed**.
- Final untouched starter: **42 passed, 13 expected failures**, all confined to
  the unfinished agent-loop and read_file exercises.
- Frontend: **8 passed**, including closed disclosures, escaping and Python code
  preservation, course-file references and editor save/error behavior.
- Strict TypeScript check, Vue production build and Docker production build pass.
- Three offline checkpoints ran successfully: a real file read with matched call
  IDs, explicitly illustrative description proposals, and real error/denial/exit-3
  feedback under a scripted model.
- Independent spec and quality reviews completed; findings about cleanup on failed
  creation, output caps, editable test fixtures and invalid rehearsal baselines
  were corrected and regression-tested. No outstanding review findings.

## Browser and HTTP checks

Playwright exercised the rebuilt local stack:

1. Welcome, Review, all three Demo pages and all six Build lessons.
2. Initially closed hints, opening the first-call solution, and completion criteria.
3. Editor save, switching away, reopening the file, then restoring its original text.
4. Starting the capstone through the actual interactive terminal.
5. Task creation, completion and refresh through the /app/ preview proxy.
6. Broken starter: **8/9 acceptance checks**, failing only completion persistence;
   the browser also loses completion on refresh.
7. Supplied repair: **9/9 acceptance checks**; completion survives a real frame reload.
8. Restored starter: **8/9 checks** again, with only the deliberate failure.

The supplied repair was temporarily substituted for browser verification and then
restored. Managed root/student sources match. The first-call, file-reader and
agent-loop blanks remain intact. Temporary browser QA tasks were deleted; code
reload also resets the application's in-memory store. The preview server remains
available for the opening demo.

Screenshots: output/playwright/redesign-demo.png, redesign-capstone-repaired.png
and redesign-welcome.png at the repository root.

## Live rehearsal

After explicit user approval, one live rehearsal ran with the configured `gpt-5`
model on 2026-09-25 using `uv run python -u rehearse.py -n 1`. The independent
baseline confirmed the expected completion-persistence defect before the model
ran. The final independent checker passed **8/9 checks**, with **complete
persistence still failing**. The command exited 1: **0 successful repairs out of
1 attempt**. This is one failed sample, not an established reliability estimate.

The log is [live-2026-09-25.log](../output/rehearsal/live-2026-09-25.log).
That version of the harness did not retain the conversation/tool trace or
temporary project, so this log establishes the failed outcome but does not
explain the model's choices or whether it stopped at the iteration cap.

The harness now retains a report.json with messages, tool calls/results, provider
stop reasons, token usage when supplied, and independent checks, plus a source
diff. Offline regressions cover false completion claims, iteration limits,
partial traces after errors and provider output limits. A diagnostic live rerun
was blocked by automatic approval review because the earlier approval covered
only one run; fresh approval is required. No additional live requests were made.
The cause of the failed model repair is still unconfirmed.

The diagnostic change also passed independent code review. It preserves the
original prompts and loop budget so the next run can investigate the failure
without speculative behavior changes.

## Limits

The live repair remains unsuccessful in the single measured run. A 90-minute
learner pilot has not been run. The earlier automatic approval rejection was
resolved by the user's explicit approval for this one rehearsal.

Rehearsal now requires a clean starter source and independently establishes the
expected failing baseline before calling the agent. An already-repaired or
otherwise invalid source cannot count as a successful repair.

Existing Vue CLI bundle-size, Node module-mode and Starlette TestClient deprecation
warnings remain non-fatal.

---

# Earlier template migration verification

Verified on 2026-09-25 against the source revision recorded in [UPSTREAM.md](UPSTREAM.md).

## Automated checks

- Editor API: **67 passed**, including real filesystem reads/writes, strict input
  validation, generated/hidden path restrictions and symlink-race regressions.
- Frontend: **6 passed**, covering save persistence, failed-save recovery,
  concurrent typing, failed reads, Python code rendering and all six lesson files.
- Strict TypeScript check and Vue production build pass.
- Docker Compose configuration and both production image builds pass.
- Existing root docs/rehearsal checks: **6 passed**.
- Full existing deterministic suite with completed facilitator implementations
  substituted into a temporary copy: **20 passed**. No student files were replaced.
- Unchanged student starter: **12 passed, 8 expected failures** in the intentionally
  blank agent-loop and web-fetch exercises.

## Browser and container checks

A fresh Playwright browser session exercised:

1. Welcome → Review → all three Demo pages → all six Build pages.
2. Lesson file buttons, including after changing files manually.
3. Editing and saving a temporary Python file, switching away and reopening it.
4. A simulated failed save: edits remain visible, route navigation is blocked,
   and a subsequent successful save permits navigation.
5. Running a temporary FastAPI app via the actual browser terminal.
6. Viewing `{"message":"Hello World"}` in App Preview and through the proxy URL.
7. Matching-origin terminal WebSockets succeed; foreign-origin requests using
   the `tty` protocol are rejected, in both production and development proxies.

The QA stack used an isolated Compose project and temporary ports. Its containers,
volume and temporary Python source were removed after testing. Screenshots are
available locally under `output/playwright/` at the repository root.

No live model requests were made. The actual API-key exercises and agent capstone
remain facilitator/student runs. Upstream toolchain output includes Vue CLI bundle
size warnings and a Starlette TestClient `httpx` deprecation warning; neither
caused a failed check.
