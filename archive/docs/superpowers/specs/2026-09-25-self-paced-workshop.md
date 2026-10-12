# Self-paced workshop

The user accepted the self-guided usability review and asked us to learn from Vercel's instructor-free course. Keep the standalone Python workshop and its six lessons. Make the existing journey usable without an instructor; do not expand into Vercel's advanced syllabus.

## Teaching design

Each lesson states the outcome, why the next capability is needed, exact file/command, expected evidence, explanation of the prediction, and recovery steps. Distinguish deterministic offline checks from calls to the configured model. Supply correctly indented solution snippets and a backup-first catch-up path. Setup help must be visible, including host versus workshop terminal, configuration versus verified credentials, and expected starter failures. Ninety minutes is a target, not a measured novice completion time.

Vercel sources: [course introduction](https://vercel.com/academy/build-ai-agent-harness), [first lesson](https://vercel.com/academy/build-ai-agent-harness/from-chat-to-agent), [first tools](https://vercel.com/academy/build-ai-agent-harness/your-first-tools), [verification](https://vercel.com/academy/build-ai-agent-harness/verification-gates). Borrow the runnable causal sequence, outcomes, fast route, exact try-it commands, done-when checks, solutions and scoped evidence reporting. Do not copy TypeScript implementations or claim Vercel provides automated grading.

## Product behavior

- Render welcome prerequisites and setup guidance; retain prominent start action.
- Fix selected-text Tab destruction; support block indent/outdent and jump to the next BLANK. Queue the latest requested editor file during loading without discarding unsaved content. Default to relevant workshop files, with all files still accessible.
- Every lesson navigation starts at its heading and focuses it. Add copy controls to lesson code blocks; handle clipboard failures visibly.
- Remember self-reported checks locally, distinctly from navigation. Navigation remains free. Finishing shows an honest summary with unconfirmed steps and the capstone evidence required, rather than silently returning home. These are student confirmations, not automatic grading.
- A dependency/configuration CLI check must not contact a model or print credentials. Show clear missing dependency/key instructions and explain that presence does not validate a key.
- The REPL must show failed shell exit status and output even outside verbose mode; denial and exceptions must not receive a success tick.

## Limits and verification

No paid model calls are authorized by this change. Preserve the four student blanks and seeded app bug. Use completed copies for verification. Test editing, asynchronous file selection, progress persistence and tool feedback. Build/typecheck frontend, run local Python checks, and walk through the deployed UI in a browser. The earlier live repair failure remains unverified until a separately authorized model rehearsal succeeds.
