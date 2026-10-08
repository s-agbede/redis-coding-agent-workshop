# Pedagogical Foundations Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development for the bounded implementation tasks and review. Independent file ownership permits the parallel content/interface work described below.

**Goal:** Address all ten findings in the accepted pedagogical gap review.

**Architecture:** Keep the existing workshop and add a coherent explanatory layer, two isolated offline demonstrations, and separate learner evidence records. No provider requests or new dependencies are needed.

**Tech Stack:** Python, existing SDK/test fakes, pytest, strict TypeScript, Vue, Markdown and SVG.

## Task 1 — Orientation and component map

**Own:** frontend/public/welcome.md, review.md, demo-steps/*, images/agent-map.svg.

- [x] Write a concrete finished-product overview, identify learner/model/target application, and distinguish supplied versus implemented pieces.
- [x] Add a readable SVG and ownership table tied to actual files; use the same asset in the lesson reference panel.
- [x] Start the demo with `uv run python -m checkpoints.outcome_demo`, explicitly scripted with real temporary file operations and checks.
- [x] Keep the broken capstone baseline and setup troubleshooting; move setup ahead of learning and explain the browser/API/in-memory store.
- [x] Check all example paths and names against source. Review rendered output after Task 3.

## Task 2 — Six teaching sequences

**Own:** frontend/public/build-steps/*.md and manifest.yaml.

- [x] Rewrite visible prerequisites and worked explanations before tasks, preserve correct commands and recovery.
- [x] Lesson 1 uses `uv run python -m checkpoints.history` for all learners before an optional live first call; give request assembly and restart exercises.
- [x] Lesson 2 annotates the complete tool exchange, message roles, JSON string decoding and `**args`; teach test output.
- [x] Lesson 3 requires writing a description plus changed-input paging practice; live proposals do not guarantee a particular choice.
- [x] Lesson 4 compares manual exchange with the repeated loop and outer conversation loop; implement/verify stopping then feedback.
- [x] Lesson 5 tours supplied tools and prompts, then classifies novel error/denial/failure evidence.
- [x] Lesson 6 adds a brief application-data primer, reuses baseline, retains independent checks and includes final reconstruct/diagnose/explain tasks with answer rubric.
- [x] Every lesson contains an independent practice prompt and a separate answer explanation; use BLANK 1 first call, BLANK 2 reader, BLANK 3 stop, BLANK 4 feedback.

## Task 3 — Render teaching aids and record evidence

**Own:** frontend/src UI and progress state, frontend/tests, vendored markdown renderer.

- [x] Add failing behavioral tests for safe table/image rendering, separate progress categories, persistence, legacy progress, and summaries.
- [x] Run `npm test` in frontend and confirm new tests fail for the absent behavior.
- [x] Implement only safe Markdown table/local-image support and responsive styles required by the materials.
- [x] Keep the component map accessible in a closed reference panel alongside lessons.
- [x] Record practical work, compared explanations, live attempt and notes independently. Navigation never grants credit; old records never infer new conceptual evidence.
- [x] Run frontend tests and strict typecheck. Verify notes/progress survive reload and categories remain distinct in the browser.

## Task 4 — Offline runnable examples and consistent starter

**Own:** checkpoints/history.py, checkpoints/outcome_demo.py, tests/test_learning_examples.py, source comments and numbering, synchronized student copies.

- [x] Write tests for first/second/restarted request contents and isolated read/edit/run/check behavior; inspect failure before implementation.
- [x] Implement typed offline scripts that clearly identify prepared model replies. Outcome demo uses a temporary greeting script, completed loop and real functions; its fixed command runs only that temporary file.
- [x] Run `UV_CACHE_DIR=/private/tmp/coding-agent-review-uv-cache uv run --no-sync pytest tests/test_learning_examples.py -q` and both new example commands.
- [x] Renumber only blank labels and docstrings; correct the claim that a no-tool answer proves task success.
- [x] Synchronize intended root/browser starter and document copies without touching learner implementations or seeded app behavior.

## Task 5 — Pilot, review and full verification

**Own:** docs/research pedagogical implementation coverage and learner-pilot worksheet, WORKSHOP.md, FACILITATOR.md, README.md, docker-workshop/VALIDATION.md.

- [x] Write a practical timed pilot protocol with tasks, misconception rubric, help/hint/time records and offline/live distinctions. Mark actual participant results pending.
- [x] Trace G1–G10 to implemented material and verification evidence; review for prerequisites, disconnected examples and misleading success claims.
- [x] Run Python tests in an isolated completed copy and inspect starter failures separately; run actual before/after capstone checks in temporary copies.
- [x] Run frontend tests, typecheck, production build and relevant backend regression tests.
- [x] Use the browser to read the actual updated first-time path, inspect map and tables, use answer disclosures, record/reload/revert temporary evidence and check finish summary.
- [x] Obtain independent spec and quality reviews, resolve findings, and report verified changes with remaining empirical learner-pilot limitations.

Verified implementation evidence is recorded in `docs/research/pedagogical-fixes-2026-09-25.md`. The participant pilot is a documented next validation step, not a claimed completed study.
