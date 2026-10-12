# Self-paced workshop implementation plan

Spec: [self-paced workshop](../specs/2026-09-25-self-paced-workshop.md).

- [x] Add regression coverage for editor indentation/selection queue; implement safe edits, BLANK navigation and focused file list.
- [x] Render onboarding, copy controls, heading focus and honest persistent self-check/finish summary. Verify frontend tests, types and build.
- [x] Add offline dependency/configuration check and truthful tool error display with tests before behavior changes.
- [x] Rewrite the active six lessons and demo with outcomes, exact expected output, explanations, setup/recovery paths, indented solutions and backup-first catch-up instructions.
- [x] Review implementation against spec, then for code quality. Resolve issues.
- [x] Mirror student files, run completed-solution tests, deploy frontend and browser-check the self-paced journey. Record evidence and limitations.

No repository metadata is present, so no commits or worktrees are needed. Only existing guided workshop services may be rebuilt; do not disturb unrelated containers. Do not invoke the model during verification.

Validation: 68 Python tests in Linux, 37 frontend tests, strict TypeScript and Docker build passed; deployed desktop/narrow browser walkthrough passed. No model calls were made. See docker-workshop/VALIDATION.md for evidence and limits.
