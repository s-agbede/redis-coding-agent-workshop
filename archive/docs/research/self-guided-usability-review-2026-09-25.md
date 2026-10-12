# Self-guided student usability review

Reviewed 2026-09-25 against the running workshop at http://localhost:8080.

## Assessment

The workshop has a coherent learning sequence, but is not yet ready to hand to
a student with basic Python knowledge and no instructor. An experienced Python
developer with the environment already configured has a workable route through
the lessons. Setup, interpreting failures, editing Python, and recovering from
an unsuccessful agent run still require knowledge the student path does not teach.

This is an expert walkthrough, not a measured learner study. I inspected the live
browser at 1366 × 768, followed all phases and six lessons, inspected the source,
and ran local reproductions of editing and feedback problems. No live model calls
were made during this review. A scratch editor buffer was restored without saving;
learner files remain unchanged. The 90-minute duration has not been validated with
an unassisted learner.

## What already supports independent learning

- Four focused blanks keep the implementation small.
- The sequence from a manual tool exchange to the general loop is understandable.
- Predict/observe prompts, closed hints and separate solutions encourage attempts.
- Each lesson has observable “Done when” criteria.
- Offline tool and recovery checkpoints let students inspect concrete feedback.
- The supplied task board gives the learner a visible problem and independent checks.
- The integrated editor/terminal/preview reduces application switching; save state
  and failed-save protection are present.

## Essential changes before self-study

### 1. Make Python editing safe and the supplied answers directly usable

**Observed:** selecting two lines in the browser editor and pressing Tab replaced
the entire selection with four spaces. It did not indent the selected lines.
The buffer was restored and no save occurred. Separately, inserting the exact
two-line read_file solution at the existing blank without reindenting its second
line produced `SyntaxError: 'return' outside function` in an in-memory compile.

**Student impact:** a learner who opens a solution to get unstuck can introduce
another error, then delete their selection while trying to correct indentation.

**Change:** implement block indent/outdent and normal undo behavior; provide
copyable full function examples or explicit insertion/indentation guidance. Add
line numbers and a jump to the exercise blank. Do not rely on a learner knowing
how a plain textarea differs from a code editor.

Evidence: [Tab handler](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/src/components/CodeEditor.vue:89),
[read_file solution](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/public/build-steps/02-one-tool.md:35).

### 2. Reset the reading position when a lesson changes

**Observed:** clicking Next Step carried the instruction panel's scroll position
into the next lesson. Recorded positions ranged from 706 to 834 pixels. On entry
to the capstone, its title was 534 pixels above the viewport.

**Student impact:** the next lesson appears to begin in the middle. Its goal,
prerequisites or first command can be missed without any obvious indication.

**Change:** scroll the instruction panel to the top and focus the new lesson
heading on navigation. Preserve a saved reading position only for an explicit
resume action.

Evidence: [goToStep](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/src/views/Build.vue:164),
[screenshot](/Users/samuelagbede/Documents/Projects/redis-coding-agent/output/playwright/solo-review-step-scroll.png).

### 3. Add visible onboarding and an environment check

**Observed:** welcome.md says to bring basic Python knowledge and a model API key,
but the Welcome component only renders its metadata. That body text is absent
from the actual page. There is no student-facing readiness check for the runtime,
Python dependencies or model configuration. The repository README contains setup
commands, but the visible workshop does not link a newcomer through that process.

**Student impact:** “Start Workshop” is available before a student knows whether
they can complete the first model call. Authentication/provider failures are
called setup issues without a concrete route to repair them.

**Change:** show prerequisites and a clear start path: install/start the environment,
configure a compatible model, check readiness, then edit code. Identify which
commands belong in the host terminal and which belong in the workshop terminal.
Separate free local checks from a labeled live connectivity check. Explain which
lessons need a model and where a supplied offline trace can substitute for observation.

Evidence: [Welcome rendering](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/src/views/Welcome.vue:10),
[hidden welcome body](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/public/welcome.md:14),
[provider-error guidance](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/public/build-steps/01-first-call.md:55).

### 4. Display actual command outcomes

**Reproduced locally:** a wrapped run_bash tool returning `exit 3\nCheck failed`
displayed only `✓ Running: python example_check.py` with default verbosity. The
nonzero result is available to the model, but the learner sees a green check.

**Student impact:** a failed check looks successful, undermining the workshop's
central lesson about evidence. A learner cannot confidently distinguish an
executed command from a passing command.

**Change:** always display the exit status and distinguish success, nonzero exit,
denial and tool exceptions. Include a short relevant output excerpt and a way to
view the full result. Keep model claims separate from actual check results.

Evidence: [unconditional success marker](/Users/samuelagbede/Documents/Projects/redis-coding-agent/ui.py:131).

### 5. Bring recovery instructions into the student path

**Observed:** the Demo asks students to start the preview and keep it running.
The capstone later repeats the start command without checking for the existing
process. Startup output is redirected to a log, but neither page supplies a
status/log/stop command. Authentication, occupied-port and reload troubleshooting
mostly lives in FACILITATOR.md. The capstone's fallback is labeled for a facilitator.

**Student impact:** when a command fails, the learner has to diagnose environment,
exercise code and model behavior together. They can also start a second preview
process unnecessarily. There is no obvious way to restore one exercise while
preserving the rest of their work.

**Change:** add a short “If this didn't work” path to each lesson, including the
expected failure, a contrasting unexpected failure, and the next concrete step.
Provide preview start/status/restart controls or documented commands; a safe
per-exercise reset with a backup; and a student-facing capstone fallback clearly
identified as a supplied solution.

Evidence: [Demo server instructions](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/public/demo-steps/loop.md:10),
[repeated capstone start](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/public/build-steps/06-capstone.md:27),
[facilitator-only recovery guidance](/Users/samuelagbede/Documents/Projects/redis-coding-agent/FACILITATOR.md:85).

The only measured live rehearsal failed 8/9 checks before trace retention was
added. This does not prove every learner will fail, but live repair reliability
has not been established. A solo student needs a clear next step for that outcome.

## Further improvements

1. **Track evidence and provide a real finish screen.** I navigated to Finish with
   every blank untouched; the button returned to Welcome without a summary.
   Keep free navigation, but distinguish visited, attempted and verified steps.
   Add concept answer explanations and a final checklist/export of evidence.
   Current resume state is only the current index in sessionStorage, not durable
   completion tracking. [Navigation code](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/src/views/Build.vue:161).
2. **Reduce manual copying and file hunting.** The selector exposed 58 files,
   including old task pages, PRD, issue documents and unrelated example files.
   The capstone prompt occupied 2685 pixels of scrollable content in a 696-pixel
   code block. Add Copy command/Copy prompt controls and a “Lesson files” default
   view with an “All files” option. Keep the full workspace available.
3. **Synchronize lesson and editor on first load.** On first entry to Demo, the
   lesson showed “Open capstone/index.html” while the editor stayed on first_call.py.
   This persisted until another action. The selected-file watcher ignores updates
   while loading, consistent with a race. The Open button provides a workaround.
   [Watcher](/Users/samuelagbede/Documents/Projects/redis-coding-agent/docker-workshop/frontend/src/components/CodeEditor.vue:104).
4. **Explain the expected results.** Show a short representative test summary,
   annotate a tool request/result pair, and explain the terms schema, registry,
   dispatch and call ID where they first matter. Questions currently test recall
   without a separate explanation students can use to check their understanding.
5. **Validate pacing with real students.** Present 90 minutes as a target. Run an
   unassisted pilot with a Python-capable learner new to LLM tooling, record setup
   time, stuck points, hint use and completion evidence, and revise the estimate.

## Recommended next pass

First fix the editor, lesson navigation and misleading command status. Then add
onboarding, expected-output examples and recovery instructions. Finally add
verified progress and a finish summary, and pilot the complete experience with
someone who has not seen this project. Preserve the existing curriculum and
progressive hints; the largest gaps are guidance and recovery around it.
# Implementation follow-up

The accepted review led to the [self-paced workshop changes](../superpowers/specs/2026-09-25-self-paced-workshop.md). The original findings below record the pre-change experience. Current test and browser evidence is in [validation](../../docker-workshop/VALIDATION.md).

Vercel's [course introduction](https://vercel.com/academy/build-ai-agent-harness) explains a causal sequence: a limitation motivates each next runnable capability. Its [first lesson](https://vercel.com/academy/build-ai-agent-harness/from-chat-to-agent) makes outcomes, commands, completion criteria and a complete solution easy to find. We adopted those teaching patterns within the existing six Python lessons, adding our own setup and recovery guidance. Its [verification lesson](https://vercel.com/academy/build-ai-agent-harness/verification-gates) reinforces reporting exactly what was checked; our progress controls therefore explicitly record student confirmations rather than claiming to grade code.
