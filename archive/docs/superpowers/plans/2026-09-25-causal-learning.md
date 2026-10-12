# Consistent causal learning

**Goal:** Every lesson begins with a prediction and a runnable limitation, then changes one mechanism and repeats the same task. The user approved this progression in the preceding conversation.

**Architecture:** Keep the six lessons, current workbench, student scaffold and independent capstone checker. Add offline checkpoint experiments using real student readers/loops and explicitly prepared model proposals. Derive completion evidence from actual messages and file results, never from a prepared final answer. Preserve all learner files during validation by using temporary copies.

**Tech stack:** Python, existing Pydantic and pytest; existing Markdown/Vue guide.

## Experience contract

1. Messages: compare the same question with latest-message-only versus retained history. Student changes the request assembly; no key needed.
2. Reader: ask the same file question using messages alone, then run the student's reader and feed its result back.
3. Context: ask for line six with the first three-line page, observe missing evidence, choose a continuation offset, retry. Description wording remains a separately qualified selection experiment.
4. Loop: use one exchange on a task needing two pages, observe an unexecuted second request, implement stopping/dispatch, repeat the identical task with the student's loop. Do not implement exception conversion yet.
5. Recovery: run the student's happy-path loop against a missing file, observe it stop, add exception-to-result conversion to that same dispatch, rerun identical recovery. Retain denial/nonzero exit examples and approval boundaries.
6. Verification: predict persistence, record the real unchanged checker/browser baseline, repair, rerun the same checker and browser interaction. Compare claims with observations.

## Work and checks

- [x] Add focused failing tests and implement real offline limitation experiments in root and student checkpoints. Root and Docker starters stay aligned.
- [x] Rewrite all six active lessons with prediction, before, explanation, change, same-task retry, reflection, and an executable next limitation. Maintain hints and clearly distinct live routes.
- [x] Adjust lesson-4 scaffold comments and stage-specific test commands so the unhandled-error behavior is intentional until lesson 5. Keep final solutions unchanged.
- [x] Align overview, workshop/facilitator guidance and timing caveats. Record paired before/after observations in existing lesson notes.
- [x] Validate a temporary starter through each stage, including expected failures and all completed-solution tests. Run frontend checks, independent review and inspect rendered guide.
- [x] Rebuild only the frontend for the current workbench; do not restart the runtime or replace learner files.

Validation details and remaining learning-outcome limitations are recorded in
[the causal-learning review](../../research/causal-learning-2026-09-25.md).

No Git metadata is present, so changes are made in this workspace without a commit.
