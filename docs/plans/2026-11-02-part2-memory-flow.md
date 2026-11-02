# Part 2 memory and shared knowledge implementation plan

**Goal:** Apply the approved 90-minute sequence while preserving the working learner runtime and Part 1.

**Architecture:** Keep the completed Part 1 loop and supplied Part 2 runtime. Change the lesson order and evidence-driven exercises; reuse the user's established embedded-slide pattern once its source is identified.

**Stack:** Python, Redis SDKs, Vue, Markdown publisher.

- [x] Reorder Part 2 to recap, forgetting, explicit agent file edit, session capture, preference recall, published procedure, independent verification. Keep existing lesson URLs stable; the manifest defines their display order.
- [x] Update the publisher order test first, run it to observe failure, then change PART2_LESSONS. Preserve Part 1 order and editor links.
- [x] Revise learner lessons, 90-minute schedule and facilitator cues. Use uv as the project rule and explanatory comments as the separately recalled preference. State that session capture stores user/final-answer events, not a resumable tool transcript.
- [x] Add a deterministic runtime flow test proving the actual agent file tool can edit AGENTS.md, reset reloads it, history disappears, and unrelated preferences do not appear in project instructions.
- [x] Reviewed the supplied raphael-workshops reference. Implemented original Markdown decks and a Vue viewer with guided/text/focus modes, preserving exercises and source paths. No copied platform or PDF machinery.
- [x] Republish docs; run focused Python tests, frontend tests and build, and publication drift validation. Report live-service limitations separately from local checks.

Do not merge origin/main or commit unrelated existing changes. No automatic Markdown extraction machinery, session restoration, semantic cache or direct vector-index lab.
