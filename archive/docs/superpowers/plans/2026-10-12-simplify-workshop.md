# Simplify the workshop implementation

Approved scope: direct main.py imports, ordinary display/approval functions,
explicit tool schemas, removal of obsolete exercises, canonical publishing,
and removal of web fetching from the core repair task.

- [x] Add regression tests for the main.py entry point, literal SDK requests,
  explicit five-tool registration and approved/declined command execution.
- [x] Replace module injection and SDK proxies with direct calls; preserve the
  browser learner's completed ask function and all unrelated edits.
- [x] Define schemas by name, keep one shared implementation of supplied tools,
  and use explicit final registration in cumulative solutions.
- [x] Remove superseded runners and their exclusive tests; retain meaningful
  request/history/tool/evaluation tests and the release evidence fixtures.
- [x] Update active lessons, add an explicit documentation publishing command,
  and verify publication does not alter learner Python or app files.
- [x] Replay published snippets and catch-ups in temporary workspaces, run
  completed harness/tool/app tests, and validate/build the frontend.
- [x] Rebuild the local workshop for review without committing or pushing.

Validation runs must never copy a completed solution over a live learner file.
Provider transport is replaced only in tests; no live API rehearsal is required.
