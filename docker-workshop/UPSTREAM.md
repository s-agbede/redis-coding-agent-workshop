# Workbench source

The default shell is adapted from:

- Repository: https://github.com/redis-developer/semantic-cache-routing-workshop
- Commit: `276e491d2b4dcc4b4c5a24acca85d368502cbb91`
- Retrieved: 2026-09-25
- Source files: `workbench/index.html`, `workbench/config.js`,
  `workbench/assets/script.js`, `workbench/assets/style.css`.

Redis logos and existing source attribution remain. Local adaptations configure
Instructions, Code, Terminal and App Preview for coding-agent lessons, preserve
iframe state through layout changes, expand Instructions as well as other panels,
and validate source/origin/path before opening lesson files in Code.

Instructions embed the existing guided Vue application at `/guide/`; we retain
its learning sequence, diagrams, answer disclosures and separate evidence records.
The active workbench uses code-server instead of the custom text editor. The
runtime combines official code-server 4.127.0 (image digest pinned in its Dockerfile),
managed Python 3.12, the existing FastAPI file API and ttyd 1.7.7 (official release,
checksum-verified). No semantic-cache/router application services are copied.

The code-server runtime uses a new Debian virtualenv volume; the old Alpine
volume is retained during upgrades. The student bind mount is unchanged.

# Guided lesson source

This standalone workshop is adapted from:

- Repository: https://github.com/redislabs-training/redis-beyond-the-cache-workshop
- Branch: `guided`
- Commit: `c2aaf0edf7ae914e592ba60282f057e90670172e`
- Retrieved: 2026-09-25

`frontend/` started as `workshops/template/frontend/` at that revision.
`vendor/workshop-front-end-components/` contains its shared component package.
The upstream README and package metadata identify the project as MIT licensed;
the source snapshot did not include a separate LICENSE file. Redis attribution
and package metadata are retained here.

Local adaptations:

- Standalone Welcome, Review, Demo and Build content for the six coding-agent exercises.
- Python-only runtime, replacing the template's Java/Python demo API setup.
- A typed FastAPI editor API over the existing student directory.
- Explicit file saves and visible errors; save before switching files or routes.
- A real ttyd/tmux shell instead of the Redis-command terminal.
- Terminal and FastAPI preview tabs under the editor.
- Production Docker images and same-origin proxy routes for the standalone stack.
- TypeScript in the new editor and workspace components; upstream JavaScript retained.
- The shared header says Workshop Home because this deployment has no hub.
- Markdown rendering preserves fenced Python code and indentation; safe native
  details/summary disclosures keep hints and solutions closed initially.
- Research-informed lessons trace one tool call, explore output limits and recovery,
  and end with repair of a supplied task board. See VALIDATION.md for checks.

The separate root-level coding-agent exercises and optional Docsify workbench remain
available. The guided app is now the Instructions panel in the default workbench.
