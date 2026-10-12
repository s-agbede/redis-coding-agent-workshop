# Causal progression in the student experience

The active guide now uses the same sequence throughout: predict, encounter the
current limitation, explain it, change one mechanism, retry the same task, then
reflect. Opening demos introduce prediction and paired evidence too. Notes use
**Before / Change / After / Why**; transfer questions follow the comparison.

| Lesson | Observed limitation | Change and same-task retry |
| --- | --- | --- |
| Messages | The latest question contains no project-name evidence. | Include retained messages; inspect the same question's outgoing payload. |
| Reader | Naming a local file supplies no contents. | Implement the reader; submit its real output with the matching call ID. |
| Context | The three-line page cannot answer a question about line six. | Follow the returned continuation offset; inspect line six from the same file. |
| Loop | One exchange leaves the second read pending. | Repeat dispatch and feedback; obtain both pages for the same task. |
| Recovery | The successful-call loop stops at a missing file. | Convert the exception to tool feedback; rerun the identical recovery fixture. |
| Verification | Passing agent tests leave the target app's persistence bug. | Repair the app; repeat the unchanged checker and browser interaction. |

Lesson 4's catch-up solution deliberately omits exception conversion. Lesson 5
extends that exact dispatch. Learners who already completed recovery can observe
a supplied baseline without replacing their work. Root and Docker starter
checkpoints, stage solution, tests, scaffold comments and overview documents match.

## Validation

- **31 focused Python tests passed.** These include four rehearsals that apply
  the published lesson snippets or stage-4 catch-up solution to temporary copies
  of both starters, observe the expected missing-file failure, and then apply
  lesson 5's snippet and verify recovery.
- **90 tests passed, 5 skipped** in a temporary completed copy inside the actual
  Docker runtime. This includes real HTTP acceptance tests for broken and repaired
  capstones. The five skips require the full repository and were covered by the
  focused host run; they are not suppressed failures.
- **68 frontend tests and 15 workbench tests passed**, together with TypeScript
  checking and the production Docker build. Existing module-format and bundle-size
  warnings remain.
- Independent pedagogical/code review found and resolved a stage-solution
  variable mismatch. A regression test also caught missing assistant-role labels
  in the displayed prepared request payload; both starter copies now include them.
- Browser inspection confirmed the deployed guide's paired commands, prediction
  prompts, closed hints, preserved code indentation, reflection prompts and
  lesson-4-to-5 transition inside the VS Code workbench.

Only the frontend container was recreated. Validation used temporary copies;
learner implementation files were not replaced with solutions, and the running
runtime was not restarted.

## Limits of this evidence

The offline comparisons use prepared model proposals and actual Python reads,
dispatch, errors and recorded requests. They establish runtime behavior, not live
model reliability. Completion checks require actual submitted file evidence; a
prepared final answer does not count. The description comparison remains labelled
as illustrative offline, with an optional live route.

No novice learner pilot or live provider run was performed. The guide and
facilitator notes retain the provisional timing caveat, and the learner-pilot
protocol now asks whether students can explain each observed transition.
