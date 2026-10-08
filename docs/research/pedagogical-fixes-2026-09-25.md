# Pedagogical review: implemented fixes

The ten areas in the [student-perspective review](pedagogical-gap-review-2026-09-25.md)
have implementation changes and verification evidence below. This establishes
that the revised learning path exists and works technically. A real novice pilot
is still needed to validate comprehension, independent transfer and duration.

The authoritative guided material is under
`docker-workshop/frontend/public/`. Active lessons, component map and reference
content are synchronized into the root, legacy and student documentation. The
four starter blanks and the capstone's intentional bug remain exercises.

| Finding | Implemented change | Evidence |
| --- | --- | --- |
| G1: destination not demonstrated | Welcome identifies the final agent, model and target. The first demo runs a completed agent through a greeting repair before the learner edits anything. | `checkpoints/outcome_demo.py` uses scripted replies with real temporary reads, edits, a command and an independent check. Isolation tests pass; the actual student container prints baseline FAIL and final PASS. |
| G2: relationships and ownership unclear | The overview has a component diagram, text equivalent and implement/inspect/supplied table tied to actual files. A closed reference stays beside the editor, with source buttons and a full-size map link. | `review.md`, `images/agent-map.svg`, and the Build reference match main.py, agent.py, tools.py and ui.py. Rendered diagram/table and reference behavior checked in browser; UI tests cover preserving the workspace. |
| G3: incomplete protocol explanation | Lesson 2 walks through schema, assistant request, JSON-string arguments, decoding, registry dispatch, result ID and next request. Four message roles and keyword argument expansion are explained before implementation. | `build-steps/02-one-tool.md` contains the full annotated exchange. JSON examples parse; tests exercise dispatch and result pairing in the completed implementation. |
| G4: disconnected stages | The overview shows a capability ladder and why each checkpoint exists. Lessons connect one exchange to repeated exchanges and distinguish outer conversation from inner tool loops. Blanks now follow learning order: 1 call, 2 reader, 3 stop, 4 feedback. | Each lesson starts with a map location and ends with the next limitation. Root/student source labels and references agree. Stopping is checked before dispatch. |
| G5: teaching hidden behind tasks | Visible worked explanations precede tasks; hints, implementation solutions and practice answers remain closed. A pytest primer explains selection, assertions, expected failure and test evidence. | All six lessons reviewed; browser confirms visible foundations and closed answer disclosures. Renderer tests protect indentation, inline code, emphasis, tables and escaping. |
| G6: supplied behavior unexplained | Lesson 5 tours list/edit/command/web tools, output limits, system prompt, project instructions and approval enforcement. Learners inspect main.py and ui.py before the capstone. | Source ownership and gate claims checked against code. File selector/reference includes supplied components. It states only run_bash/web_fetch are gated and project selection is not a sandbox. |
| G7: insufficient independent practice | Each lesson includes a changed-input task and separate answer explanation: history correction, changed IDs, description rewrite, paging, multiple tool calls, unfamiliar failures, reopening tasks and final reconstruction. | Content review confirms practice requires prediction/application before answer comparison. Actual learner success awaits the pilot. |
| G8: completion confused with understanding | Practical checks, explanation comparison, live attempts and notes are separate persisted records. Final tasks require reconstruction, trace diagnosis, repair explanation and scoped evidence. | State/UI tests cover migration, independent values, storage errors and summaries. Browser test recorded 1 practical, 1 explanation and 0 live; reload preserved them and free navigation added no credit. Temporary test records were restored. |
| G9: offline foundation missing | Every learner assembles first, second and restarted requests with a fictional project name before the optional live call. | `checkpoints/history.py` runs without a key or provider call. Tests check exact role/history relationships and loss of unsent context; student-container run matches the lesson. |
| G10: prerequisites and workload | API/JSON, SDK, pytest and browser/API/state primers appear where needed. Setup is separated, baseline reused, optional live work labeled and timing explicitly provisional. A novice-pilot protocol records operational friction separately from conceptual errors. | `WORKSHOP.md`, `FACILITATOR.md` and the [pilot worksheet](learner-pilot-2026-09-25.md) specify tasks, misconceptions, help, hints and timing. Participant results and a validated schedule remain pending. |

## Verification performed

- **71/71 Python tests pass** in an isolated completed copy. Solutions replaced
  only agent.py/tools.py in that temporary copy; learner files were not completed.
- The untouched starter has **58 passing tests and 13 expected failures**, all
  in the six loop and seven reader cases corresponding to its unfinished blanks.
  The first SDK blank requires a configured optional live call to execute.
- Independent capstone acceptance checks show **8/9 before**, with only completion
  persistence failing, and **9/9 after** the supplied repair in a temporary app.
- **67/67 backend tests pass**. **49/49 frontend tests pass**, strict TypeScript
  passes, and the production Docker build passes. Existing dependency/module-type
  and bundle-size warnings remain; they are not new pedagogy failures.
- Both new modules run inside the actual Linux student runtime with an empty
  API key and an unreachable provider URL. No live provider requests were made.
- Browser walkthrough of the rebuilt local frontend checked the opening path,
  diagram, ownership table, annotated protocol, answer disclosure, persistent
  reference, evidence controls, note persistence and honest finish summary.
  Tables remain scrollable at a 390px viewport; the default viewport was restored.
- Independent spec and code-quality reviews found two minor issues: inconsistent
  JSON field naming and Markdown emphasis spanning inline code. Both were fixed;
  renderer regression tests failed before the fix and now pass.

The first unrestricted Python run encountered filesystem-sandbox restrictions on
local HTTP sockets; the checks were repeated with local-server permission. The
first completed-copy fixture also omitted a document referenced by the link test;
adding that existing document made the complete suite pass. Neither issue required
changing the workshop behavior or weakening its tests.

## What this does not establish

No new live-model reliability claims are made. Prepared replies validate the
mechanism, not model choices. No actual novice learning or completion-time results
have been recorded. Run the pilot and revise the timing and any persistent
misconceptions before treating the pedagogical gap as empirically closed.
