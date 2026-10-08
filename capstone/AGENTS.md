# Repair the task board

This small FastAPI app is the workshop's repair exercise. A task appears complete
when you click its checkbox, but it becomes incomplete again after a refresh.
Reproduce the behaviour, repair the code, and verify the result.

- Work in this directory. Keep the application small, typed, and readable.
- Preserve the existing API and page. Tasks may remain in memory and reset when
  the server restarts; completion must survive subsequent GET requests while the
  same server is running.
- Do not modify the acceptance verifier, its checks, or any workshop tests.
- From this directory, run `python ../verify_capstone.py --project .` before and
  after the repair. It starts and stops an isolated test server for you.
- For the browser preview, run
  `uvicorn app:app --host 0.0.0.0 --port 8000` from this directory. Use a separate
  terminal for this foreground server. The page is served at `/`.
- Finish with the files changed, commands run, observed results, and anything
  you have not verified. Do not claim success from an HTTP status alone.

No model, network service, database, or new dependency is needed by this app.
