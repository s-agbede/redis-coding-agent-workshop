# Workshop causal redesign implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development with isolated
> file ownership and superpowers:dispatching-parallel-agents for independent work.

**Goal:** Deliver the approved 90-minute instructor-led coding-agent workshop.

**Architecture:** Keep existing Vue lessons embedded beside code-server and the
Terminal. Python learner functions and supplied checks run in the same student
workspace; root CLI sources remain consistent. Existing capstone stays seeded.

**Tech Stack:** Vue, strict TypeScript for new frontend logic, Python/uv/pytest,
Docker, existing OpenAI SDK. No new dependencies.

## 1. Python exercises and checks (Python agent)

- [x] Inspect existing checkpoints, tests and solutions without printing secrets.
- [x] Add failing behavior tests for a scaffold model-call function, retained
  conversation requests, plain-to-bounded reader progression, and matching tool
  feedback. Test with prepared SDK responses and real temporary files.
- [x] Implement small typed learner functions and separate complete solutions.
  Keep the reader starter unbounded in the first exercise and reveal the supplied
  excerpt helper only when excessive output has been observed. Publish exact
  callable names and commands to the lesson author before integration.
- [x] Remove the hard-coded credential in student first_call.py and use
  os.environ.get("AGENT_API_KEY"). Do not use or print the credential.
- [x] Keep existing tool/harness/application evaluators and explain their boundary.
  Mirror relevant .py changes in root and docker-workshop/student.
- [x] Run focused tests with `uv run pytest` and the complete solution suite in
  a disposable workspace. Keep intentional learner exercise failures distinguishable.

## 2. Lesson content (lesson agent)

- [x] Replace active manifest with seven steps: 01-first-call.md, 02-peas.md,
  03-conversation.md, 04-one-tool.md, 05-better-tools.md, 06-agent-loop.md,
  07-capstone.md. Write concise friendly pages with exact exercise commands,
  hints and copyable functions matching the Python agent's published contract.
- [x] Simplify welcome.md; update architecture SVGs, WORKSHOP.md, FACILITATOR.md,
  README guidance and docs mirrors. PEAS uses try-then-reveal; capstone uses the
  visible completion bug and provided independent checks.
- [x] Replace obsolete documentation-contract assertions in test_workshop_docs.py
  with link/command/file-integrity checks for the new active path; avoid brittle
  assertions about ordinary prose. Validate referenced source paths and commands.

## 3. Navigation and app integration (primary agent)

- [x] Write failing navigation/UI tests: Start Workshop leads directly to the
  model lesson; legacy review/demo URLs redirect; seven lessons are available;
  evidence forms/notes/progress summary and repeated file map are absent.
- [x] Change workshop.config.yaml and fallback phases to Welcome + Workshop;
  simplify Build.vue by removing evidence collection, progress summary and component
  map. Preserve code links, hints, keyboard focus, terminal/editor sessions and
  previous/next navigation. Keep old localStorage records untouched.
- [x] Run `npm test`, `npm run typecheck`, and
  `VUE_APP_BASE_PATH=/guide/ npm run build` in docker-workshop/frontend.
- [x] Run workbench tests and backend tests; rebuild the local frontend service
  without replacing student data or runtime configuration. Inspect every active
  lesson in a browser and exercise hints, links and the final navigation state.

## 4. Review and delivery

- [x] Independently review spec coverage, then code quality and exercise wiring.
- [x] Exercise the solved learner path and independent capstone checker on temporary
  copies; confirm starter remains unfinished and capstone remains seeded.
- [x] Record verification in docker-workshop/VALIDATION.md. Report live-model and
  human timing limitations accurately, without presenting scripted tests as trials.

No Git metadata is present. A local source snapshot is saved under /private/tmp
for review; do not invent commits or create a repository to satisfy workflow steps.
