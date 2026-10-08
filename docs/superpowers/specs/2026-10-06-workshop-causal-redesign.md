# Workshop redesign: build, encounter, improve

Approved in chat on 6 October 2026. Implementation and subagent use are authorized.

Audience: experienced Python developers at Bank of America who are relatively new
to LLM applications. Plan for roughly 90 minutes, including ten minutes of buffer;
validate timing in a facilitator rehearsal. Preserve the Vue workbench, Python SDK,
Docker environment, editor, embedded Terminal, and task-board application.

The learner path is Welcome → model call → PEAS → conversation history → first
tool → better tools → agent loop → repair and evaluation. Welcome explains outcomes
and the instructor-guided format without prerequisite/API-key instructions, an
opening completed-agent demo, or a tour of implementation files. Setup remains in
facilitator/reference documentation, with one quick check command available.

Learners complete small scaffold functions with optional hints and copyable
solutions. Start with FizzBuzz. Inspect a follow-up request that omits the earlier
messages, then retain history. Keep model behavior probabilistic: missing input is
observable even when a model guesses correctly. Explain model + harness, request
state, trained weights, and text as the interface used here without claiming all
models are text-only.

PEAS begins with why design matters. Learners try a design for their coding agent,
then reveal an example in the app. Connect Performance to independent checks,
Environment to the project and runtime, Actuators to edits/execution, and Sensors
to file contents and tool results. Revisit this mapping in later lessons.

The first file tool reads plain text without introducing pagination prematurely.
Show the structured tool request and matching result explicitly: the harness runs
the function. A large file creates observable excessive output; learners improve
the reader with range selection, line numbers and continuation information. Include
a short editable description experiment without guaranteeing model misrouting.
Students implement repetition, stopping and dispatch/feedback; supplied error
handling and approval helpers are explained in context. No new framework or datastore.

Use the embedded Terminal consistently: edit, save, stop/restart, rerun the exact
request. Restart loads new code and clears in-memory conversation. Architecture
diagrams show the model, harness, tools and environment, not file mappings.

Final ticket: completing a task appears successful but refreshing the browser
loses the completion state. The learner's agent reads, edits and runs checks; an
independent evaluator confirms the repair and preservation of existing behavior.
Provide simple tool tests, deterministic harness tests, and application outcome
checks. Explain what each establishes. Live task trials and deterministic tests
must not be conflated. Learners need not build an evaluator.

Remove evidence checkboxes, notes files, mandatory reflection/transfer sections,
and the late separate start-building phase. Keep short questions and revealable
answers in the lesson. Friendly teaching language: clear tasks followed by concise
explanation of the problem just encountered. Keep existing saved user records
untouched even though those controls leave the UI.

Preserve starter exercise gaps and the seeded capstone bug. Verify complete
solutions in disposable workspaces, never by completing the learner's files.
Remove the discovered hard-coded credential from source without displaying or
using it; rotation remains an account-owner action.
