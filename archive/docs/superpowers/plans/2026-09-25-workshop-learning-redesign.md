# Workshop Learning Redesign Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development for the independent capstone implementation and review. Implement other coupled lesson/runtime changes inline with test-first verification.

**Goal:** Deliver the approved before/after workshop as a runnable guided lab with a repair capstone.

**Architecture:** Keep the flat Python application and Vue template. Root files are maintained sources, mirrored explicitly into the browser student workspace. New checkpoints and capstone verification are small standalone Python modules. No Git metadata exists; a pre-edit archive is saved at `/private/tmp/coding-agent-before-redesign/workshop.tgz`.

**Tech Stack:** Python/uv/pytest/FastAPI, existing OpenAI SDK and Rich, Vue/TypeScript, Docker, browser verification.

- [x] Capstone: add `capstone/app.py`, `capstone/index.html`, `capstone/AGENTS.md`, `solutions/capstone_app.py`, `verify_capstone.py`, `tests/test_capstone.py`; replace `rehearse.py` and its tests. First demonstrate the missing behavior with failing tests. Verify broken starter fails acceptance, repaired fixture passes, and rehearsal uses the same checks.
- [x] Tools: test numbered `read_file(path, offset=1, limit=80)`, validation, character/line caps, explicit continuation; cap directory/shell results while retaining exit status. Add implementation to solutions and leave a focused read_file blank in starter. Make web_fetch prebuilt.
- [x] Checkpoints: test one manual tool round trip with matching call ID, a no-execution description comparison, and scripted missing-file recovery; implement `checkpoints/stage2_one_tool.py`, `checkpoints/description_lab.py`, `checkpoints/recovery.py`. Run with `uv run python -m checkpoints.<name>` to preserve project imports.
- [x] Project runner: test and add `main.py --project capstone`, trusted AGENTS.md loading, request timeout and an explicit verification-report instruction. Preserve main() default behavior and student blanks.
- [x] Guided lessons: update all six lesson contents, manifest, welcome/review/demo, docs/sidebar, README, WORKSHOP, FACILITATOR, browser setup. Add safe `<details><summary>` rendering after a failing renderer test; no arbitrary HTML execution. First-call and loop answers move behind hints. Existing routes remain valid where practical.
- [x] Integration: mirror managed root sources into student workspace without secrets or virtualenvs; update course-file tests; run completed-solution tests from isolated copies. Run starter suite and verify every failure maps to an intentional blank.
- [x] Review and delivery: independent spec and quality review; fix findings; rebuild Docker; verify browser steps/disclosures/editor/terminal and broken/fixed capstone HTTP+preview. Record results in docker-workshop/VALIDATION.md. Leave the actual learner workspace in starter state.

Proposed timing: orientation 10m; call/history 15m; one tool including descriptions/output 15m; loop 20m; recovery 10m; capstone 15m; reflection/extensions 5m. Pilot timing is not yet measured.

Validation is recorded in docker-workshop/VALIDATION.md. After explicit user approval, one live gpt-5 rehearsal ran and failed: 8/9 independent acceptance checks passed, with completion persistence still failing. Local implementation and deterministic verification are complete; live repair success has not been established. See output/rehearsal/live-2026-09-25.log for the measured result.
