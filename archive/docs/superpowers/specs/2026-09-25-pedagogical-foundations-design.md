# Pedagogical foundations

The user approved implementation of all ten findings in the pedagogical gap review. This spec makes that direction executable without another approval gate.

Keep the Python SDK loop, six lessons, supplied tools, starter blanks, seeded capstone bug and guided Vue workspace. Preserve student work. The workspace has no Git metadata, so changes are made directly and compared with a temporary source snapshot.

## Learning experience

- G1: show a prepared completed-agent read/edit/check demonstration on a temporary toy project before the learner edits anything. It executes real Python operations with clearly labeled scripted model replies and never modifies the capstone.
- G2: introduce the finished product, a visual component map, the implement/inspect/supplied ownership table, and a map available alongside every build lesson.
- G3: show a complete annotated schema/request/decoded arguments/dispatch/result/next-request exchange and the four message roles.
- G4: map checkpoints to the final agent, explain outer human turns versus inner tool rounds, and number blanks 1 through 4 in learning order.
- G5: put the minimum explanation and worked example before each task; teach reading test output; preserve closed hints and solutions.
- G6: explain supplied tools, system instructions, project instructions and actual approval enforcement before full-agent use.
- G7: give each lesson a small changed-input exercise with an answer explanation; require a description rewrite and an unfamiliar paging/recovery case.
- G8: separate practice, understanding and live-attempt records, retain notes, and provide a final reconstruction/diagnosis exercise with a rubric. Existing self-checks do not automatically certify new understanding checks.
- G9: add an offline conversation-history exercise before tools. It shows first and second requests and a restart without contacting a model. Live calls remain optional and separately recorded.
- G10: separate setup from learning time; add JSON, argument unpacking, pytest and browser/API/state primers where needed; reuse the opening baseline in the capstone; provide a timed novice-pilot worksheet and report its status honestly.

## Implementation boundaries

Use Markdown and an SVG diagram instead of a new visualization dependency. The existing safe renderer gains only the table/image support needed for these teaching aids, with regression tests for escaping. Keep the runtime flat. Add small typed offline scripts and tests. Do not introduce a grading service, provider calls, a framework migration or advanced agent topics.

Synchronize core student lesson copies and intended starter documentation after integration, without copying solutions into student blanks. Tests use isolated completed copies. Keep the supplied capstone broken in the distributed starter.

## Verification

Run meaningful tests before new runtime and progress/rendering behavior. Verify offline examples, complete-solution Python tests, expected starter failures, frontend tests/typecheck/build, and browser navigation, diagrams, disclosures and evidence persistence. Map every review finding to delivered files and evidence. Actual learning effectiveness and duration require a real learner pilot; prepare it, but do not invent participant results.
